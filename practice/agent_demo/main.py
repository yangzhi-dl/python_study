"""不良品根因追溯 Agent —— 最小可运行版本

运行前准备：
1. 把 .env.example 复制成 .env，填上你的 API Key
2. 装依赖：pip install langchain langchain-openai python-dotenv
3. 跑：python main.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from tools import ALL_TOOLS


# ============================================================
# 1. 加载配置
#    用 Path(__file__).parent 而不是相对路径 —— 换目录运行也不会失效
# ============================================================

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

if not API_KEY:
    raise SystemExit(
        "没有读到 API_KEY。\n"
        "请把 .env.example 复制成 .env，并填入你的 API Key。"
    )


# ============================================================
# 2. 创建模型
#    base_url 是给国内中转/兼容接口用的，用官方 OpenAI 可以留空
#    temperature=0 让输出更稳定 —— 分析类任务不需要"创造力"
# ============================================================

llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL or None,
    temperature=0,
)


# ============================================================
# 3. 系统提示词
#
#    这里定义了 Agent 的"工作流程"和"输出要求"。
#    这是整个 Agent 里最需要反复调的部分 ——
#    模型不按你想的顺序查、不给证据、乱猜，都靠这里约束。
# ============================================================

SYSTEM_PROMPT = """你是不良品根因分析助手。

分析问题时，按这个顺序：
1. 先用 query_workorder 查工单，找出异常批次
2. 再用 query_quality 查这些异常批次的质检记录
3. 如果多个批次有相同的参数异常，用 query_bom 查物料，排查来料问题

结论要求：
- 必须基于查询到的数据，不要猜测
- 每个结论都要标注证据来源（哪条工单、哪条质检记录）
- 如果数据不足以判断，明确说"还需要补充哪些信息"
"""


# ============================================================
# 4. 创建 Agent
#
#    create_agent 帮你做好了这些事：
#    - 把 tools 转成 JSON Schema 交给模型
#    - 模型返回 tool_calls 时自动执行工具
#    - 把工具结果包成 ToolMessage 塞回消息列表
#    - 循环，直到模型不再调工具
#
#    这就是 ReAct 循环，只是被封装起来了。
# ============================================================

agent = create_agent(
    model=llm,
    tools=ALL_TOOLS,
    system_prompt=SYSTEM_PROMPT,
)


# ============================================================
# 5. 入口
# ============================================================

def main() -> None:
    question = "3号线 2026-10-24 的不良原因是什么？"

    print(f"问题: {question}")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{"role": "user", "content": question}]
    })

    # result["messages"] 是完整的消息列表：
    # [用户消息, AI消息(带tool_calls), 工具结果, AI消息(带tool_calls), ..., 最终AI消息]
    # 打印全部，你能看到 Agent 的完整思考过程
    print("\n--- 完整消息链 ---")
    for i, msg in enumerate(result["messages"]):
        msg_type = type(msg).__name__
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        print(f"[{i}] {msg_type}: {content[:200]}")

        # 如果有工具调用，单独打印出来
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                print(f"     → 调用工具: {tc['name']}, 参数: {tc['args']}")

    print("\n" + "=" * 60)
    print("--- 最终结论 ---")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
