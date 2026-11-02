"""1.7 流式与事件（astream / astream_events）

【跑这个文件能看到什么】
Demo 1  astream 和 astream_events 的本质区别
Demo 2  事件的 7 个字段，以及 run_id / parent_ids 怎么还原调用树
Demo 3  ★ 只取 token 流：过滤 on_chat_model_stream
Demo 4  工具事件：on_tool_start / on_tool_end（离线）
Demo 5  ★ 完整链路：模型 → 工具 → 模型，全程用事件流观察
Demo 6  ★ 生产封装：把事件流转成 SSE 格式（对应简历的 SSE 流式输出）
Demo 7  六个必踩的坑

【对应手册】Part 1 · 1.7 流式与事件
【对应简历】"通过 astream_events 捕获每个节点的 Token 流与工具调用状态"

【怎么跑】
    cd studyLangChain_LangGraph/mini-project

    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_07_streaming_events.py
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_07_streaming_events.py --offline
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_07_streaming_events.py 5

【一句话结论】
    astream       → 只给你"文本片段"，够做打字机效果
    astream_events → 给你"每一步发生了什么"，够做完整的进度展示
"""

import asyncio
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


# ============================================================
# 一、加载配置
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


def show_title(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ============================================================
# 二、工具定义
# ============================================================

class LineQuery(BaseModel):
    line: str = Field(description="产线编号，例如 3号线")
    date: str = Field(description="生产日期，格式 YYYY-MM-DD")


class BatchQuery(BaseModel):
    batch_id: str = Field(description="批次号，例如 B002")


@tool("query_workorder", args_schema=LineQuery)
def query_workorder(line: str, date: str) -> str:
    """查询指定产线在某天的工单记录，返回批次数量和异常批次列表。"""
    if (line, date) != ("3号线", "2026-10-24"):
        return f"{line} {date} 没有记录"
    return "3号线 2026-10-24 共 5 个批次，3 个异常：B002, B003, B005"


@tool("query_quality", args_schema=BatchQuery)
def query_quality(batch_id: str) -> str:
    """查询指定批次的质检记录，返回不良项和检测参数。"""
    if batch_id != "B002":
        return f"批次 {batch_id} 没有质检记录"
    return "B002: 焊缝气孔，回流焊峰值温度 228℃（标准 235-245℃）"


TOOLS = [query_workorder, query_quality]
TOOL_MAP = {t.name: t for t in TOOLS}


# ============================================================
# Demo 1 · astream vs astream_events
# ============================================================

async def _demo1() -> None:
    question = "用一句话说明什么是回流焊。"

    print("① astream：每次给你一个 AIMessageChunk（只有文本片段）")
    chunk_count = 0 # 记录 chunk 数量
    first_text_index = None # 记录第一个有文本的 chunk 序号
    async for chunk in llm.astream(question):
        chunk_count += 1
        if chunk.text and first_text_index is None:
            first_text_index = chunk_count
        print(chunk.text, end="", flush=True)#流式输出文本
    print()
    print(f"   共 {chunk_count} 个 chunk，第一个有文本的是第 {first_text_index} 个")
    print("   ← 注意：前面几个 chunk 的 text 是空的")
    print("     因为这个模型在走思考模式，先吐 reasoning chunk，再吐正文")

    print("\n② astream_events：给你'每一步发生了什么'")
    event_types: list[str] = []
    async for event in llm.astream_events(question, version="v2"):
        event_types.append(event["event"])

    # print("event_types:",event_types,"\n")
    print("   事件类型统计：")
    for name, count in Counter(event_types).items():
        print(f"     {name:24} {count} 次")
    print(f"   总计 {len(event_types)} 个事件")

    print("\n【两者对比】")
    print("  astream         → 只关心文本，够做打字机效果")
    print("  astream_events  → 关心全过程：模型开始/结束、每个 token、工具调用")
    print("")
    print("  做聊天界面：astream 就够")
    print("  做'正在查询工单...'这种进度提示：必须 astream_events")


async def demo1_stream_vs_events() -> None:
    show_title("Demo 1 · astream vs astream_events")
    await _demo1()


# ============================================================
# Demo 2 · 事件的 7 个字段
# ============================================================

async def _demo2() -> None:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是质量助手，回答 20 字内。"),
        ("human", "{q}"),
    ])
    chain = prompt | llm

    print("① 一个完整的事件长这样（on_chat_model_end）")
    async for event in chain.astream_events({"q": "什么是虚焊？"}, version="v2"):
        if event["event"] == "on_chat_model_end":
            print(f"   event      = {event['event']!r}")
            print(f"   name       = {event['name']!r}")
            print("   data       = {'input': ..., 'output': AIMessage(...)}")
            print(f"   run_id     = {event['run_id'][:24]}...")
            print(f"   parent_ids = {[p[:16] + '...' for p in event['parent_ids']]}")
            print(f"   tags       = {event['tags']}")
            print(f"   metadata   = {list(event['metadata'].keys())}")
            break

    print("\n② 七个字段各自的作用")
    print("   event      → 事件类型，你要靠它过滤")
    print("   name       → 产生事件的对象名（RunnableSequence / ChatOpenAI / 工具名）")
    print("   data       → 负载。start 是 input，end 是 output，stream 是 chunk")
    print("   run_id     → 本次运行的唯一 id，用来配对 start 和 end")
    print("   parent_ids → 父级 run_id 列表，用来还原调用树")
    print("   tags       → 你手动打的标签（bind(tags=[...]) 传的）")
    print("   metadata   → 元信息（ls_model_name、ls_provider 等）")

    print("\n③ 用 run_id / parent_ids 还原调用树")
    print("   实测一条链的事件关系：")
    tree: dict[str, list[str]] = {}
    async for event in chain.astream_events({"q": "什么是虚焊？"}, version="v2"):
        if event["event"].endswith("_start"):
            depth = len(event["parent_ids"])
            indent = "   " + "  " * depth
            print(f"{indent}└─ [{event['event']}] {event['name']}")
            tree[event["run_id"]] = event["parent_ids"]

    print("\n   ← 缩进层级就是 parent_ids 的长度")
    print("     这条链只有两层：RunnableSequence → ChatOpenAI")
    print("     复杂 Agent 里会看到 5-6 层嵌套，靠这个能定位是哪一步出的问题")


