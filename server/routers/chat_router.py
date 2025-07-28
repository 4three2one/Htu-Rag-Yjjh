import os
import json
import asyncio
import traceback
import uuid
import time
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from langchain_core.messages import AIMessageChunk, HumanMessage
from sqlalchemy.orm import Session
from pydantic import BaseModel
import aiosqlite

from src import executor, config
from src.core import HistoryManager
from src.agents import agent_manager
from src.models import select_model
from src.utils.logging_config import logger
from src.agents.tools_factory import get_all_tools
from server.routers.auth_router import get_admin_user
from server.utils.auth_middleware import get_required_user, get_db
from server.models.user_model import User
from server.models.thread_model import Thread
from server.db_manager import db_manager

from server.third.ragflow_http_api import ragflow_chat_completion_origin,\
    ragflow_create_session_with_chat_assistant
from server.third.utils import make_chunk, RAGFLOW_HISTORY_DB,save_ragflow_history

chat = APIRouter(prefix="/chat")


@chat.get("/default_agent")
async def get_default_agent(current_user: User = Depends(get_required_user)):
    """获取默认智能体ID（需要登录）"""
    try:
        default_agent_id = config.default_agent_id
        # 如果没有设置默认智能体，尝试获取第一个可用的智能体
        if not default_agent_id:
            agents = await agent_manager.get_agents_info()
            if agents:
                default_agent_id = agents[0].get("name", "")

        return {"default_agent_id": default_agent_id}
    except Exception as e:
        logger.error(f"获取默认智能体出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取默认智能体出错: {str(e)}")


@chat.post("/set_default_agent")
async def set_default_agent(agent_id: str = Body(..., embed=True), current_user=Depends(get_admin_user)):
    """设置默认智能体ID (仅管理员)"""
    try:
        # 验证智能体是否存在
        agents = await agent_manager.get_agents_info()
        agent_ids = [agent.get("name", "") for agent in agents]

        if agent_id not in agent_ids:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 不存在")

        # 设置默认智能体ID
        config.default_agent_id = agent_id
        # 保存配置
        config.save()

        return {"success": True, "default_agent_id": agent_id}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"设置默认智能体出错: {e}")
        raise HTTPException(status_code=500, detail=f"设置默认智能体出错: {str(e)}")


@chat.get("/")
async def chat_get(current_user: User = Depends(get_required_user)):
    """聊天服务健康检查（需要登录）"""
    return "Chat Get!"


@chat.post("/call")
async def call(query: str = Body(...), meta: dict = Body(None), current_user: User = Depends(get_required_user)):
    """调用模型进行简单问答（需要登录）"""
    meta = meta or {}
    model = select_model(model_provider=meta.get("model_provider"), model_name=meta.get("model_name"))

    async def predict_async(query):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, model.predict, query)

    response = await predict_async(query)
    logger.debug({"query": query, "response": response.content})

    return {"response": response.content}


@chat.get("/agent")
async def get_agent(current_user: User = Depends(get_required_user)):
    """获取所有可用智能体（需要登录）"""
    agents = await agent_manager.get_agents_info()
    # logger.debug(f"agents: {agents}")
    return {"agents": agents}


