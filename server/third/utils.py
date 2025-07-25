import json
import os
import aiosqlite



RAGFLOW_HISTORY_DB = os.path.join("saves", "agents", "ragflow", "aio_history.db")
os.makedirs(os.path.dirname(RAGFLOW_HISTORY_DB), exist_ok=True)

def make_chunk(content=None, request_id=None, **kwargs):
    chunk_data = {
        "request_id": request_id,
        **kwargs
    }
    
    # 同时支持response和content字段
    if content is not None:
        chunk_data["response"] = content
        chunk_data["content"] = content
    
    return json.dumps(chunk_data, ensure_ascii=False) + "\n"



async def save_ragflow_history(thread_id, user_id, agent_id, user_msg, ai_msg):
    async with aiosqlite.connect(RAGFLOW_HISTORY_DB) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS history
               (
                   id
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   thread_id
                   TEXT,
                   user_id
                   TEXT,
                   agent_id
                   TEXT,
                   role
                   TEXT,
                   content
                   TEXT,
                   create_at
                   TIMESTAMP
                   DEFAULT
                   CURRENT_TIMESTAMP
               )"""
        )
        await db.execute(
            "INSERT INTO history (thread_id, user_id, agent_id, role, content) VALUES (?, ?, ?, ?, ?)",
            (thread_id, user_id, agent_id, "user", user_msg)
        )
        await db.execute(
            "INSERT INTO history (thread_id, user_id, agent_id, role, content) VALUES (?, ?, ?, ?, ?)",
            (thread_id, user_id, agent_id, "assistant", ai_msg)
        )
        await db.commit()