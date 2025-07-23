import os
import asyncio
import traceback
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Body, Form, Query
from typing import Optional

from src.utils import logger, hashstr
from src import executor, config, knowledge_base, graph_base
from server.utils.auth_middleware import get_admin_user
from server.models.user_model import User
from server.third.ragflow import *
from server.third.ragflow_http_api import list_documents_http, list_datasets_http, update_dataset_http
from server.third.data_transfer import *
from server.db_manager import db_manager

data = APIRouter(prefix="/knowledge")


@data.get("/")
async def api_get_databases(current_user: User = Depends(get_admin_user)):
    try:
        database = await list_datasets_http()
    except Exception as e:
        logger.error(f"获取数据库列表失败 {e}, {traceback.format_exc()}")
        return {"message": f"获取数据库列表失败 {e}", "knowledge_items": []}
    return transform_database_li_data(database)


@data.post("/")
async def api_create_database(
        knowledge_name: str = Body(...),
        description: str = Body(...),
        parent_db_id: Optional[str] = Body(None),
        # embed_model_name: str = Body(...),
        current_user: User = Depends(get_admin_user)
):
    try:
        newly_dataset = create_dataset(knowledge_name, description)
        # 插入层次关系
        if parent_db_id and parent_db_id != "null" and parent_db_id != "undefined":
            db_manager.add_knowledge_hierarchy(newly_dataset['id'], parent_db_id)
        else:
            db_manager.add_knowledge_hierarchy(newly_dataset['id'], None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建数据库失败 {e}, {traceback.format_exc()}")
        return {"message": f"创建数据库失败 {e}", "status": "failed"}
    return newly_dataset


@data.delete("/")
async def api_delete_database(db_id, current_user: User = Depends(get_admin_user)):
    logger.debug(f"Delete database {db_id}")
    delete_dataset(db_id)
    # 级联删除层级结构
    db_manager.delete_knowledge_hierarchy(db_id)
    return {"message": "删除成功"}


@data.get("/info")
async def api_get_database_info(db_id: str, current_user: User = Depends(get_admin_user)):
    # logger.debug(f"Get database {db_id} info")
    database = get_dataset(db_id)
    if database is None:
        raise HTTPException(status_code=404, detail="Database not found")
    db_files = await list_documents_http(db_id)

    return transform_database_data(database, db_files)


@data.post("/add-files")
async def api_add_files(db_id: str = Body(...), items: list[str] = Body(...), params: dict = Body(...),
                        current_user: User = Depends(get_admin_user)):
    logger.debug(f"Add files/urls for db_id {db_id}: {items} {params=}")

    # 从 params 中获取 content_type，默认为 'file'
    content_type = params.get('content_type', 'file')

    try:
        li_result = []
        for item in items:
            upload_response = upload_document_third_with_parse(db_id, item)
            li_result.append(upload_response)
        return {"message": "", "items": li_result, "status": "success"}
        # # 使用统一的 add_content 方法
        # processed_items = await knowledge_base.add_content(db_id, items, params=params)
        #
        # item_type = "URLs" if content_type == 'url' else "files"
        # processed_failed_count = len([_p for _p in processed_items if _p['status'] == 'failed'])
        # processed_info = f"Processed {len(processed_items)} {item_type}, {processed_failed_count} {item_type} failed"
        # return {"message": processed_info, "items": processed_items, "status": "success"}
    except Exception as e:
        logger.error(f"Failed to process {content_type}s: {e}, {traceback.format_exc()}")
        return {"message": f"Failed to process {content_type}s: {e}", "status": "failed"}


@data.delete("/document")
async def api_delete_document(db_id: str = Body(...), file_id: str = Body(...),
                              current_user: User = Depends(get_admin_user)):
    logger.debug(f"DELETE document {file_id} info in {db_id}")
    delete_flag = delete_document(db_id, file_id)
    if delete_flag:
        return {"message": "删除成功"}
    return {"message": "删除失败"}


@data.post("/update")
async def api_update_database_info(
        db_id: str = Body(...),
        name: str = Body(...),
        description: str = Body(...),
        parent_db_id: Optional[str] = Body(None),
        current_user: User = Depends(get_admin_user)
):
    logger.debug(f"Update database {db_id} info: {name}, {description},{parent_db_id}")
    try:
        # 检测循环依赖
        if parent_db_id and parent_db_id != "null" and parent_db_id != "undefined":
            # 检查是否会造成循环依赖
            def check_circular_dependency(current_id, target_parent_id, visited=None):
                if visited is None:
                    visited = set()
                
                # if current_id in visited:
                #     return False  # 没有循环
                
                visited.add(current_id)
                
                # 如果目标父级是当前节点，则形成循环
                if target_parent_id == current_id:
                    return True
                
                # 获取目标父级的父级
                parent_info = db_manager.get_knowledge_hierarchy(target_parent_id)
                if parent_info and parent_info.get('parent_db_id'):
                    return check_circular_dependency(current_id, parent_info['parent_db_id'], visited)
                
                return False
            
            if check_circular_dependency(db_id, parent_db_id):
                raise HTTPException(status_code=400, detail="检测到循环依赖，无法设置此父级知识库")
        
        database = await update_dataset_http(db_id, name=name, description=description)
        # 更新层次结构
        db_manager.delete_knowledge_hierarchy(db_id)
        if parent_db_id and parent_db_id != "null" and parent_db_id != "undefined":
            db_manager.add_knowledge_hierarchy(db_id, parent_db_id)
        else:
            db_manager.add_knowledge_hierarchy(db_id, None)
        return {"message": "更新成功", "database": database}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新数据库失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"更新数据库失败: {e}")