async def demo2_event_fields() -> None:
    show_title("Demo 2 · 事件的 7 个字段")
    await _demo2()


# ============================================================
# Demo 3 · 只取 token 流
# ============================================================

async def _demo3() -> None:
    print("① 不过滤：事件太多，没法直接用")
    total = 0
    async for _ in llm.astream_events("说三个字", version="v2"):
        total += 1
    print(f"   一个很短的回答，产生了 {total} 个事件")
    print("   ← 26 个 token 的回答，事件数接近 60 个")

    print("\n② 过滤 on_chat_model_stream，只取 token")
    print("   实时输出：", end="", flush=True)
    token_count = 0
    async for event in llm.astream_events(  "用两句话说明什么是回流焊。",  version="v2", ):
        if event["event"] != "on_chat_model_stream":
            continue
        chunk = event["data"]["chunk"]
        # 关键：必须判空。思考模式下前面会有一堆 text 为空的 chunk
        if not chunk.text: # 如果 chunk 的 text 为空，跳过
            continue
        token_count += 1
        print(chunk.text, end="", flush=True)# 流式输出文本
    print()
    print(f"   实际有内容的 chunk = {token_count} 个")

    print("\n【关键点】为什么要判空")
    print("  这个模型有思考模式，流式返回时会先吐 reasoning 的 chunk，")
    print("  这些 chunk 的 .text 是空字符串。")
    print("  不判空的话，前端会收到一堆空消息，看起来像卡住了。")

    print("\n【三种过滤写法，从粗到细】")
    print("  只要文本：event['event'] == 'on_chat_model_stream'")
    print("  只要最终回答：再加 name 判断（多模型场景）")
    print("  只要某个节点的：用 tags 或 metadata 打标后过滤")


async def demo3_token_stream() -> None:
    show_title("Demo 3 · 只取 token 流")
    await _demo3()


# ============================================================
# Demo 4 · 工具事件（离线）
# ============================================================

