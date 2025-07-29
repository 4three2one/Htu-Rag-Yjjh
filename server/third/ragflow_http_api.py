import httpx
from typing import Optional, Dict, Any, List
import os
from src.utils import logger
import requests
import json
from typing import AsyncGenerator

# 配置 ragflow HTTP API 基础地址和 API KEY
api_key = os.getenv("RAGFLOW_API_KEY", "")
base_url = os.getenv("RAGFLOW_BASE_URL", "")
chat_id=os.getenv("RAGFLOW_CHAT_ID", "")


headers = {
    "Authorization": f"Bearer {api_key}"
}


async def list_documents_http(
        dataset_id: str,
        page: int = 1,
        page_size: int = 30,
        orderby: Optional[str] = None,
        desc: Optional[bool] = None,
        keywords: Optional[str] = None,
        document_id: Optional[str] = None,
        document_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    通过 HTTP API 获取 ragflow 数据集下的文档列表。
    """
    url = f"{base_url}/api/v1/datasets/{dataset_id}/documents"
    params = {
        "page": page,
        "page_size": page_size
    }
    logger.info(f" dataset: {dataset_id}")
    if orderby:
        params["orderby"] = orderby
    if desc is not None:
        params["desc"] = str(desc).lower()
    if keywords:
        params["keywords"] = keywords
    if document_id:
        params["id"] = document_id
    if document_name:
        params["name"] = document_name

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        json_resp = resp.json()
        documents = json_resp['data']['docs']
        db_files = {}
        for doc in documents:
            db_files[doc['id']] = {
                "file_id": doc['id'],
                "filename": doc.get('name', ''),
                "create_time": doc.get('create_time', ''),
                "path": doc.get('file_path', ''),
                "type": doc.get('type', ''),
                "run": doc.get('run', ''),
                "status": doc.get('status', ''),
                "chunk_count": doc.get('chunk_count', ''),
                "chunk_method": doc.get('chunk_method', ''),
                "dataset_id": dataset_id
            }
        logger.info(f"获取文档列表成功，共 {len(db_files)} 个文档")
        return db_files


async def list_datasets_http(
        page: int = 1,
        page_size: int = 30,
        orderby: Optional[str] = None,
        desc: Optional[bool] = None,
        name: Optional[str] = None,
        dataset_id: Optional[str] = None
) -> List[Any]:
    """
    通过 HTTP API 获取 ragflow 的数据集列表。
    """
    url = f"{base_url}/api/v1/datasets"
    params = {
        "page": page,
        "page_size": page_size
    }
    logger.info(f" dataset: {dataset_id}")
    if orderby:
        params["orderby"] = orderby
    if desc is not None:
        params["desc"] = str(desc).lower()
    if name:
        params["name"] = name
    if dataset_id:
        params["id"] = dataset_id

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        json_resp = resp.json()
        datasets = json_resp['data']
        result = []
        for dataset in datasets:
            result.append({
                "id": dataset.get('id', ''),
                "name": dataset.get('name', ''),
                "description": dataset.get('description', ''),
                "document_count": dataset.get('document_count', ''),
                "embedding_model": dataset.get('embedding_model', ''),
                "created_at": dataset.get('create_time', ''),
                "updated_at": dataset.get('updated_at', '')
            })
        return result


async def update_dataset_http(
        dataset_id: str,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
        description: Optional[str] = None,
        embedding_model: Optional[str] = None,
        permission: Optional[str] = None,
        chunk_method: Optional[str] = None,
        pagerank: Optional[int] = None,
        parser_config: Optional[dict] = None,
) -> dict:
    """
    通过 HTTP API 更新 ragflow 数据集信息。
    """
    url = f"{base_url}/api/v1/datasets/{dataset_id}"
    payload = {}
    if name is not None:
        payload["name"] = name
    if avatar is not None:
        payload["avatar"] = avatar
    if description is not None:
        payload["description"] = description
    if embedding_model is not None:
        payload["embedding_model"] = embedding_model
    if permission is not None:
        payload["permission"] = permission
    if chunk_method is not None:
        payload["chunk_method"] = chunk_method
    if pagerank is not None:
        payload["pagerank"] = pagerank
    if parser_config is not None:
        payload["parser_config"] = parser_config

    logger.info(f"更新数据集 {dataset_id}，payload: {payload}")
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            url,
            headers={**headers, "content-Type": "application/json"},
            json=payload
        )
        resp.raise_for_status()
        return resp.json()


async def ragflow_chat_completion_openai(query):
    from openai import OpenAI
    import asyncio
    model = "model"
    client = OpenAI(api_key="ragflow-k4OThiYTgwNjdkNTExZjA5OTBiODIyYT",
                    base_url=f"http://47.117.45.109:20006/api/v1/chats_openai/{chat_id}")
    logger.info(f"ragflow_chat_completion_openai , {query}")
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{query}"},
        ],
        stream=True
    )

    for chunk in completion:
        print(chunk)
        yield chunk


# 异步原生 API 版本
async def ragflow_chat_completion_origin(
        question: str,
        session_id: str = None,
        stream: bool = True
) -> AsyncGenerator:
    """异步调用原生 RAGFlow API"""
    payload = {
        "question": question,
        "stream": stream,
        "session_id": session_id
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"  # 请确保 api_key 已定义
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/api/v1/chats/{chat_id}/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            if stream:
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    # 处理可能的 SSE 格式 (data: {...}) 或纯 JSON
                    if line.startswith("data:"):
                        line = line[5:].strip()

                    try:
                        chunk = json.loads(line)
                        yield chunk
                    except json.JSONDecodeError:
                        continue
            else:
                yield response.json()

        except httpx.HTTPStatusError as e:
            yield {"error": f"HTTP 错误: {e.response.status_code}"}
        except Exception as e:
            yield {"error": f"请求失败: {str(e)}"}



async def ragflow_create_session_with_chat_assistant(
        name: str = "新会话",
) -> Any:
    """
    RAGFlow API 创建会话
    """
    data = {
        "name": name
    }
    url = f"{base_url}/api/v1/chats/{chat_id}/sessions"
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # 如果请求失败会抛出异常
    return response.json()



async def ragflow_download_url(
        dataset_id: str,
        document_id: str,
):
    """
    RAGFlow API 下载文件
    """
    url = f"{base_url}/api/v1/datasets/{dataset_id}/documents/{document_id}"
    print(f"download url: {url}")
    return  {
        "url": url,
        "headers": headers,
    }

async def ragflow_preview_link(
        dataset_id: str,
        document_id: str,
        document_name: str,
):
    url = f"{base_url}/document/{document_id}?ext=docx&prefix=document"
    return {
        "url": url,
    }