@chat.post("/agent/{agent_name}")
async def chat_agent(agent_name: str,
                     query: str = Body(...),
                     config: dict = Body({}),
                     meta: dict = Body({}),
                     current_user: User = Depends(get_required_user)):
    logger.info(f"starting chat with: {agent_name}")

    meta.update({
        "query": query,
        "agent_name": agent_name,
        "server_model_name": config.get("model", agent_name),
        "thread_id": config.get("thread_id"),
        "user_id": current_user.id
    })
    request_id = meta.get("request_id")
    thread_id = config.get("thread_id")
    delay = 0.01

    # 根据 thread_id 获取session_id，没有创建新的 session_id
    session_id = None
    # chat_id = None
    current_answer_id = str(uuid.uuid4())
    ragflow_obj = db_manager.get_ragflow_by_thread_id(thread_id) if thread_id else None
    if ragflow_obj:
        session_id = ragflow_obj["session_id"]
    elif thread_id:
        # 没有找到，自动创建
        ragflow_resp = await ragflow_create_session_with_chat_assistant("新对话")
        chat_id = ragflow_resp['data']['chat_id']
        session_id = ragflow_resp['data']['id']
        db_manager.add_ragflow(thread_id=thread_id, chat_id=chat_id, session_id=session_id)

    async def stream_messages():
        yield make_chunk(status="init",request_id=request_id, meta=meta, msg=HumanMessage(content=query).model_dump())
        # 正确处理流式数据
        last_content = ""
        ai_content = ""
        ragflow_data = None

        async for message in ragflow_chat_completion_origin(query,session_id=session_id):
            logger.debug(f"收到RAGFlow消息: {message}")

            # 检查是否有错误
            if "error" in message:
                yield make_chunk(status="error",request_id=request_id, message=message["error"], meta=meta)
                return

            # 解析RAGFlow返回的数据 - 支持多种格式
            content = None
            msg_data = None

            message = message["data"]

            if type(message) is bool:
                await save_ragflow_history(
                    thread_id=config["thread_id"],
                    user_id=current_user.id,
                    agent_id=agent_name,
                    user_msg=query,
                    ai_msg=ai_content,
                    reference=ragflow_data['reference'],
                )
                yield make_chunk(status="finished",request_id=request_id, meta=meta)
                continue

            # 格式1: OpenAI兼容格式
            if "choices" in message and len(message["choices"]) > 0:
                choice = message["choices"][0]
                if "delta" in choice and "content" in choice["delta"]:
                    content = choice["delta"]["content"]
                    msg_data = {
                        "content": content,
                        "id":current_answer_id,
                        "role": "assistant",
                        "type": "ai"
                    }

            # ragflow格式
            elif "answer" in message:
                content = message["answer"]
                delta = content[len(last_content):]
                ai_content += delta
                last_content = content
                ragflow_data=message
                msg_data = {
                    "content": delta,
                    "id": current_answer_id,
                    "role": "assistant",
                    "reference": ragflow_data['reference'],
                    "type": "ai",
                }

                # 增加延迟
                length = len(delta)
                if length > 100:
                    delay = 0.1
                elif length > 50:
                    delay = 0.2
                elif length > 20:
                    delay = 0.5
                else:
                    delay = 0.7

            print(f"{content=}, {msg_data=}")
            # 添加调试日志
            if ragflow_data and 'reference' in ragflow_data:
                print(f"RAGFlow reference数据: {ragflow_data['reference']}")
            
            time.sleep(delay)
            yield make_chunk(
                content=content,
                request_id=request_id,
                msg=msg_data,
                metadata=meta,
                status="loading"
            )

    # return EventSourceResponse(stream_messages())
    return StreamingResponse(stream_messages(), media_type='application/json')

    # 新增分支：ragflow 直接用ChatOpenAI
    # if agent_name == "ragflow":
    #     async def stream_ragflow():
    #         try:
    #             thread_id = config.get("thread_id")
    #             if not thread_id:
    #                 thread_id = str(uuid.uuid4())
    #                 config["thread_id"] = thread_id
    #
    #             # 默认模型可根据需要调整
    #             # model_name = config.get("model", "openai/gpt-3.5-turbo")
    #             model_name = "deepseek/deepseek-chat"
    #             chat_model = load_chat_model(model_name)
    #             messages = [HumanMessage(content=query)]
    #             yield make_chunk(status="init", meta=meta, msg=messages[0].model_dump())
    #
    #             ai_content = ""
    #             async for chunk in chat_model.astream(messages):
    #                 if hasattr(chunk, "content"):
    #                     ai_content += chunk.content
    #                     yield make_chunk(content=chunk.content, msg=chunk.model_dump(), status="loading")
    #
    #             await save_ragflow_history(
    #                 thread_id=thread_id,
    #                 user_id=current_user.id,
    #                 agent_id=agent_name,
    #                 user_msg=query,
    #                 ai_msg=ai_content
    #             )
    #
    #             yield make_chunk(status="finished", meta=meta)
    #         except Exception as e:
    #             import traceback
    #             yield make_chunk(message=f"Error in ragflow: {e}", status="error")
    #     return StreamingResponse(stream_ragflow(), media_type='application/json')
    # async def stream_ragflow():
    #     try:
    #         thread_id = config.get("thread_id")
    #         if not thread_id:
    #             thread_id = str(uuid.uuid4())
    #             config["thread_id"] = thread_id
    #
    #         yield make_chunk(status="init", meta=meta, msg=HumanMessage(content=query).model_dump())
    #
    #         ai_content = ""
    #         async for chunk in ragflow_chat_completion_openai(query):
    #             # 提取内容
    #             content = None
    #             if hasattr(chunk, "choices") and chunk.choices:
    #                 delta = getattr(chunk.choices[0], "delta", None)
    #                 if delta and hasattr(delta, "content"):
    #                     content = delta.content
    #             if content:
    #                 ai_content += content
    #                 msg = {
    #                     "content": content,
    #                     "role": "assistant",
    #                     "type": "ai"
    #                 }
    #                 yield make_chunk(content=content, msg=msg, status="loading")
    #
    #         await save_ragflow_history(
    #             thread_id=thread_id,
    #             user_id=current_user.id,
    #             agent_id=agent_name,
    #             user_msg=query,
    #             ai_msg=ai_content
    #         )
    #
    #         yield make_chunk(status="finished", meta=meta)
    #     except Exception as e:
    #         import traceback
    #         yield make_chunk(message=f"Error in ragflow: {e}", status="error")
    # return StreamingResponse(stream_ragflow(), media_type='application/json')

    # 将meta和thread_id整合到config中
    # def make_chunk(content=None, **kwargs):
    #
    #     return json.dumps({
    #         "request_id": meta.get("request_id"),
    #         "response": content,
    #         **kwargs
    #     }, ensure_ascii=False).encode('utf-8') + b"\n"
    #
    # async def stream_messages():
    #
    #     # 代表服务端已经收到了请求
    #     yield make_chunk(status="init", meta=meta, msg=HumanMessage(content=query).model_dump())
    #
    #     try:
    #         agent = agent_manager.get_agent(agent_name)
    #     except Exception as e:
    #         logger.error(f"Error getting agent {agent_name}: {e}, {traceback.format_exc()}")
    #         yield make_chunk(message=f"Error getting agent {agent_name}: {e}", status="error")
    #         return
    #
    #     messages = [{"role": "user", "content": query}]
    #
    #     # 构造运行时配置，如果没有thread_id则生成一个
    #     config["user_id"] = current_user.id
    #     if "thread_id" not in config or not config["thread_id"]:
    #         config["thread_id"] = str(uuid.uuid4())
    #         logger.debug(f"没有thread_id，生成一个: {config['thread_id']=}")
    #
    #     runnable_config = {"configurable": {**config}}
    #
    #     try:
    #         async for msg, metadata in agent.stream_messages(messages, config_schema=runnable_config):
    #             # logger.debug(f"msg: {msg.model_dump()}, metadata: {metadata}")
    #             if isinstance(msg, AIMessageChunk):
    #                 yield make_chunk(content=msg.content,
    #                                 msg=msg.model_dump(),
    #                                 metadata=metadata,
    #                                 status="loading")
    #             else:
    #                 yield make_chunk(msg=msg.model_dump(),
    #                                 metadata=metadata,
    #                                 status="loading")
    #
    #         yield make_chunk(status="finished", meta=meta)
    #     except Exception as e:
    #         logger.error(f"Error streaming messages: {e}, {traceback.format_exc()}")
    #         yield make_chunk(message=f"Error streaming messages: {e}", status="error")
    #
    # return StreamingResponse(stream_messages(), media_type='application/json')


