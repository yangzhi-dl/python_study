"""进度提示 Demo：用 astream_events 做"正在查询工单..."效果

【跑这个能看到什么】
模拟一个聊天界面，用户提问后依次出现：
  ⏳ 正在思考...  →  文字逐个出现  →  🔧 正在查询 query_workorder ...  →  ✅ 查询完成  →  继续输出

【怎么跑】
    cd studyLangChain_LangGraph/mini-project
    .venv/Scripts/python.exe ../../playground/tool_progress_demo.py
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


# ============================================================
# 一、环境
# ============================================================

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL: str = os.getenv("BASE_URL", "")
MODEL_CODE: str = os.getenv("MODEL_CODE", "")

if not API_KEY:
    raise SystemExit(f"没有读到 DASHSCOPE_API_KEY，检查 {ENV_PATH}")
if not MODEL_CODE:
    raise SystemExit(f"没有读到 MODEL_CODE，检查 {ENV_PATH}")


llm_kwargs: dict = {
    "model": MODEL_CODE,
    "api_key": API_KEY,
    "temperature": 0,
}
if BASE_URL:
    llm_kwargs["base_url"] = BASE_URL

llm = ChatOpenAI(**llm_kwargs)




# ============================================================
# 二、假数据 + 工具
# ============================================================

FAKE_WORKORDERS: dict = {
    ("3号线", "2026-10-24"): [
        {"batch": "B001", "status": "正常"},
        {"batch": "B002", "status": "异常", "defect": "焊缝气孔"},
        {"batch": "B003", "status": "异常", "defect": "虚焊"},
        {"batch": "B004", "status": "正常"},
        {"batch": "B005", "status": "异常", "defect": "气孔"},
    ],
}


class WorkorderQuery(BaseModel):
    line: str = Field(description="产线编号，例如 3号线")
    date: str = Field(description="日期，格式 YYYY-MM-DD")


@tool("query_workorder", args_schema=WorkorderQuery)
def query_workorder(line: str, date: str) -> str:
    """查询指定产线在某天的工单记录，返回批次数量和异常批次号。"""
    records = FAKE_WORKORDERS.get((line, date), [])
    if not records:
        return f"{line} {date} 没有记录"

    # 故意睡 1.5 秒，模拟真实数据库查询耗时
    time.sleep(1.5)

    abnormal = [r for r in records if r["status"] == "异常"]
    batches = ", ".join(r["batch"] for r in abnormal)
    return f"{line} {date} 共 {len(records)} 个批次，{len(abnormal)} 个异常：{batches}"


TOOLS: list = [query_workorder]
TOOL_MAP: dict[str, Any] = {t.name: t for t in TOOLS}


# ============================================================
# 三、核心：带进度提示的调用
# ============================================================

async def stream_model(bound, messages: list) -> AIMessage:
    """跑一次模型，边流 token 边报'正在思考'。

    关键：on_chat_model_stream 只给文本片段，
          拿不到 tool_calls；tool_calls 要从 on_chat_model_end 的 output 里取。
    """
    ai_msg: AIMessage | None = None

    async for event in bound.astream_events(messages, version="v2"):
        kind: str = event["event"]

        # ---- 模型开始推理 ----
        if kind == "on_chat_model_start":
            print("[UI] ⏳ 正在思考...", flush=True)

        # ---- 每吐一个 token ----
        elif kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            text: str = chunk.text
            if text:                       # 思考模式下前面很多 chunk 是空的
                print(text, end="", flush=True)

        # ---- 模型这一轮结束，这里才拿得到完整消息（含 tool_calls）----
        elif kind == "on_chat_model_end":
            ai_msg = event["data"]["output"]

    if ai_msg is not None and ai_msg.text:
        print()                            # 收个尾换行

    return ai_msg


async def run_one_tool(call: dict) -> str:
    """执行一个工具，中间报'正在查询'和'查询完成'。"""
    name: str = call["name"]
    args: dict = call["args"]
    tool_obj = TOOL_MAP[name]

    result_text: str = ""
    start: float = time.time()

    async for event in tool_obj.astream_events(args, version="v2"):
        kind: str = event["event"]

        # ---- 工具开始执行 ----
        if kind == "on_tool_start":
            print(f"[UI] 🔧 正在查询 {name} {args} ...", flush=True)

        # ---- 工具执行完成 ----
        elif kind == "on_tool_end":
            output = event["data"].get("output")
            result_text = getattr(output, "content", str(output))
            cost: float = time.time() - start
            print(f"[UI] ✅ 查询完成，用时 {cost:.2f}s", flush=True)

    return result_text


async def chat(question: str) -> None:
    """完整的一轮对话：模型 → 工具 → 模型，最多 3 轮。"""
    print(f"\n用户：{question}")

    messages: list = [HumanMessage(content=question)]
    bound = llm.bind_tools(TOOLS)

    for round_no in range(1, 4):
        print(f"\n--- 第 {round_no} 轮 ---")

        ai_msg = await stream_model(bound, messages)

        # 没有 tool_calls = 模型认为可以直接回答，结束
        if not ai_msg.tool_calls:
            print("[UI] 回答完毕")
            return

        # 有 tool_calls = 模型要查数据，执行后把结果塞回消息列表
        messages.append(ai_msg)

        for call in ai_msg.tool_calls:
            result: str = await run_one_tool(call)
            messages.append(
                ToolMessage(content=result, tool_call_id=call["id"])
            )

    print("[UI] 超过 3 轮，强制结束")


# ============================================================
# 四、入口
# ============================================================

async def main() -> None:
    await chat("3号线 2026-10-24 有几个异常批次？分别是哪几个？")


if __name__ == "__main__":
    asyncio.run(main())
