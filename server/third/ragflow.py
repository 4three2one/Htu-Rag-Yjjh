"""
RagFlow SDK 包装模块

基于 RagFlow Python SDK 提供便捷的接口函数，参考 data_router.py 的编写风格。
"""

import os
import traceback
from typing import Dict, List, Optional, Any
from src.utils import logger
from ragflow_sdk import RAGFlow


# 全局 RagFlow 客户端实例
_ragflow_client: Optional[RAGFlow] = None


def get_ragflow_client() -> Optional[RAGFlow]:
    """获取 RagFlow 客户端实例"""
    global _ragflow_client
    
    if _ragflow_client is None:
        try:
            # 从环境变量获取配置
            api_key = os.getenv("RAGFLOW_API_KEY", "ragflow-RmMDAyNzJlNWE0MjExZjA4MGMyN2VjZG")
            base_url = os.getenv("RAGFLOW_BASE_URL", "http://47.117.45.109:20006")
            
            _ragflow_client = RAGFlow(api_key=api_key, base_url=base_url)
            logger.info(f"RagFlow 客户端初始化成功: {base_url}")
        except Exception as e:
            logger.error(f"RagFlow 客户端初始化失败: {e}")
            _ragflow_client = None
    
    return _ragflow_client


def test_ragflow_connection() -> bool:
    """测试 RagFlow 连接"""
    try:
        client = get_ragflow_client()
        if client is None:
            return False
        
        # 尝试获取数据集列表来测试连接
        datasets = client.list_datasets()
        logger.info(f"RagFlow 连接测试成功，发现 {len(datasets)} 个数据集")
        return True
    except Exception as e:
        logger.error(f"RagFlow 连接测试失败: {e}")
        return False


def create_dataset(name: str, description: str = "", embedding_model: str = "BAAI/bge-large-zh-v1.5@BAAI") -> Optional[Dict]:
    """创建数据集（知识库）"""
    try:
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return None
        
        dataset = client.create_dataset(
            name=name,
            description=description,
            embedding_model=embedding_model
        )
        
        logger.info(f"创建数据集成功: {name}")
        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "embedding_model": embedding_model
        }
    except Exception as e:
        logger.error(f"创建数据集失败: {e}, {traceback.format_exc()}")
        return None


def list_datasets(page: int = 1, page_size: int = 30) -> List[Dict]:
    """获取数据集列表"""
    try:
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return []
        
        datasets = client.list_datasets(page=page, page_size=page_size)
        result = []
        for dataset in datasets:
            result.append({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "embedding_model": getattr(dataset, 'embedding_model', ''),
                "created_at": getattr(dataset, 'created_at', ''),
                "updated_at": getattr(dataset, 'updated_at', '')
            })
        
        logger.info(f"获取数据集列表成功，共 {len(result)} 个数据集")
        return result
    except Exception as e:
        logger.error(f"获取数据集列表失败: {e}, {traceback.format_exc()}")
        return []


def get_dataset(dataset_id: str) -> Optional[Dict]:
    """获取数据集信息"""
    try:
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return None
        
        datasets = client.list_datasets(id=dataset_id)
        if not datasets:
            logger.error(f"数据集不存在: {dataset_id}")
            return None
        
        dataset = datasets[0]
        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "embedding_model": getattr(dataset, 'embedding_model', ''),
            "created_at": getattr(dataset, 'created_at', ''),
            "updated_at": getattr(dataset, 'updated_at', '')
        }
    except Exception as e:
        logger.error(f"获取数据集信息失败: {e}, {traceback.format_exc()}")
        return None


def delete_dataset(dataset_id: str) -> bool:
    """删除数据集"""
    try:
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return False
        
        client.delete_datasets(ids=[dataset_id])
        logger.info(f"删除数据集成功: {dataset_id}")
        return True
    except Exception as e:
        logger.error(f"删除数据集失败: {e}, {traceback.format_exc()}")
        return False


def upload_document_third(dataset_id: str, file_path: str, file_name: Optional[str] = None) -> Optional[Dict]:
    """上传文档到数据集 - 使用官方API格式"""
    try:
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
        
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return None
        
        # 获取数据集
        datasets = client.list_datasets(id=dataset_id)
        if not datasets:
            logger.error(f"数据集不存在: {dataset_id}")
            return None
        
        dataset = datasets[0]
        
        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 如果没有指定文件名，使用路径中的文件名
        if file_name is None:
            file_name = os.path.basename(file_path)
        
        # 使用官方API格式上传文档
        # dataset.upload_documents([{"display_name": "1.txt", "blob": "<BINARY_CONTENT_OF_THE_DOC>"}])
        documents = dataset.upload_documents([
            {
                "display_name": file_name,
                "blob": file_content
            }
        ])
        
        if not documents:
            logger.error(f"上传文档失败: 没有返回文档对象")
            return None
        
        document = documents[0]  # 获取第一个上传的文档
        
        logger.info(f"上传文档成功: {file_path} -> {document.id}")
        return {
            "id": document.id,
            "name": document.name,
            "file_path": file_path,
            "dataset_id": dataset_id
        }
    except Exception as e:
        logger.error(f"上传文档失败: {e}, {traceback.format_exc()}")
        return None