@chat.post("/agent_origin/{agent_name}")
async def chat_agent_origin(agent_name: str,
                            query: str = Body(...),
                            config: dict = Body({}),
                            meta: dict = Body({}),
                            current_user: User = Depends(get_required_user)):
    """使用特定智能体进行对话（需要登录）"""

    meta.update({
        "query": query,
        "agent_name": agent_name,
        "server_model_name": config.get("model", agent_name),
        "thread_id": config.get("thread_id"),
        "user_id": current_user.id
    })

    # 将meta和thread_id整合到config中
    def make_chunk(content=None, **kwargs):

        return json.dumps({
            "request_id": meta.get("request_id"),
            "response": content,
            **kwargs
        }, ensure_ascii=False).encode('utf-8') + b"\n"

    async def stream_messages():

        # 代表服务端已经收到了请求
        yield make_chunk(status="init", meta=meta, msg=HumanMessage(content=query).model_dump())

        try:
            agent = agent_manager.get_agent(agent_name)
        except Exception as e:
            logger.error(f"Error getting agent {agent_name}: {e}, {traceback.format_exc()}")
            yield make_chunk(message=f"Error getting agent {agent_name}: {e}", status="error")
            return

        messages = [{"role": "user", "content": query}]

        # 构造运行时配置，如果没有thread_id则生成一个
        config["user_id"] = current_user.id
        if "thread_id" not in config or not config["thread_id"]:
            config["thread_id"] = str(uuid.uuid4())
            logger.debug(f"没有thread_id，生成一个: {config['thread_id']=}")

        runnable_config = {"configurable": {**config}}

        try:
            async for msg, metadata in agent.stream_messages(messages, config_schema=runnable_config):
                # logger.debug(f"msg: {msg.model_dump()}, metadata: {metadata}")
                if isinstance(msg, AIMessageChunk):
                    yield make_chunk(content=msg.content,
                                     msg=msg.model_dump(),
                                     metadata=metadata,
                                     status="loading")
                else:
                    yield make_chunk(msg=msg.model_dump(),
                                     metadata=metadata,
                                     status="loading")

            yield make_chunk(status="finished", meta=meta)
        except Exception as e:
            logger.error(f"Error streaming messages: {e}, {traceback.format_exc()}")
            yield make_chunk(message=f"Error streaming messages: {e}", status="error")

    return StreamingResponse(stream_messages(), media_type='application/json')


