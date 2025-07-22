import httpx
from typing import Optional, Dict, Any
import os
from src.utils import logger

# 配置 ragflow HTTP API 基础地址和 API KEY
api_key = os.getenv("RAGFLOW_API_KEY", "ragflow-RmMDAyNzJlNWE0MjExZjA4MGMyN2VjZG")
base_url = os.getenv("RAGFLOW_BASE_URL", "http://47.117.45.109:20006")
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
        json_resp=resp.json()
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
