import requests
import json

API_BASE = "http://47.117.45.109:20006/api/v1"
API_KEY = "ragflow-k4OThiYTgwNjdkNTExZjA5OTBiODIyYT"
CHAT_ID = "be0d226a63a211f0a894822a712eb46f"

# 设置请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


def chat_completion(question, session_id, stream=True):
    """
    向RAGFlow API发送聊天完成请求

    参数:
        question: 要询问的问题
        session_id: 会话ID
        stream: 是否使用流式响应

    返回:
        如果是流式响应，返回生成器
        如果是非流式响应，返回完整的响应数据
    """
    payload = {
        "question": question,
        "stream": stream,
        "session_id": session_id
    }

    try:
        response = requests.post(
            f"{API_BASE}/chats/{CHAT_ID}/completions",
            headers=headers,
            json=payload,
            stream=stream  # 启用流式传输
        )
        response.raise_for_status()

        if stream:
            # 处理流式响应
            def generate():
                for line in response.iter_lines():
                    if line:
                        yield line.decode('utf-8')

            return generate()
        else:
            # 处理非流式响应
            return response.json()

    except requests.exceptions.RequestException as e:
        print(f"请求RAGFlow API时出错: {e}")
        return None


# 示例使用
if __name__ == "__main__":
    # 示例参数
    question = "合肥监管处在哪里"
    session_id = "e52668aa684011f085b2822a712eb46f"

    # 流式响应示例
    print("流式响应结果:")
    stream_response = chat_completion(question, session_id, stream=True)
    if stream_response:
        for chunk in stream_response:
            print(chunk)

    # # 非流式响应示例
    # print("\n非流式响应结果:")
    # full_response = chat_completion(question, session_id, stream=False)
    # if full_response:
    #     print(json.dumps(full_response, indent=2))