# %% 待调整的API
@data.post("/query-test")
async def query_test(query: str = Body(...), meta: dict = Body(...), current_user: User = Depends(get_admin_user)):
    logger.debug(f"Query test in {meta}: {query}")
    result = await knowledge_base.aquery(query, **meta)
    return result


@data.post("/file-to-chunk")
async def file_to_chunk(db_id: str = Body(...), files: list[str] = Body(...), params: dict = Body(...),
                        current_user: User = Depends(get_admin_user)):
    logger.debug(f"File to chunk for db_id {db_id}: {files} {params=} (deprecated, use /add-files)")
    # 兼容性路由，转发到新的统一接口
    params['content_type'] = 'file'
    return await add_files(db_id, files, params, current_user)


@data.post("/url-to-chunk")
async def url_to_chunk(db_id: str = Body(...), urls: list[str] = Body(...), params: dict = Body(...),
                       current_user: User = Depends(get_admin_user)):
    logger.debug(f"Url to chunk for db_id {db_id}: {urls} {params=} (deprecated, use /add-files)")
    # 兼容性路由，转发到新的统一接口
    params['content_type'] = 'url'
    return await add_files(db_id, urls, params, current_user)


@data.post("/add-by-file")
async def create_document_by_file(db_id: str = Body(...), files: list[str] = Body(...),
                                  current_user: User = Depends(get_admin_user)):
    raise ValueError("This method is deprecated. Use /add-files instead.")


@data.post("/add-by-chunks")
async def add_by_chunks(db_id: str = Body(...), file_chunks: dict = Body(...),
                        current_user: User = Depends(get_admin_user)):
    raise ValueError("This method is deprecated. Use /add-files instead.")


# @data.delete("/document")
# async def delete_document(db_id: str = Body(...), file_id: str = Body(...),
#                           current_user: User = Depends(get_admin_user)):
#     logger.debug(f"DELETE document {file_id} info in {db_id}")
#     await knowledge_base.delete_file(db_id, file_id)
#     return {"message": "删除成功"}


@data.get("/document")
async def get_document_info(db_id: str, file_id: str, current_user: User = Depends(get_admin_user)):
    logger.debug(f"GET document {file_id} info in {db_id}")

    try:
        info = await knowledge_base.get_file_info(db_id, file_id)
    except Exception as e:
        logger.error(f"Failed to get file info, {e}, {db_id=}, {file_id=}, {traceback.format_exc()}")
        info = {"message": "Failed to get file info", "status": "failed"}

    return info


