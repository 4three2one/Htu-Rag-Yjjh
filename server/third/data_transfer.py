
def transform_database_li_data(original_data):
    # 转换为前端期望的格式
    knowledge_items = []
    
    for item in original_data:
        knowledge_item = {
            "id": item["id"],
            "name": item["name"],
            "description": item["description"] or "",
            "type": "document",  # 默认类型
            "content_count": item["document_count"] or 0,
            "status": "active",
            "created_at": item["created_at"] or "",
            "updated_at": item.get("updated_at", ""),
            # 保留原始数据用于兼容性
            "db_id": item["id"],
            "embed_info": {
                "name": item["embedding_model"].split("@")[0] if "embedding_model" in item else "BAAI/bge-large-zh-v1.5",
                # "dimension": 1024,
                "base_url": "",
                "api_key": ""
            },
            "metadata": {},
            "files": {},
            "row_count": 0
        }
        knowledge_items.append(knowledge_item)

    return {"knowledge_items": knowledge_items}


def transform_database_data(original_item,db_files):
    # 转换为前端期望的格式
    knowledge_item = {
        "id": original_item["id"],
        "name": original_item["name"],
        "description": original_item["description"] or "",
        "type": "document",  # 默认类型
        "content_count": 0,  # 暂时设为0，后续可以从文档数量获取
        "status": "active",
        "created_at": original_item["created_at"] or "",
        "updated_at": original_item.get("updated_at", ""),
        # 保留原始数据用于兼容性
        "db_id": original_item["id"],
        "embed_info": {
            "name": original_item["embedding_model"].split("@")[
                0] if "embedding_model" in original_item else "BAAI/bge-large-zh-v1.5",
            "dimension": 1024,
            "base_url": "",
            "api_key": ""
        },
        "metadata": {},
        "files": db_files,
        "row_count": 0
    }

    return knowledge_item