async def _demo4() -> None:
    print("① 工具执行也会发事件")
    async for event in query_workorder.astream_events( {"line": "3号线", "date": "2026-10-24"},  version="v2", ):
        print(f" 1111  [{event['event']}] name={event['name']}") # 打印事件类型和名称  [on_tool_start] name=query_workorder
        if event["event"] == "on_tool_start":
            print(f" 22222     data['input'] = {event['data']['input']}") #如果是工具调用事件开始，打印input内容：{'line': '3号线', 'date': '2026-10-24'}
        elif event["event"] == "on_tool_end":
            output = event["data"].get("output")
            print(f" 3333      data['output'] = {output!r}")#如果类型为输出，打印output内容： '3号线 2026-10-24 共 5 个批次，3 个异常：B002, B003, B005'
            print(f" 4444      output 类型    = {type(output).__name__}")#output类型为 str

    print("\n② 工具事件的用途")
    print("   on_tool_start → 前端显示'正在查询工单...'")
    print("   on_tool_end   → 显示'查询完成'，或者把结果折叠展示")
    print("")
    print("   没有这两个事件，用户只能干等 —— 一个查询要 2 秒，")
    print("   界面上什么都不动，用户以为卡死了。")

    print("\n③ 工具执行失败时")
    @tool("bad_tool")
    def bad_tool(x: str) -> str:
        """故意抛错的工具"""
        raise ValueError(f"参数 {x} 非法")

    try:
        async for event in bad_tool.astream_events({"x": "test"}, version="v2"):
            print(f"   [{event['event']}]")# [on_tool_start]
    except Exception as e:
        print(f"   抛出了 {type(e).__name__}: {e}")# [on_tool_error]
        print("   ← 注意顺序：先发 on_tool_error 事件，再把异常抛出来")
        print("     所以前端能收到'工具失败'的信号，")
        print("     但你的执行器仍然必须 try/except，")
        print("     把失败转成 ToolMessage 回填给模型，否则整个 Agent 就断了")


async def demo4_tool_events() -> None:
    show_title("Demo 4 · 工具事件（离线）")
    await _demo4()


# ============================================================
# Demo 5 · 完整链路：模型 → 工具 → 模型
#
# 这是阶段 3「手写工具循环」的雏形。
# 用事件流把每一步都打出来，你能看清整个流程。
# ============================================================

async def _demo5() -> None:
    bound = llm.bind_tools(TOOLS) # 绑定工具
    messages: list = [
        SystemMessage(
            content="你是质量助手。需要数据时必须调用工具，不要猜测。"
        ),
        HumanMessage(
            content="3号线 2026-10-24 的不良原因是什么？请先查工单，再查异常批次的质检记录。"
        ),
    ]

    MAX_ROUNDS = 5 # 最大轮数
    round_no = 0

    while round_no < MAX_ROUNDS:
        round_no += 19
        print()
        print("=" * 72)
        print(f"第 {round_no} 轮")
        print("=" * 72)

        ai_message = None
        async for event in bound.astream_events(messages, version="v2"):
            if event["event"] == "on_chat_model_stream":
                text = event["data"]["chunk"].text
                if text:
                    print(text, end="", flush=True)
            elif event["event"] == "on_chat_model_end":
                ai_message = event["data"]["output"]
        print()

        if ai_message is None:
            print("[中断] 没有拿到模型输出")
            break

        # 模型不再请求工具 → 说明它给出最终答案了，循环结束
        if not ai_message.tool_calls:
            print("[结束] 模型不再请求工具，这就是最终答案")
            break

        # ---------------- 执行工具 ----------------
        print(f"模型请求了 {len(ai_message.tool_calls)} 个工具调用：")
        for call in ai_message.tool_calls:
            print(f"  - {call['name']}({call['args']})")

        messages.append(ai_message)
        for call in ai_message.tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]

            tool_obj = TOOL_MAP.get(tool_name)
            if tool_obj is None:
                result = f"[错误] 工具 {tool_name} 不存在"
            else:
                try:
                    result = tool_obj.invoke(tool_args)
                except Exception as e:
                    result = f"[执行失败] {type(e).__name__}: {e}"

            print(f"  → {tool_name} 结果：{result}")
            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call["id"],
                    name=tool_name,
                )
            )

        if round_no >= MAX_ROUNDS:
            print(f"\n[强制停止] 已达最大轮数 {MAX_ROUNDS}，防止死循环")

    print("\n【这条链路就是完整的 ReAct 循环】")
    print("  while True:")
    print("      模型 → 有 tool_calls 就执行 → 结果回填 → 再问模型")
    print("      没有 tool_calls 就退出")
    print("      加上最大轮数上限防死循环")
    print("")
    print("  你刚才看到的第 2 轮很关键：")
    print("  模型查完工单后，发现 3 个异常批次，又自己决定去查这 3 个批次的质检。")
    print("  这不是你教的，是它根据 tool_calls 自己往下走的 ——")
    print("  所以循环必须能处理【任意轮数】，不能写死两轮。")
    print("")
    print("  create_agent 内部干的就是这件事，只是它把循环、重试、")
    print("  终止条件都封装好了。面试被问'Agent 循环怎么实现'，说出这段就够了。")


async def demo5_full_loop() -> None:
    show_title("Demo 5 · 完整链路：模型 → 工具 → 模型")
    await _demo5()


