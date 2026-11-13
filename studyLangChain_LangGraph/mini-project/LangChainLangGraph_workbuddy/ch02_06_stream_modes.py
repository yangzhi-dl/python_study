"""2.6 流式：五种 stream_mode

【跑这个文件能看到什么】
Demo 1  values：每个 super-step 后的完整 State
Demo 2  updates：每个节点的增量更新（最常用）
Demo 3  ★ messages：LLM 的 token 流，带节点名
Demo 4  custom：节点内部自己写的进度
Demo 5  debug：调试用的事件流
Demo 6  多模式组合
Demo 7  ★ 和 astream_events 怎么选

【对应手册】Part 2 · 2.10 流式
【面试高频】"LangGraph 的 stream_mode 有哪几种？"
          答得出五种 + 各自用途 + messages 模式的 metadata 里有什么，
          就是"用过"和"懂"的分界线。

【怎么跑】
    cd studyLangChain_LangGraph/mini-project
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_06_stream_modes.py
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_06_stream_modes.py --offline
"""

import os
import sys
from pathlib import Path
from typing import Annotated, Callable, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from graph_flow import draw_flow


# ============================================================
# 一、加载配置
# ============================================================

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH,override=True)

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
# 二、一个简单的三节点图（用于 values / updates / custom / debug）
# ============================================================

class StepState(TypedDict):
    steps: Annotated[list[str], lambda left, right: (left or []) + right]
    count: int


def node_a(state: StepState) -> dict:
    # get_stream_writer 拿到一个写入器，写的东西会从 custom 模式流出
    writer = get_stream_writer()
    writer({"progress": "节点 a：开始查工单", "percent": 10})
    return {"steps": ["a"], "count": state["count"] + 1}


def node_b(state: StepState) -> dict:
    writer = get_stream_writer()
    writer({"progress": "节点 b：开始查质检", "percent": 50})
    return {"steps": ["b"], "count": state["count"] + 1}


def node_c(state: StepState) -> dict:
    writer = get_stream_writer()
    writer({"progress": "节点 c：生成报告", "percent": 90})
    return {"steps": ["c"], "count": state["count"] + 1}


def build_step_graph():
    builder = StateGraph(StepState)
    builder.add_node("a", node_a)
    builder.add_node("b", node_b)
    builder.add_node("c", node_c)
    builder.add_edge(START, "a")
    builder.add_edge("a", "b")
    builder.add_edge("b", "c")
    builder.add_edge("c", END)
    return builder.compile()


def show_step_graph(title: str = "流程图（stream 的这张图）") -> None:
    """把 Demo 1/2/4/5/6 共用的这张三步图打印出来。"""
    draw_flow(
        build_step_graph(),
        node_notes={
            "START": "初始 State = {steps: [], count: 0}",
            "a": "写 progress 10%，steps 加 'a'",
            "b": "写 progress 50%，steps 加 'b'",
            "c": "写 progress 90%，steps 加 'c'",
            "END": "steps = ['a','b','c']，count = 3",
        },
        edge_notes={
            ("START", "a"): ["普通边：START → 第一个节点"],
            ("a", "b"): ["steps 有 reducer → 累加"],
            ("b", "c"): ["steps 累加"],
            ("c", "END"): ["普通边：最后一个节点 → END"],
        },
        title=title,
    )


# ============================================================
# Demo 1 · values
# ============================================================

def demo1_values() -> None:
    show_title("Demo 1 · stream_mode='values'（离线）")

    app = build_step_graph()

    show_step_graph("Demo 1 · 流程图（values 模式跑的就是这张图）")

    print("① 每执行完一个 super-step，吐出【完整 State】")
    print("   （第一条是初始 State）\n")

    for i, state in enumerate(app.stream({"steps": [], "count": 0}, stream_mode="values")):
        print(f"   [{i}] steps={state['steps']}  count={state['count']}")

    print("\n② 特点")
    print("   - 每次给全量 State，不用自己拼")
    print("   - 但数据量大：State 越大，每条消息越重")
    print("   - 适合：前端要'当前完整状态'，比如整页刷新")

    print("\n③ 对比 invoke")
    print("   invoke 只给最后一份，stream(values) 给每一份。")
    print("   想看'过程'就用 stream，只关心结果用 invoke。")


# ============================================================
# Demo 2 · updates
# ============================================================

def demo2_updates() -> None:
    show_title("Demo 2 · stream_mode='updates'（离线，最常用）")

    app = build_step_graph()
    show_step_graph("Demo 2 · 流程图（updates 模式）")


    print("① 每个节点执行完，吐出【这个节点改了什么】\n")

    for chunk in app.stream({"steps": [], "count": 0}, stream_mode="updates"):
        # chunk 的形状是 {节点名: {字段: 值}}
        for node_name, update in chunk.items():
            print(f"   节点 {node_name!r} 更新了 {update}")

    print("\n② 特点")
    print("   - 只给增量，数据量小")
    print("   - 带节点名，知道是哪一步产生的")
    print("   - 适合：日志、进度展示、审计")

    print("\n③ 这是最常用的模式")
    print("   '正在执行 execute 节点...' 这种提示就靠它。")
    print("   生产环境的审计日志也用它 —— 每一条都能对应到具体节点。")

    print("\n④ 注意形状")
    print("   chunk = {'节点名': {'字段': 新值}}")
    print("   不是 {'字段': 新值}。多一层节点名，所以要先 .items() 遍历。")