@chat.get("/models")
async def get_chat_models(model_provider: str, current_user: User = Depends(get_admin_user)):
    """获取指定模型提供商的模型列表（需要登录）"""
    model = select_model(model_provider=model_provider)
    return {"models": model.get_models()}


@chat.post("/models/update")
async def update_chat_models(model_provider: str, model_names: list[str], current_user=Depends(get_admin_user)):
    """更新指定模型提供商的模型列表 (仅管理员)"""
    config.model_names[model_provider]["models"] = model_names
    config._save_models_to_file()
    return {"models": config.model_names[model_provider]["models"]}


@chat.get("/tools")
async def get_tools(current_user: User = Depends(get_admin_user)):
    """获取所有可用工具（需要登录）"""
    return {"tools": list(get_all_tools().keys())}


@chat.post("/agent/{agent_name}/config")
async def save_agent_config(
        agent_name: str,
        config: dict = Body(...),
        current_user: User = Depends(get_admin_user)
):
    """保存智能体配置到YAML文件（需要管理员权限）"""
    try:
        # 获取Agent实例和配置类
        agent = agent_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_name} 不存在")

        # 使用配置类的save_to_file方法保存配置
        config_cls = agent.config_schema
        result = config_cls.save_to_file(config, agent_name)

        if result:
            return {"success": True, "message": f"智能体 {agent_name} 配置已保存"}
        else:
            raise HTTPException(status_code=500, detail="保存智能体配置失败")

    except Exception as e:
        logger.error(f"保存智能体配置出错: {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"保存智能体配置出错: {str(e)}")


@chat.get("/agent/{agent_name}/history")
async def get_agent_history(
        agent_name: str,
        thread_id: str,
        current_user: User = Depends(get_required_user)
):
    """获取智能体历史消息（需要登录）"""
    # if agent_name == "ragflow":
    async with aiosqlite.connect(RAGFLOW_HISTORY_DB) as db:
        cursor = await db.execute(
            "SELECT role, content,reference, create_at FROM history WHERE thread_id=? AND user_id=? AND agent_id=? ORDER BY id ASC",
            (thread_id, current_user.id, agent_name)
        )
        rows = await cursor.fetchall()
        history = [
            {
                "role": row[0],
                "type": "human" if row[0] == "user" else "ai",
                "content": row[1],
                "reference":row[2],
                "create_at": row[3]
            }
            for row in rows
        ]
    return {"history": history}
    # try:
    #     # 获取Agent实例和配置类
    #     agent = agent_manager.get_agent(agent_name)
    #     if not agent:
    #         raise HTTPException(status_code=404, detail=f"智能体 {agent_name} 不存在")
    #
    #     # 获取历史消息
    #     history = await agent.get_history(user_id=current_user.id, thread_id=thread_id)
    #     return {"history": history}
    #
    # except Exception as e:
    #     logger.error(f"获取智能体历史消息出错: {e}, {traceback.format_exc()}")
    #     raise HTTPException(status_code=500, detail=f"获取智能体历史消息出错: {str(e)}")


@chat.get("/agent/{agent_name}/config")
async def get_agent_config(
        agent_name: str,
        current_user: User = Depends(get_required_user)
):
    """从YAML文件加载智能体配置（需要登录）"""
    try:
        # 检查智能体是否存在
        if not (agent := agent_manager.get_agent(agent_name)):
            raise HTTPException(status_code=404, detail=f"智能体 {agent_name} 不存在")

        config = agent.config_schema.from_runnable_config(config={}, agent_name=agent_name)
        return {"success": True, "config": config}

    except Exception as e:
        logger.error(f"加载智能体配置出错: {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"加载智能体配置出错: {str(e)}")


# ==================== 线程管理 API ====================

class ThreadCreate(BaseModel):
    title: str | None = None
    agent_id: str
    description: str | None = None
    metadata: dict | None = None


class ThreadResponse(BaseModel):
    id: str
    user_id: str
    agent_id: str
    title: str | None = None
    description: str | None = None
    create_at: str
    update_at: str


@chat.post("/thread", response_model=ThreadResponse)
async def create_thread(
        thread: ThreadCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_required_user)
):
    """创建新对话线程"""
    thread_id = str(uuid.uuid4())

    new_thread = Thread(
        id=thread_id,
        user_id=current_user.id,
        agent_id=thread.agent_id,
        title=thread.title or "新对话",
        description=thread.description,
    )

    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)

    """关联ragflow"""
    ragflow_resp= await ragflow_create_session_with_chat_assistant(thread.title or "新对话")
    chat_id=ragflow_resp['data']['chat_id']
    session_id=ragflow_resp['data']['id']
    db_manager.add_ragflow(thread_id=thread_id, chat_id=chat_id, session_id=session_id)

    return {
        "id": new_thread.id,
        "user_id": new_thread.user_id,
        "agent_id": new_thread.agent_id,
        "title": new_thread.title,
        "description": new_thread.description,
        "create_at": new_thread.create_at.isoformat(),
        "update_at": new_thread.update_at.isoformat(),
        "chat_id": chat_id,
        "session_id": session_id,
    }