# ============================================================
# Demo 6 · 生产封装：转成 SSE
#
# 这一段直接对应简历里的"SSE 流式输出与游标补拉"
# ============================================================

async def sse_generator(question: str, max_rounds: int = 5) -> AsyncIterator[str]:
    """
    把 Agent 的执行过程转成 SSE 格式的字符串流。

    SSE 格式（每个事件三行，最后必须空行）：
        event: token
        data: {"text": "回"}

    前端用 EventSource 接，按 event 名分别处理。

    注意：内部是 while 循环，因为模型可能多轮请求工具。
    """
    bound = llm.bind_tools(TOOLS)#绑定工具  它只是把工具定义/schema 提供给模型。

    #初始化消息上下文
    messages: list = [
        SystemMessage(
            content="你是质量助手。需要数据时必须调用工具，不要猜测。"
        ),
        HumanMessage(content=question),
    ]

    #Agent 多轮循环
    for _ in range(max_rounds):
        #先清空消息内容
        ai_message = None

        # ---------------- 一轮模型调用：token 流 ----------------
        async for event in bound.astream_events(messages, version="v2"):#它会把模型运行过程中的事件不断交给你。
            event_name = event["event"]#事件名称

            #on_chat_model_stream  on_chat_model_end
            if event_name == "on_chat_model_stream":
                text = event["data"]["chunk"].text #提取chunks中的文本
                if text:
                    payload = json.dumps({"text": text}, ensure_ascii=False)
                    """一个事件
                    event: token
                    data: {"text": "根据"}
                    <空行>
                    """
                    yield f"event: token\ndata: {payload}\n\n" #生成json格式后   直接一段一段返回内容

            elif event_name == "on_chat_model_end":
                ai_message = event["data"]["output"] #模型最终输出，是给Agent的内容

        if ai_message is None:
            yield f"event: error\ndata: {json.dumps({'msg': '模型无输出'}, ensure_ascii=False)}\n\n"
            return

        # 模型不再请求工具 → 最终答案已经吐完，退出Agent循环
        if not ai_message.tool_calls:
            break

        # ---------------- 执行工具，每个发一对事件 ----------------
        messages.append(ai_message)

        for call in ai_message.tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]

            start_payload = json.dumps(
                {"tool": tool_name, "args": tool_args}, ensure_ascii=False
            )
            yield f"event: tool_start\ndata: {start_payload}\n\n"

            tool_obj = TOOL_MAP.get(tool_name)
            if tool_obj is None:
                result = f"[错误] 工具 {tool_name} 不存在"
            else:
                try:
                    result = tool_obj.invoke(tool_args)
                except Exception as e:
                    result = f"[执行失败] {type(e).__name__}: {e}"

            end_payload = json.dumps(
                {"tool": tool_name, "result": str(result)}, ensure_ascii=False
            )
            yield f"event: tool_end\ndata: {end_payload}\n\n"

            messages.append(
                #把工具结果重新放回 LLM 上下文。
                ToolMessage(content=str(result), tool_call_id=call["id"], name=tool_name)
            )

    yield "event: done\ndata: {}\n\n"


async def _demo6() -> None:
    print("① 原始 SSE 流（前端收到的就是这些字符串）")
    print("-" * 72)

    all_chunks: list[str] = []
    async for sse_chunk in sse_generator("3号线 2026-10-24 的不良原因是什么？"):
        all_chunks.append(sse_chunk)#将所有see_chunk添加到all_chunks列表中
        # 只打印前 6 条，避免刷屏
        if len(all_chunks) <= 6:
            print(sse_chunk, end="")
    print("-" * 72)
    print(f"共 {len(all_chunks)} 条 SSE 消息")

    print("\n② 按事件名分类统计")
    counts: Counter = Counter()
    for sse_chunk in all_chunks:
        if sse_chunk.startswith("event: "):
            event_name = sse_chunk.split("\n")[0][7:]
            counts[event_name] += 1
    for name, count in counts.items():
        print(f"   {name:12} {count} 条")

    print("\n   ← token 很多条、tool_start/tool_end 成对、最后一条 done")
    print("     前端就是靠这个顺序渲染出'思考中 → 打字 → 查数据 → 继续打字'的效果")

    print("\n③ 前端怎么用")
    print("   const es = new EventSource('/api/analyze?q=...');")
    print("   es.addEventListener('token', e => appendText(JSON.parse(e.data).text));")
    print("   es.addEventListener('tool_start', e => showSpinner(JSON.parse(e.data).tool));")
    print("   es.addEventListener('tool_end', e => hideSpinner());")
    print("   es.addEventListener('done', () => es.close());")

    print("\n【为什么简历里要写这个】")
    print("  Agent 一次分析要 10-30 秒。没有流式，用户盯着转圈等半分钟。")
    print("  有了 SSE，用户能看到：")
    print("    '正在思考...' → 文字一个个出现 → '正在查询工单 B002...' → 继续输出")
    print("  体验差距是决定性的，不是锦上添花。")

    print("\n【'游标补拉'是什么】")
    print("  SSE 连接断了（网络抖动、切后台），前面的内容就丢了。")
    print("  做法：每个事件带一个递增的 seq，前端记录最后收到的 seq；")
    print("  重连时带上 seq，后端从断点继续推。")
    print("  这就需要后端把事件【持久化】（存 Redis / MySQL），不是只靠内存流。")
    print("")
    print("  这一层已经超出 LangChain 的范围，属于工程实现。")