# ============================================================
# Demo 3 · messages（重点）
# ============================================================

class LineQuery(BaseModel):
    line: str = Field(description="产线编号，例如 3号线")
    date: str = Field(description="生产日期，格式 YYYY-MM-DD")


@tool("query_workorder", args_schema=LineQuery)
def query_workorder(line: str, date: str) -> str:
    """查询指定产线在某天的工单记录。"""
    if (line, date) != ("3号线", "2026-10-24"):
        return f"{line} {date} 没有记录"
    return "3号线 2026-10-24 共 5 个批次，3 个异常：B002, B003, B005"


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]


def demo3_messages() -> None:
    show_title("Demo 3 · stream_mode='messages'：token 流 + 节点名")

    llm_with_tools = llm.bind_tools([query_workorder])

    def agent_node(state: ChatState) -> dict:
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    builder = StateGraph(ChatState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode([query_workorder]))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 messages",
            "agent": "调模型，token 从这里流出来",
            "tools": "ToolNode 执行工具",
            "END": "没有 tool_calls 就结束",
        },
        title="Demo 3 · 流程图（messages 模式）",
    )

    print("① messages 模式吐的是 (chunk, metadata) 元组")
    print("   实时输出：\n   ", end="")

    token_count = 0
    metadata_sample = None

    for chunk, metadata in app.stream(
        {
            "messages": [
                SystemMessage(content="你是质量助手。"),
                HumanMessage(content="3号线 2026-10-24 有几个异常批次？"),
            ]
        },
        stream_mode="messages",
    ):
        # chunk 是 AIMessageChunk，要 .text 取文本
        if chunk.text:
            token_count += 1
            print(chunk.text, end="", flush=True)
        if metadata_sample is None:
            metadata_sample = metadata

    print()
    print(f"\n② 共收到 {token_count} 个有内容的 chunk")

    print("\n③ metadata 里有什么（这是 messages 模式的核心价值）")
    if metadata_sample:
        for key, value in metadata_sample.items():
            text = str(value)
            if len(text) > 60:
                text = text[:60] + "..."
            print(f"   {key:22} = {text}")

    print("\n④ 最关键的是 langgraph_node")
    print("   metadata['langgraph_node'] 告诉你这个 token 是哪个节点产生的。")
    print("   所以你能做到：")
    print("     if metadata['langgraph_node'] == 'agent': 显示在聊天气泡里")
    print("     if metadata['langgraph_node'] == 'summarize': 显示在报告区")
    print("")
    print("   这个能力 astream_events 也能做（靠 name），")
    print("   但 messages 模式直接给你，不用自己解析事件。")

    print("\n⑤ 按节点过滤 token 的写法")
    print("   for chunk, meta in app.stream(..., stream_mode='messages'):")
    print("       if meta['langgraph_node'] != 'agent':")
    print("           continue")
    print("       print(chunk.text, end='')")


# ============================================================
# Demo 4 · custom
# ============================================================

def demo4_custom() -> None:
    show_title("Demo 4 · stream_mode='custom'：节点自己写进度（离线）")

    app = build_step_graph()

    show_step_graph("Demo 4 · 流程图（custom 模式，进度从节点里写出来）")

    print("① 节点内部用 get_stream_writer() 写任意数据")
    print("   写的东西只从 custom 模式流出，不影响 State\n")

    for chunk in app.stream({"steps": [], "count": 0}, stream_mode="custom"):
        print(f"   {chunk}")

    print("\n② 特点")
    print("   - 想写什么写什么，不受 State schema 限制")
    print("   - 不进 State，不占 checkpointer 快照")
    print("   - 适合：精细进度条、'正在查询第 3/10 个批次'")

    print("\n③ 和 updates 的区别")
    print("   updates → 节点返回值，会进 State")
    print("   custom  → 节点里主动写的，只是通知，不进 State")
    print("")
    print("   所以'进度 30%'这种临时信息用 custom，")
    print("   别塞进 State —— 塞进去会被 checkpointer 存一堆没用的快照。")

    print("\n④ 坑：节点不是 async 时也能用")
    print("   get_stream_writer() 在同步和异步节点里都能调。")
    print("   但在【没有 stream 上下文】时调（比如直接 invoke），")
    print("   它会返回一个空操作函数，不会报错也不会输出。")


# ============================================================
# Demo 5 · debug
# ============================================================