def list_documents(dataset_id: str, page: int = 1, page_size: int = 30) -> List[Dict]:
    """获取数据集中的文档列表"""
    try:
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return []
        
        # 获取数据集
        datasets = client.list_datasets(id=dataset_id)
        if not datasets:
            logger.error(f"数据集不存在: {dataset_id}")
            return []
        
        dataset = datasets[0]
        documents = dataset.list_documents(page=page, page_size=page_size)
        
        result = []
        for doc in documents:
            result.append({
                "id": doc.id,
                "name": doc.name,
                "file_path": getattr(doc, 'file_path', ''),
                "created_at": getattr(doc, 'created_at', ''),
                "dataset_id": dataset_id
            })
        
        logger.info(f"获取文档列表成功，共 {len(result)} 个文档")
        return result
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}, {traceback.format_exc()}")
        return []


def delete_document(dataset_id: str, document_id: str) -> bool:
    """删除文档"""
    try:
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return False
        
        # 获取数据集
        datasets = client.list_datasets(id=dataset_id)
        if not datasets:
            logger.error(f"数据集不存在: {dataset_id}")
            return False
        
        dataset = datasets[0]
        dataset.delete_document(document_id=document_id)
        
        logger.info(f"删除文档成功: {document_id}")
        return True
    except Exception as e:
        logger.error(f"删除文档失败: {e}, {traceback.format_exc()}")
        return False


def query_dataset(dataset_id: str, query: str, top_k: int = 5) -> Optional[Dict]:
    """查询数据集"""
    try:
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return None
        
        # 获取数据集
        datasets = client.list_datasets(id=dataset_id)
        if not datasets:
            logger.error(f"数据集不存在: {dataset_id}")
            return None
        
        dataset = datasets[0]
        
        # 执行查询
        results = dataset.query(query=query, top_k=top_k)
        
        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.content,
                "metadata": getattr(result, 'metadata', {}),
                "score": getattr(result, 'score', 0.0),
                "document_id": getattr(result, 'document_id', '')
            })
        
        logger.info(f"查询数据集成功: {query} -> {len(formatted_results)} 个结果")
        return {
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "dataset_id": dataset_id
        }
    except Exception as e:
        logger.error(f"查询数据集失败: {e}, {traceback.format_exc()}")
        return None


def get_document_info(dataset_id: str, document_id: str) -> Optional[Dict]:
    """获取文档信息"""
    try:
        client = get_ragflow_client()
        if client is None:
            logger.error("RagFlow 客户端未初始化")
            return None
        
        # 获取数据集
        datasets = client.list_datasets(id=dataset_id)
        if not datasets:
            logger.error(f"数据集不存在: {dataset_id}")
            return None
        
        dataset = datasets[0]
        documents = dataset.list_documents(id=document_id)
        
        if not documents:
            logger.error(f"文档不存在: {document_id}")
            return None
        
        document = documents[0]
        return {
            "id": document.id,
            "name": document.name,
            "file_path": getattr(document, 'file_path', ''),
            "created_at": getattr(document, 'created_at', ''),
            "dataset_id": dataset_id
        }
    except Exception as e:
        logger.error(f"获取文档信息失败: {e}, {traceback.format_exc()}")
        return None


# 异步包装函数（如果需要）
async def async_test_connection() -> bool:
    """异步测试连接"""
    return test_ragflow_connection()


async def async_create_dataset(name: str, description: str = "", embedding_model: str = "BAAI/bge-large-zh-v1.5@BAAI") -> Optional[Dict]:
    """异步创建数据集"""
    return create_dataset(name, description, embedding_model)


async def async_list_datasets(page: int = 1, page_size: int = 30) -> List[Dict]:
    """异步获取数据集列表"""
    return list_datasets(page, page_size)


async def async_get_dataset(dataset_id: str) -> Optional[Dict]:
    """异步获取数据集信息"""
    return get_dataset(dataset_id)


async def async_delete_dataset(dataset_id: str) -> bool:
    """异步删除数据集"""
    return delete_dataset(dataset_id)


async def async_upload_document(dataset_id: str, file_path: str, file_name: Optional[str] = None) -> Optional[Dict]:
    """异步上传文档"""
    return upload_document_third(dataset_id, file_path, file_name)


async def async_list_documents(dataset_id: str, page: int = 1, page_size: int = 30) -> List[Dict]:
    """异步获取文档列表"""
    return list_documents(dataset_id, page, page_size)


async def async_delete_document(dataset_id: str, document_id: str) -> bool:
    """异步删除文档"""
    return delete_document(dataset_id, document_id)


async def async_query_dataset(dataset_id: str, query: str, top_k: int = 5) -> Optional[Dict]:
    """异步查询数据集"""
    return query_dataset(dataset_id, query, top_k)


async def async_get_document_info(dataset_id: str, document_id: str) -> Optional[Dict]:
    """异步获取文档信息"""
    return get_document_info(dataset_id, document_id)

if __name__ == '__main__':
    test_ragflow_connection()