async def demo6_sse() -> None:
    show_title("Demo 6 · 生产封装：转成 SSE 格式")
    await _demo6()


# ============================================================
# Demo 7 · 六个必踩的坑（离线）
# ============================================================

async def demo7_pitfalls() -> None:
    show_title("Demo 7 · 六个必踩的坑（离线）")

    print("① 忘了 version='v2'")
    print("   astream_events(input)                  ← 旧版，事件结构不同")
    print("   astream_events(input, version='v2')    ← 必须写")
    print("   不写会拿到 v1 的事件格式，字段名对不上。")

    print("\n② 用 for 而不是 async for")
    print("   for event in chain.astream_events(...)      ← TypeError")
    print("   async for event in chain.astream_events(...) ← 正确")
    print("   astream_events 是异步生成器，必须在 async 函数里用。")

    print("\n③ 不判 chunk.text 是否为空")
    print("   思考模式下前面会有一批空 text 的 chunk。")
    print("   不判空 → 前端收到一堆空消息，看起来像卡住。")

    print("\n④ 事件太多，不做过滤")
    print("   一个 26 token 的回答产生约 60 个事件。")
    print("   全量推给前端 → 网络开销大、前端处理不过来。")
    print("   只推 on_chat_model_stream 和工具事件就够了。")

    print("\n⑤ 以为 astream_events 会自动执行工具")
    print("   bind_tools 只是把工具定义发给模型。")
    print("   模型返回 tool_calls 后，【执行仍然是你的代码做的】。")
    print("   astream_events 只是把这个过程记录下来给你看。")

    print("\n⑥ 用 astream 又想拿工具调用信息")
    print("   astream 只给 AIMessageChunk，chunk 上虽然有 tool_call_chunks，")
    print("   但要自己拼、自己解析，很麻烦。")
    print("   要工具信息就用 astream_events，别硬用 astream。")

    print("\n【选型口诀】")
    print("  只要打字机效果          → astream")
    print("  要显示'正在调工具'      → astream_events")
    print("  要接 SSE 给前端         → astream_events + 自己转格式")
    print("  要做 LangGraph 节点级流 → stream_mode（LangGraph 才有的）")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], Awaitable[None]], bool]] = [
    # ("1", "astream vs astream_events", demo1_stream_vs_events, True),
    # ("2", "事件的 7 个字段", demo2_event_fields, True),
    # ("3", "只取 token 流", demo3_token_stream, True),
    # ("4", "工具事件", demo4_tool_events, False),
    # ("5", "完整链路 模型→工具→模型", demo5_full_loop, True),
    # ("6", "转成 SSE 格式", demo6_sse, True),
    ("7", "六个必踩的坑", demo7_pitfalls, False),
]


async def _run_selected(picked: list[str], offline_only: bool) -> None:
    """所有 Demo 共用同一个事件循环。

    为什么不能每个 Demo 单独 asyncio.run：
    httpx 的异步连接池会在第一个事件循环关闭后失效，
    第二次 asyncio.run 再复用它就会报 'Event loop is closed'。
    """
    for key, title, func, needs_model in DEMOS:
        if picked and key not in picked:
            continue
        if offline_only and needs_model:
            continue
        await func()


def main() -> None:
    args = sys.argv[1:]
    offline_only = "--offline" in args
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print(f"1.7 流式与事件 | 模型 = {MODEL_CODE}")
    if offline_only:
        print("模式：--offline（只跑 Demo 4/7）")
    print("=" * 72)

    asyncio.run(_run_selected(picked, offline_only))

    print()
    print("=" * 72)
    print("全部完成")
    print("=" * 72)


if __name__ == "__main__":
    main()