@data.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        db_id: str | None = Query(None),
        current_user: User = Depends(get_admin_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    # 根据db_id获取上传路径，如果db_id为None则使用默认路径
    if db_id:
        upload_dir = knowledge_base.get_db_upload_path(db_id)
    else:
        upload_dir = os.path.join(config.save_dir, "database", "uploads")

    basename, ext = os.path.splitext(file.filename)
    filename = f"{basename}_{hashstr(basename, 4, with_salt=True)}{ext}".lower()
    file_path = os.path.join(upload_dir, filename)
    os.makedirs(upload_dir, exist_ok=True)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"message": "File successfully uploaded", "file_path": file_path, "db_id": db_id}


@data.get("/graph")
async def get_graph_info(current_user: User = Depends(get_admin_user)):
    graph_info = graph_base.get_graph_info()
    if graph_info is None:
        raise HTTPException(status_code=400, detail="图数据库获取出错")
    return graph_info


@data.post("/graph/index-nodes")
async def index_nodes(data: dict = Body(default={}), current_user: User = Depends(get_admin_user)):
    if not graph_base.is_running():
        raise HTTPException(status_code=400, detail="图数据库未启动")

    # 获取参数或使用默认值
    kgdb_name = data.get('kgdb_name', 'neo4j')

    # 调用GraphDatabase的add_embedding_to_nodes方法
    count = graph_base.add_embedding_to_nodes(kgdb_name=kgdb_name)

    return {"status": "success", "message": f"已成功为{count}个节点添加嵌入向量", "indexed_count": count}


@data.get("/graph/node")
async def get_graph_node(entity_name: str, current_user: User = Depends(get_admin_user)):
    result = graph_base.query_node(entity_name=entity_name)
    return {"result": graph_base.format_query_result_to_graph(result), "message": "success"}


@data.get("/graph/nodes")
async def get_graph_nodes(kgdb_name: str, num: int, current_user: User = Depends(get_admin_user)):
    logger.debug(f"Get graph nodes in {kgdb_name} with {num} nodes")
    result = graph_base.get_sample_nodes(kgdb_name, num)
    return {"result": graph_base.format_general_results(result), "message": "success"}


@data.post("/graph/add-by-jsonl")
async def add_graph_entity(file_path: str = Body(...), kgdb_name: str | None = Body(None),
                           current_user: User = Depends(get_admin_user)):
    if not file_path.endswith('.jsonl'):
        return {"message": "文件格式错误，请上传jsonl文件", "status": "failed"}

    try:
        await graph_base.jsonl_file_add_entity(file_path, kgdb_name)
        return {"message": "实体添加成功", "status": "success"}
    except Exception as e:
        logger.error(f"添加实体失败: {e}, {traceback.format_exc()}")
        return {"message": f"添加实体失败: {e}", "status": "failed"}


@data.post("/hierarchy/add")
async def add_knowledge_hierarchy(
        db_id: str = Body(...),
        parent_db_id: str = Body(None),
        order: int = Body(0),
        current_user: User = Depends(get_admin_user)
):
    try:
        hierarchy = db_manager.add_knowledge_hierarchy(db_id, parent_db_id, order)
        return {"message": "添加成功", "hierarchy": hierarchy}  # 直接返回，因为已经是字典了
    except Exception as e:
        logger.error(f"添加知识库层级失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"添加失败: {e}")


@data.get("/hierarchy/info")
async def get_knowledge_hierarchy(db_id: str, current_user: User = Depends(get_admin_user)):
    hierarchy = db_manager.get_knowledge_hierarchy(db_id)
    if not hierarchy:
        return {"message": "未找到层级信息", "hierarchy": None}
    return {"hierarchy": hierarchy}  # 直接返回，因为已经是字典了


@data.get("/hierarchy/children")
async def get_children_knowledge(parent_db_id: str, current_user: User = Depends(get_admin_user)):
    children = db_manager.get_children_knowledge(parent_db_id)
    return {"children": children}  # 直接返回，因为已经是字典列表了


@data.get("/hierarchy/all")
async def get_all_knowledge_hierarchy(current_user: User = Depends(get_admin_user)):
    all_hierarchy = db_manager.get_all_knowledge_hierarchy()
    return {"all_hierarchy": all_hierarchy}  # 直接返回，因为已经是字典列表了


@data.delete("/hierarchy/delete")
async def delete_knowledge_hierarchy(db_id: str = Body(...), current_user: User = Depends(get_admin_user)):
    db_manager.delete_knowledge_hierarchy(db_id)
    return {"message": "删除成功"}