@chat.get("/threads", response_model=list[ThreadResponse])
async def list_threads(
        agent_id: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_required_user)
):
    """获取用户的所有对话线程"""
    query = db.query(Thread).filter(
        Thread.user_id == current_user.id,
        Thread.status == 1
    )

    if agent_id:
        query = query.filter(Thread.agent_id == agent_id)

    threads = query.order_by(Thread.update_at.desc()).all()

    return [
        {
            "id": thread.id,
            "user_id": thread.user_id,
            "agent_id": thread.agent_id,
            "title": thread.title,
            "description": thread.description,
            "create_at": thread.create_at.isoformat(),
            "update_at": thread.update_at.isoformat(),
        }
        for thread in threads
    ]


@chat.delete("/thread/{thread_id}")
async def delete_thread(
        thread_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_required_user)
):
    """删除对话线程"""
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == current_user.id
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="对话线程不存在")

    # 软删除
    thread.status = 0
    db.commit()

    return {"message": "删除成功"}


class ThreadUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


@chat.put("/thread/{thread_id}", response_model=ThreadResponse)
async def update_thread(
        thread_id: str,
        thread_update: ThreadUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_required_user)
):
    """更新对话线程信息"""
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == current_user.id,
        Thread.status == 1
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="对话线程不存在")

    if thread_update.title is not None:
        thread.title = thread_update.title

    if thread_update.description is not None:
        thread.description = thread_update.description

    db.commit()
    db.refresh(thread)

    return {
        "id": thread.id,
        "user_id": thread.user_id,
        "agent_id": thread.agent_id,
        "title": thread.title,
        "description": thread.description,
        "create_at": thread.create_at.isoformat(),
        "update_at": thread.update_at.isoformat(),
    }
