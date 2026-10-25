"""1.1 模型调用 —— 四种调用方式对比

【跑这个文件能看到什么】
① invoke   同步调用，等全部生成完才返回 → 首字延迟 = 总耗时
② stream   流式调用，逐 token 返回      → 首字延迟低（打字机效果）
③ batch    批量调用，多个输入并发        → 总耗时接近单个
④ ainvoke  异步调用，不阻塞事件循环      → Web 服务必须用

【对应手册】Part 1 · 1.1 模型调用

【怎么跑】
    cd studyLangChain_LangGraph/mini-project
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_01_model_call_modes.py

【跑之前确认】
    .env 在 mini-project/ 下，含 DASHSCOPE_API_KEY / BASE_URL / MODEL_CODE
"""

import asyncio
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


# ============================================================
# 一、加载配置
#
# 文件在 mini-project/LangChainLangGraph_workbuddy/ 下，
# 所以 .parent.parent 才是 mini-project/，.env 在那里。
# ============================================================

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL: str = os.getenv("BASE_URL", "")
MODEL_CODE: str = os.getenv("MODEL_CODE", "")

if not API_KEY:
    raise SystemExit(
        "没有读到 DASHSCOPE_API_KEY。\n"
        f"检查这个文件是否存在且格式正确：{ENV_PATH}"
    )

if not MODEL_CODE:
    raise SystemExit(f"没有读到 MODEL_CODE，检查 {ENV_PATH}")


# ============================================================
# 二、创建模型
#
# 注意点：
# 1. temperature=0 → 分析类任务要稳定，不要"创造力"
# 2. 用通义千问必须传 base_url（OpenAI 兼容接口地址）
# 3. 三个参数全部从 .env 读，换模型只改 .env
# ============================================================

llm_kwargs: dict = {
    "model": MODEL_CODE,
    "api_key": API_KEY,
    "temperature": 0,
}
if BASE_URL:
    llm_kwargs["base_url"] = BASE_URL

llm = ChatOpenAI(**llm_kwargs) #传入解构llm_kwargs参数

PROMPT = "用一句话解释什么是 AI Agent"


# ============================================================
# 三、四种调用方式
# ============================================================


def demo_invoke() -> None:
    """① invoke —— 同步，一次拿完"""
    print("=" * 60)
    print("① invoke —— 同步调用")
    print("=" * 60)

    start = time.perf_counter()
    result = llm.invoke(PROMPT) #invoke 同步调用
    elapsed = time.perf_counter() - start

    print(f"返回的内容为：{result}")
    print(f"结果: {result.content}")
    print(f"耗时: {elapsed:.2f}s")
    print("→ 注意：必须等全部生成完，用户才能看到第一个字")
    print("→ result 是 AIMessage 对象，.content 才是文本\n")


def demo_stream() -> None:
    """② stream —— 流式，逐 token 返回"""
    print("=" * 60)
    print("② stream —— 流式调用")
    print("=" * 60)

    start = time.perf_counter()
    first_token_time: float | None = None  #相当于定义了一个变量，设置为float

    print("结果: ", end="")

    #打印机输出
    for chunk in llm.stream(PROMPT):
        # 记录第一个 token 到达的时间
        if first_token_time is None:
            first_token_time = time.perf_counter() - start
        print(chunk.content, end="", flush=True)

    total = time.perf_counter() - start

    print(f"\n首字延迟: {first_token_time:.2f}s")
    print(f"总耗时:   {total:.2f}s")
    print("→ 注意：总耗时和 invoke 差不多，但首字延迟低得多")
    print("→ 这就是打字机效果的原理\n")


def demo_batch() -> None:
    """③ batch —— 批量，并发处理"""
    print("=" * 60)
    print("③ batch —— 批量调用")
    print("=" * 60)

    questions = [
        "用一句话解释什么是 MES",
        "用一句话解释什么是 QMS",
        "用一句话解释什么是 SPC",
    ]

    start = time.perf_counter()
    results = llm.batch(questions) #批量处理问题
    elapsed = time.perf_counter() - start

    for q, r in zip(questions, results):
        print(f"Q: {q}")
        print(f"A: {r.content}\n")

    print(f"3 个问题总耗时: {elapsed:.2f}s")
    print("→ 注意：不是串行 3 倍时间，是并发执行\n")


async def demo_ainvoke() -> None:
    """④ ainvoke —— 异步"""
    print("=" * 60)
    print("④ ainvoke —— 异步调用")
    print("=" * 60)

    start = time.perf_counter()
    result = await llm.ainvoke("用一句话解释什么是 LangGraph") #异步调用 **Web 服务必须用**
    elapsed = time.perf_counter() - start

    print(f"结果: {result.content}")
    print(f"耗时: {elapsed:.2f}s")
    print("→ 注意：结果和 invoke 一样，区别在于 await 期间不阻塞事件循环")
    print("→ FastAPI 里必须用 ainvoke，否则所有请求排队\n")


# ============================================================
# 四、入口
# ============================================================


def main() -> None:
    print(f"\n模型: {MODEL_CODE}")
    print(f"地址: {BASE_URL or '(OpenAI 官方)'}\n")

    demo_invoke()
    demo_stream()
    demo_batch()
    asyncio.run(demo_ainvoke())

    print("=" * 60)
    print("对比总结")
    print("=" * 60)
    print("invoke  : 简单，但首字延迟 = 总耗时")
    print("stream  : 首字延迟低，适合打字机效果")
    print("batch   : 多输入并发，省时间")
    print("ainvoke : 异步，Web 服务必须用")
    print()
    print("注意点（手册 1.1）：")
    print("  1. temperature=0 → 分析类任务要稳定")
    print("  2. 通义/DeepSeek 等必须配 base_url")
    print("  3. Web 服务用 ainvoke，不要用 invoke")
    print("  4. 文本在 result.content，不是 result 本身")


if __name__ == "__main__":
    main()
