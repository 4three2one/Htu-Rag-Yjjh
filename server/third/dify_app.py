from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 初始化ChatOpenAI客户端
llm = ChatOpenAI(
    api_key="http://192.168.1.118:18080/v1",
    base_url="http://192.168.1.118:3099/v1",
    model="dify|app-W1fb9flI4juhc6jcjIUgLMRj|Chat",
    streaming=True,
)

# 定义要发送的问题
question = "给我生成月度总结"

# 创建人类消息对象
message = HumanMessage(content=question)

# 流式调用并打印响应
print("开始接收流式响应：")
for chunk in llm.stream([message]):
    # 打印每个流式返回的chunk内容
    print(chunk.content, end="", flush=True)

print("\n响应接收完成！")