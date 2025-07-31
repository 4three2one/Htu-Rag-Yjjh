from server.third.utils import make_chunk, RAGFLOW_HISTORY_DB, save_ragflow_history
from src.utils.logging_config import logger
from langchain_core.messages import AIMessageChunk, HumanMessage
from server.third.ragflow_http_api import *
import time
import uuid
from langchain_openai import ChatOpenAI


def process_content(content):
    import re
    # 先替换所有 [ID:数字] 为 ⓘ
    processed_content = re.sub(r'\[ID:\d+\]', r'ⓘ', content)
    # 然后合并连续的 ⓘ 符号，只保留一个
    processed_content = re.sub(r'(ⓘ\s*)+', r'ⓘ', processed_content)
    return processed_content


async def stream_messages_4_ragflow(agent_name, query, request_id, session_id, meta, current_user, config):
    delay = 0.01
    # chat_id = None
    current_answer_id = str(uuid.uuid4())

    yield make_chunk(status="init", request_id=request_id, meta=meta, msg=HumanMessage(content=query).model_dump())
    # 正确处理流式数据
    last_content = ""
    ai_content = ""
    ragflow_data = None

    async for message in ragflow_chat_completion_origin(query, session_id=session_id):
        logger.debug(f"收到RAGFlow消息: {message}")

        # 检查是否有错误
        if "error" in message:
            yield make_chunk(status="error", request_id=request_id, message=message["error"], meta=meta)
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
                ai_msg=process_content(ai_content),
                reference=ragflow_data['reference'],
            )
            yield make_chunk(status="finished", request_id=request_id, meta=meta)
            continue

        # 格式1: OpenAI兼容格式
        if "choices" in message and len(message["choices"]) > 0:
            choice = message["choices"][0]
            if "delta" in choice and "content" in choice["delta"]:
                content = choice["delta"]["content"]
                msg_data = {
                    "content": content,
                    "id": current_answer_id,
                    "role": "assistant",
                    "type": "ai"
                }

        # ragflow格式
        elif "answer" in message:
            content = message["answer"]
            delta = content[len(last_content):]
            ai_content += delta
            last_content = content
            ragflow_data = message
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


async def stream_messages_4_dify_openai(agent_name, query, request_id, meta, current_user, config):

    print("agent_name", agent_name)
    if "报告" in agent_name:
        model = "dify|app-W1fb9flI4juhc6jcjIUgLMRj|Chat"
    else:
        model="dify|app-srwTCijv7vzZF3OWbPMh28ao|Chat"

    current_answer_id = str(uuid.uuid4())
    yield make_chunk(status="init",  request_id=request_id,meta=meta, msg=HumanMessage(content=query).model_dump())
    chat_model = ChatOpenAI(
        api_key="http://192.168.1.118:18080/v1",
        base_url="http://192.168.1.118:3099/v1",
        # model="dify|app-W1fb9flI4juhc6jcjIUgLMRj|Chat",
        model=model,
        streaming=True,
    )
    messages = [HumanMessage(content=query)]

    ai_content = ""
    async for chunk in chat_model.astream(messages):
        if hasattr(chunk, "content"):
            ai_content += chunk.content
            print(f"接收到 dify openai message {chunk.content=}")

            msg_data = {
                "content": chunk.content,
                "id": current_answer_id,
                "role": "assistant",
                "reference": [],
                "type": "ai",
            }
            yield make_chunk(content=chunk.content,  request_id=request_id,msg=msg_data, metadata=meta,status="loading")

    await save_ragflow_history(
        thread_id=config["thread_id"],
        user_id=current_user.id,
        agent_id=agent_name,
        user_msg=query,
        ai_msg=process_content(ai_content),
        reference=[],
    )
    yield make_chunk(status="finished", meta=meta,request_id=request_id,)
