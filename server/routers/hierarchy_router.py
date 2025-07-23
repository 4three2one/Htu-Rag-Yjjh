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

data = APIRouter(prefix="/hierarchy")


@data.post("/add")
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


@data.get("/info")
async def get_knowledge_hierarchy(db_id: str, current_user: User = Depends(get_admin_user)):
    hierarchy = db_manager.get_knowledge_hierarchy(db_id)
    if not hierarchy:
        return {"message": "未找到层级信息", "hierarchy": None}
    logger.info(f"Get hierarchy info: {hierarchy}")
    return {"hierarchy": hierarchy}  # 直接返回，因为已经是字典了


@data.get("/children")
async def get_children_knowledge(parent_db_id: str, current_user: User = Depends(get_admin_user)):
    children = db_manager.get_children_knowledge(parent_db_id)
    return {"children": children}  # 直接返回，因为已经是字典列表了


@data.get("/all")
async def get_all_knowledge_hierarchy(current_user: User = Depends(get_admin_user)):
    all_hierarchy = db_manager.get_all_knowledge_hierarchy()
    return {"all_hierarchy": all_hierarchy}  # 直接返回，因为已经是字典列表了


@data.delete("/delete")
async def delete_knowledge_hierarchy(db_id: str = Body(...), current_user: User = Depends(get_admin_user)):
    db_manager.delete_knowledge_hierarchy(db_id)
    return {"message": "删除成功"}
