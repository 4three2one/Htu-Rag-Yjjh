import os

# 配置 ragflow HTTP API 基础地址和 API KEY
api_key = os.getenv("RAGFLOW_API_KEY", "")
base_url = os.getenv("RAGFLOW_BASE_URL", "")
chat_id=os.getenv("RAGFLOW_CHAT_ID", "")


headers = {
    "Authorization": f"Bearer {api_key}"
}