def demo5_debug() -> None:
    show_title("Demo 5 · stream_mode='debug'：调试事件（离线）")

    app = build_step_graph()

    show_step_graph("Demo 5 · 流程图（debug 模式）")

    print("① debug 模式吐出所有内部事件\n")

    for i, chunk in enumerate(app.stream({"steps": [], "count": 0}, stream_mode="debug")):
        event_type = chunk.get("type")
        step = chunk.get("step")
        name = chunk.get("payload", {}).get("name", "-")
        print(f"   [{i}] step={step} type={event_type:14} name={name}")

    print("\n② 三种事件类型")
    print("   task        → 节点开始执行")
    print("   task_result → 节点执行完成，带返回值")
    print("   checkpoint  → 快照保存")

    print("\n③ 用途")
    print("   排查'节点到底执行了几次'、'返回值是什么'。")
    print("   比 print 干净，比 LangSmith 轻量。")
    print("")
    print("   但别在生产开着它 —— 输出量太大，日志会被淹没。")


# ============================================================
# Demo 6 · 多模式组合
# ============================================================

def demo6_combined() -> None:
    show_title("Demo 6 · 多模式组合（离线）")

    app = build_step_graph()

    show_step_graph("Demo 6 · 流程图（多模式组合）")

    print("① stream_mode 传列表，同时拿多种数据")
    print("   返回变成 (mode, chunk) 元组\n")

    for mode, chunk in app.stream(
        {"steps": [], "count": 0},
        stream_mode=["updates", "custom"],
    ):
        if mode == "custom":
            print(f"   [custom]  {chunk['progress']}")
        else:
            for node_name, update in chunk.items():
                print(f"   [updates] {node_name} → {update}")

    print("\n② 组合的价值")
    print("   updates 给'业务进展'，custom 给'精细进度'。")
    print("   前端可以同时渲染两层：")
    print("     顶部进度条 ← custom 的 percent")
    print("     中间日志流 ← updates 的节点名")
    print("")
    print("   一个 SSE 连接就能推两种信息，不用开两个接口。")

    print("\n③ 异步版")
    print("   async for mode, chunk in app.astream(input, stream_mode=['updates','custom']):")
    print("   Web 服务里用 astream，别用 stream（会阻塞事件循环）。")


# ============================================================
# Demo 7 · 和 astream_events 怎么选
# ============================================================

def demo7_choose_mode() -> None:
    show_title("Demo 7 · 和 astream_events 怎么选（离线）")

    print("① 两者的层级不同")
    print()
    print("   astream_events（LangChain 层，1.7 学的）")
    print("     - 看得到每一次 LLM 调用、每一次工具调用、每一层 Runnable")
    print("     - 事件有 run_id / parent_ids，能还原完整调用树")
    print("     - 信息最全，但最啰嗦")
    print()
    print("   stream_mode（LangGraph 层，本节）")
    print("     - 看得到【图层面】的进展：哪个节点跑了、State 怎么变")
    print("     - 更贴近业务语义")
    print("     - 五种模式各管一件事，按需选")

    print("\n② 场景对照表")
    print()
    print("   需求                              用什么")
    print("   --------------------------------  -----------------------")
    print("   聊天界面打字机效果                stream_mode='messages'")
    print("   显示'正在执行 X 节点'             stream_mode='updates'")
    print("   精细进度条（第 3/10 个批次）      stream_mode='custom'")
    print("   前端要完整 State                   stream_mode='values'")
    print("   排查节点执行次数                  stream_mode='debug'")
    print("   要看 LLM 的原始请求/响应           astream_events")
    print("   要接 LangSmith 做 trace            astream_events")

    print("\n③ 实践建议：LangGraph 项目里优先用 stream_mode")
    print("   原因：")
    print("   1. 语义更清楚 —— 'agent 节点在说话' 比 'run_id xxx 的 chat_model_stream' 好懂")
    print("   2. 代码更短 —— 不用自己过滤几十种事件类型")
    print("   3. 和业务对齐 —— 节点名就是你设计的名字")
    print()
    print("   只有需要'LLM 请求的完整细节'时才降到 astream_events。")

    print("\n④ 简历里那句话怎么讲")
    print("   '流式分两层：节点级进度用 stream_mode 的 updates 和 custom 推给前端，")
    print("   token 级用 messages 模式，靠 metadata 里的 langgraph_node 区分是哪个节点在输出。")
    print("   需要排查 LLM 层问题时，再降到 astream_events 看原始事件。'")
    print()
    print("   能说出'两层'和'什么时候降级'，比只说'用了 SSE'扎实得多。")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], None], bool]] = [
    # ("1", "values", demo1_values, False),
    # ("2", "updates", demo2_updates, False),
    ("3", "messages", demo3_messages, True),
    # ("4", "custom", demo4_custom, False),
    # ("5", "debug", demo5_debug, False),
    # ("6", "多模式组合", demo6_combined, False),
    # ("7", "和 astream_events 怎么选", demo7_choose_mode, False),
]


def main() -> None:
    args = sys.argv[1:]
    offline_only = "--offline" in args
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print(f"2.6 五种 stream_mode | 模型 = {MODEL_CODE}")
    if offline_only:
        print("模式：--offline（只跑 Demo 1/2/4/5/6/7）")
    print("=" * 72)

    for key, title, func, needs_model in DEMOS:
        if picked and key not in picked:
            continue
        if offline_only and needs_model:
            continue
        func()

    print()
    print("=" * 72)
    print("全部完成")
    print("=" * 72)


if __name__ == "__main__":
    main()
