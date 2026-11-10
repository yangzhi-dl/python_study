"""2.2 节点、边与编译（把 ReAct 循环画成图）

【跑这个文件能看到什么】
Demo 1  节点的三种写法：普通函数 / Runnable / 预置 ToolNode
Demo 2  普通边：顺序执行
Demo 3  ★ 条件边：返回值决定下一步走哪
Demo 4  条件边的三种映射写法（字符串 / 列表 / 显式映射）
Demo 5  ★ 完整 ReAct 图：ToolNode + tools_condition（最标准的写法）
Demo 6  ★ 手写条件路由（不用 prebuilt），看清 tools_condition 到底做了什么
Demo 7  图可视化 + recursion_limit 的实测行为

【对应手册】Part 2 · 2.3 节点 / 2.4 边 / 2.5 编译
【面试高频】"LangGraph 怎么防止死循环？"
          答：条件边判断终止条件 + recursion_limit 兜底，
          但要注意默认值（见 Demo 7 的实测）。

【怎么跑】
    cd studyLangChain_LangGraph/mini-project

    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_02_nodes_and_edges.py
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_02_nodes_and_edges.py --offline
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_02_nodes_and_edges.py 5
"""

import json
import os
import sys
from pathlib import Path
from typing import Annotated, Callable, Literal, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
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
# 二、工具
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


# ============================================================
# Demo 1 · 节点的三种写法
# ============================================================

class CounterState(TypedDict):
    count: int
    notes: Annotated[list[str], lambda left, right: (left or []) + right]


def demo1_node_forms() -> None:
    show_title("Demo 1 · 节点的三种写法（离线）")

    print("① 普通函数（最常用）")
    print("   def my_node(state: MyState) -> dict:")
    print("       return {'字段': 新值}")
    print("")
    print("   要求：参数是整个 State，返回值是 dict 补丁")

    def func_node(state: CounterState) -> dict:
        return {"count": state["count"] + 1, "notes": ["来自普通函数"]}

    # ② Runnable（比如绑定工具后的 llm）
    #    Runnable 的输入输出直接对接 State 的某个字段时，可以这样用
    from langchain_core.runnables import RunnableLambda

    runnable_node = RunnableLambda(
        lambda state: {"count": state["count"] + 10, "notes": ["来自 Runnable"]}
    )

    print("\n② Runnable（把已有的 Runnable 直接当节点）")
    print("   常见场景：把 llm 或 chain 直接 add_node")
    print("   注意：Runnable 的输入是 State 的话，它得自己处理 dict")

    # ③ 预置节点：ToolNode
    print("\n③ 预置节点：ToolNode（自动执行 tool_calls）")
    print("   builder.add_node('tools', ToolNode(TOOLS))")
    print("   它自动做的事：读 state['messages'][-1].tool_calls，")
    print("   逐个执行，把结果包成 ToolMessage 追加进 messages。")

    builder = StateGraph(CounterState)
    builder.add_node("func", func_node)
    builder.add_node("run", runnable_node)
    builder.add_edge(START, "func")
    builder.add_edge("func", "run")
    builder.add_edge("run", END)
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {count: 0, notes: []}",
            "func": "普通函数节点：count +1，notes 追加一条",
            "run": "RunnableLambda 节点：count +10，notes 追加一条",
            "END": "count = 11，notes 两条都在",
        },
        edge_notes={
            ("START", "func"): ["普通边：START 连到第一个节点"],
            ("func", "run"): ["notes 有 reducer → 累加", "count 无 reducer → 覆盖"],
            ("run", "END"): ["notes 再累加一条"],
        },
        title="Demo 1 · 流程图",
    )

    result = app.invoke({"count": 0, "notes": []})
    print(f"\n④ 跑一遍：count = {result['count']}")
    for note in result["notes"]:
        print(f"   - {note}")

    print("\n【节点命名建议】")
    print("  用业务语义命名，不要用 node1 / step2：")
    print("   ✅ agent / tools / plan / execute / verify / human_review")
    print("   ❌ n1 / n2 / func_a")
    print("   原因：图可视化时、日志排查时，名字就是唯一线索。")


# ============================================================
# Demo 2 · 普通边
# ============================================================

def demo2_normal_edges() -> None:
    show_title("Demo 2 · 普通边：顺序执行（离线）")

    class State(TypedDict):
        steps: Annotated[list[str], lambda l, r: (l or []) + r]

    def step_a(state: State) -> dict:
        return {"steps": ["a"]}

    def step_b(state: State) -> dict:
        return {"steps": ["b"]}

    def step_c(state: State) -> dict:
        return {"steps": ["c"]}

    builder = StateGraph(State)
    builder.add_node("a", step_a)
    builder.add_node("b", step_b)
    builder.add_node("c", step_c)

    # START / END 是常量，不是字符串 "START"
    print(f"① START 的实际值 = {START!r}")
    print(f"   END   的实际值 = {END!r}")
    print("   ← 它们是 '__start__' / '__end__'，")
    print("     所以写 add_edge(START, 'a') 而不是 add_edge('START', 'a')")

    builder.add_edge(START, "a")
    builder.add_edge("a", "b")
    builder.add_edge("b", "c")
    builder.add_edge("c", END)
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {steps: []}",
            "a": "return {'steps': ['a']}",
            "b": "return {'steps': ['b']}",
            "c": "return {'steps': ['c']}",
            "END": "steps = ['a','b','c']",
        },
        edge_notes={
            ("START", "a"): ["普通边：START 连到第一个节点"],
            ("a", "b"): ["steps 有 reducer → 累加"],
            ("b", "c"): ["steps 累加"],
            ("c", "END"): ["普通边：最后一个节点连到 END"],
        },
        title="Demo 2 · 流程图（普通边）",
    )

    result = app.invoke({"steps": []})
    print(f"\n② 执行顺序 = {result['steps']}")

    print("\n③ 简写：add_sequence")
    builder2 = StateGraph(State)
    # 注意两点：
    #   1. 参数是 [(节点名, 函数), ...]，只传名字会 TypeError
    #   2. 它只连【节点之间】的边，不连 START / END，必须自己补
    builder2.add_sequence([
        ("a", step_a),
        ("b", step_b),
        ("c", step_c),
    ])
    builder2.add_edge(START, "a")
    builder2.add_edge("c", END)
    app2 = builder2.compile()
    draw_flow(
        app2,
        node_notes={
            "START": "add_sequence 不连 START，要自己补",
            "a": "add_sequence 自动连 a→b",
            "b": "add_sequence 自动连 b→c",
            "c": "add_sequence 不连 END，要自己补",
            "END": "所以要补 START→a 和 c→END",
        },
        title="Demo 2 · add_sequence 建出来的图",
    )
    result2 = app2.invoke({"steps": []})
    print(f"   add_sequence([('a',f),('b',f),('c',f)]) 结果 = {result2['steps']}")
    print("   ← 省掉了 a→b、b→c 两条边，但 START→a 和 c→END 还得自己写")
    print("     不加会报：Graph must have an entrypoint")

    print("\n【边的规则】")
    print("  1. 每个节点必须有出边，否则图跑不通（编译时会报）")
    print("  2. START 只能有出边，END 只能有入边")
    print("  3. 一个节点可以有多个出边 —— 但那是【并行】不是【顺序】")
    print("     想按条件选一个，必须用条件边（Demo 3）")


# ============================================================
# Demo 3 · 条件边
# ============================================================

def demo3_conditional_edges() -> None:
    show_title("Demo 3 · 条件边：返回值决定走向（离线）")

    class State(TypedDict):
        score: int
        path: Annotated[list[str], lambda l, r: (l or []) + r]

    def judge(state: State) -> dict:
        return {"path": [f"judge(score={state['score']})"]}

    def pass_node(state: State) -> dict:
        return {"path": ["pass"]}

    def retry_node(state: State) -> dict:
        return {"path": ["retry"]}

    def route(state: State) -> str:
        """条件边函数：只看 State，返回下一个节点的名字。

        注意：它【不能】改 State，只能返回字符串。
        """
        if state["score"] >= 60:
            return "pass"
        return "retry"

    builder = StateGraph(State)
    builder.add_node("judge", judge)
    builder.add_node("pass", pass_node)
    builder.add_node("retry", retry_node)
    builder.add_edge(START, "judge")
    builder.add_conditional_edges("judge", route)
    builder.add_edge("pass", END)
    builder.add_edge("retry", END)

    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {score, path}",
            "judge": "route() 只看 score，不改 State",
            "pass": "score >= 60 走这里",
            "retry": "score < 60 走这里",
            "END": "两条路都汇到 END",
        },
        branch_targets={"judge": ["pass", "retry"]},
        title="Demo 3 · 流程图（条件边）",
    )

    print("① score=80（应该走 pass）")
    result_high = app.invoke({"score": 80, "path": []})
    print(f"   path = {result_high['path']}")

    print("\n② score=30（应该走 retry）")
    result_low = app.invoke({"score": 30, "path": []})
    print(f"   path = {result_low['path']}")

    print("\n【条件边和普通边的区别】")
    print("  add_edge('a', 'b')")
    print("    → 写死，a 执行完一定去 b")
    print("")
    print("  add_conditional_edges('a', route)")
    print("    → 动态，a 执行完调 route(state)，按返回值决定去哪")
    print("")
    print("  route 就是一个普通函数，返回【节点名字符串】。")
    print("  它不执行任何业务，只做判断 —— 保持它纯净，别在里面查数据库。")


# ============================================================
# Demo 4 · 条件边的三种映射写法
# ============================================================

def demo4_conditional_mapping() -> None:
    show_title("Demo 4 · 条件边的三种映射写法（离线）")

    class State(TypedDict):
        mode: str
        path: Annotated[list[str], lambda l, r: (l or []) + r]

    def router_node(state: State) -> dict:
        return {"path": [f"router(mode={state['mode']})"]}

    def n_a(state: State) -> dict:
        return {"path": ["A"]}

    def n_b(state: State) -> dict:
        return {"path": ["B"]}

    # ---------------- 写法 1：不传映射，直接返回节点名 ----------------
    def route_direct(state: State) -> str:
        return "A" if state["mode"] == "a" else "B"

    b1 = StateGraph(State)
    b1.add_node("router", router_node)
    b1.add_node("A", n_a)
    b1.add_node("B", n_b)
    b1.add_edge(START, "router")
    b1.add_conditional_edges("router", route_direct)
    b1.add_edge("A", END)
    b1.add_edge("B", END)
    app1 = b1.compile()

    draw_flow(
        app1,
        node_notes={
            "START": "初始 State = {mode, path}",
            "router": "route_direct 直接返回 'A' 或 'B'",
            "A": "mode='a' 走这里",
            "B": "其他情况走这里",
            "END": "两个分支都汇到 END",
        },
        branch_targets={"router": ["A", "B"]},
        title="Demo 4 · 写法一：直接返回节点名",
    )

    print("① 写法一：返回值直接就是节点名")
    print(f"   mode='a' → {app1.invoke({'mode': 'a', 'path': []})['path']}")
    print("   最简单，但有个隐患：节点改名时容易漏改 route 函数")

    # ---------------- 写法 2：传显式映射 ----------------
    def route_key(state: State) -> str:
        """返回的是'键'，不是节点名。"""
        return "go_a" if state["mode"] == "a" else "go_b"

    b2 = StateGraph(State)
    b2.add_node("router", router_node)
    b2.add_node("A", n_a)
    b2.add_node("B", n_b)
    b2.add_edge(START, "router")
    b2.add_conditional_edges(
        "router",
        route_key,
        {
            "go_a": "A",     # 键 → 节点名
            "go_b": "B",
        },
    )
    b2.add_edge("A", END)
    b2.add_edge("B", END)
    app2 = b2.compile()

    draw_flow(
        app2,
        node_notes={
            "START": "初始 State = {mode, path}",
            "router": "route_key 返回 'go_a' / 'go_b'，再查映射表",
            "A": "映射表 go_a → A",
            "B": "映射表 go_b → B",
            "END": "两个分支都汇到 END",
        },
        title="Demo 4 · 写法二：返回键 + 显式映射",
    )

    print("\n② 写法二：返回键 + 显式映射（推荐）")
    print(f"   mode='b' → {app2.invoke({'mode': 'b', 'path': []})['path']}")
    print("   好处：route 函数返回业务语义（go_a），")
    print("         节点改名只改映射表，route 函数不用动")

    # ---------------- 写法 3：返回列表（并行） ----------------
    def route_multi(state: State) -> list[str]:
        """返回列表 = 同时走多个分支（并行执行）。"""
        return ["A", "B"]

    b3 = StateGraph(State)
    b3.add_node("router", router_node)
    b3.add_node("A", n_a)
    b3.add_node("B", n_b)
    b3.add_edge(START, "router")
    b3.add_conditional_edges("router", route_multi)
    b3.add_edge("A", END)
    b3.add_edge("B", END)
    app3 = b3.compile()

    draw_flow(
        app3,
        node_notes={
            "START": "初始 State = {mode, path}",
            "router": "route_multi 返回 ['A','B'] = 两条一起走",
            "A": "和 B 并行执行",
            "B": "和 A 并行执行",
            "END": "两个分支都完成后才到 END",
        },
        branch_targets={"router": ["A", "B"]},
        title="Demo 4 · 写法三：返回列表（并行）",
    )

    print("\n③ 写法三：返回列表 = 并行执行多个分支")
    result3 = app3.invoke({"mode": "x", "path": []})
    print(f"   path = {result3['path']}")
    print("   ← A 和 B 都执行了。注意顺序不保证，因为是真的并行。")
    print("     并行分支写同一个字段会冲突，要靠 reducer 合并。")

    print("\n【三种写法怎么选】")
    print("  两个分支、节点名稳定  → 写法一")
    print("  分支多、会改名        → 写法二（推荐，也是官方示例的写法）")
    print("  要并行查多个数据源    → 写法三")


# ============================================================
# Demo 5 · 完整 ReAct 图（标准写法）
# ============================================================

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]#add_message:表示追加 Reducer函数部分


def demo5_react_graph() -> None:
    show_title("Demo 5 · 完整 ReAct 图（ToolNode + tools_condition）")

    llm_with_tools = llm.bind_tools(TOOLS)

    def agent_node(state: AgentState) -> dict:
        """agent 节点：调模型，把回复追加进 messages。"""
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))

    builder.add_edge(START, "agent")

    # 关键：tools_condition 自动判断
    #   有 tool_calls → "tools"
    #   没有          → END
    builder.add_conditional_edges("agent", tools_condition)

    # 工具执行完回到 agent，形成循环
    builder.add_edge("tools", "agent")

    app = builder.compile()

    print("① 图的结构")
    draw_flow(
        app,
        node_notes={
            "START": "初始 messages",
            "agent": "调模型，可能返回 tool_calls",
            "tools": "ToolNode 自动执行 tool_calls",
            "END": "没有 tool_calls 就结束",
        },
        title="Demo 5 · 流程图（ReAct 循环）",
    )

    print("\n② 开始执行")
    question = "3号线 2026-10-24 的不良原因是什么？"
    print(f"   问题：{question}")

    result = app.invoke({
        "messages": [
            SystemMessage(content="你是质量助手。需要数据时必须调用工具，不要猜测。"),
            HumanMessage(content=question),
        ]
    })

    print(f"\n③ 执行完，messages 共 {len(result['messages'])} 条")
    for i, msg in enumerate(result["messages"]):
        type_name = type(msg).__name__
        # 只有 AIMessage 有 tool_calls，其他类型没有这个属性
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            names = [c["name"] for c in tool_calls]
            print(f"   [{i}] {type_name:14} 请求工具 {names}")
        else:
            text = msg.text.replace("\n", " ")[:90]
            print(f"   [{i}] {type_name:14} {text}")

    print("\n④ 最终答案")
    print(f"   {result['messages'][-1].text}")

    print("\n【这段代码就是 create_agent 的内部结构】")
    print("  create_agent(model, tools, system_prompt) 做的事，展开就是：")
    print("    1. State = {messages: Annotated[list, add_messages]}")
    print("    2. add_node('agent', 调模型)")
    print("    3. add_node('tools', ToolNode(tools))")
    print("    4. 条件边：tools_condition")
    print("    5. tools → agent 回边")
    print("")
    print("  所以'LangChain 和 LangGraph 什么关系'的标准答案是：")
    print("  create_agent 内部就是一张 LangGraph 图，LangGraph 是底层编排引擎。")

    print("\n【ToolNode 帮你做了什么】")
    print("  1. 读 state['messages'][-1].tool_calls")
    print("  2. 按 name 找到工具，用 args 执行")
    print("  3. 把结果包成 ToolMessage（带 tool_call_id）追加进 messages")
    print("  4. 工具报错时把错误信息也包成 ToolMessage，不会让图崩掉")
    print("")
    print("  第 4 点很重要：你 1.5 手工写的 try/except，ToolNode 内置了。")


# ============================================================
# Demo 6 · 手写条件路由（不用 prebuilt）
# ============================================================

def demo6_manual_routing() -> None:
    show_title("Demo 6 · 手写条件路由，看清 tools_condition 干了什么")

    llm_with_tools = llm.bind_tools(TOOLS)

    def agent_node(state: AgentState) -> dict:
        response = llm_with_tools.invoke(state["messages"])#调用模型
        return {"messages": [response]}

    def route_after_agent(state: AgentState) -> Literal["tools", "__end__"]:
        """手写版 tools_condition。

        逻辑只有一句：最后一条消息有没有 tool_calls？
        有 → 去 tools 节点
        没有 → 结束
        """
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges( "agent", route_after_agent,
        {
            "tools": "tools",
            END: END,
        },
    )
    builder.add_edge("tools", "agent")
    app = builder.compile()

    print("① 手写版和 tools_condition 版的结构完全一样")
    draw_flow(
        app,
        node_notes={
            "START": "初始 messages",
            "agent": "调模型，可能返回 tool_calls",
            "tools": "ToolNode 执行工具",
            "END": "最后一条消息没有 tool_calls 就结束",
        },
        title="Demo 6 · 流程图（手写条件路由）",
    )

    print("\n② 执行（用一个不需要多轮的问题，快一点）")
    result = app.invoke({
        "messages": [
            SystemMessage(content="你是质量助手。"),
            HumanMessage(content="B002 这个批次有什么问题？"),
        ]
    })

    print(f"   共 {len(result['messages'])} 条消息")
    print(f"   最终答案：{result['messages'][-1].text[:150]}")

    print("\n【为什么要手写一遍】")
    print("  1. 面试问'你怎么控制 Agent 什么时候停'，")
    print("     答'判断最后一条消息有没有 tool_calls'，这就是答案。")
    print("  2. 真实业务里条件比这复杂，比如：")
    print("     - 有 tool_calls 但重试次数超限 → 强制结束")
    print("     - 有 tool_calls 但涉及写操作 → 转到人工审批节点")
    print("     - 没有 tool_calls 但结论没给证据 → 转回验证节点")
    print("  这些 tools_condition 都做不了，必须手写。")


# ============================================================
# Demo 7 · 图可视化 + recursion_limit
# ============================================================

def demo7_visualize_and_limit() -> None:
    show_title("Demo 7 · 图可视化 + recursion_limit 实测（离线）")

    print("① 先把图画出来看结构（draw_flow 直接读编译后的图）")
    print("   调试图结构时，先看图比读代码快。\n")

    class LoopState(TypedDict):
        n: int

    def loop_node(state: LoopState) -> dict:
        return {"n": state["n"] + 1}

    builder = StateGraph(LoopState)
    builder.add_node("loop", loop_node)
    builder.add_edge(START, "loop")
    builder.add_conditional_edges(
        "loop",
        lambda s: "loop" if s["n"] < 1000 else END,
    )
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {n: 0}",
            "loop": "n = n + 1",
            "END": "n >= 1000 时结束",
        },
        branch_targets={"loop": ["loop", "END"]},
        title="Demo 7 · 流程图（自循环）",
    )

    print("\n② ★ 实测：不设 recursion_limit 会怎样")
    try:
        result = app.invoke({"n": 0})
        print(f"   跑完了，n = {result['n']}")
        print("   ← 1000 次循环全部执行，【没有报错】")
        print("")
        print("   这说明 langgraph 1.2.16 的默认 recursion_limit")
        print("   【不是常见教程里说的 25】，而是很大（或不限）。")
        print("   所以别指望默认值保护你 —— 死循环会真的跑下去。")
    except GraphRecursionError as e:
        print(f"   抛了 GraphRecursionError: {str(e)[:100]}")

    print("\n③ 显式设置 recursion_limit=5")
    try:
        app.invoke({"n": 0}, {"recursion_limit": 5})
        print("   没报错？")
    except GraphRecursionError as e:
        print(f"   抛了 GraphRecursionError")
        print(f"   {str(e)[:160]}")
        print("   ← 这才拦住。")

    print("\n④ recursion_limit 怎么算")
    print("   它数的是【super-step 的数量】，不是节点数。")
    print("   一个 super-step = 一次并行执行的所有节点。")
    print("   线性图 3 个节点 = 3 个 super-step；")
    print("   ReAct 循环跑 3 轮 = agent/tools 各 3 次 = 6 个 super-step。")

    print("\n【生产写法】")
    print("   config = {'recursion_limit': 20}")
    print("   app.invoke(input, config)")
    print("")
    print("   注意：recursion_limit 放在【config】里，")
    print("   不是 invoke 的第二个位置参数（虽然位置参数也能传，但容易漏）。")

    print("\n【两道防线，都要有】")
    print("  第一道：条件边里的业务终止条件")
    print("          （比如 retry_count >= 3 就强制走 END）")
    print("  第二道：recursion_limit 兜底")
    print("          （业务逻辑写错时的最后保险）")
    print("")
    print("  只有第一道 → 逻辑一错就跑飞")
    print("  只有第二道 → 白烧 20 轮 token 才停，钱和时间都浪费")


# ============================================================
# Demo 8 · compile() 专项：它到底校验了什么
#
# 手册说"compile 会校验图的完整性（孤立节点、入口出口），不完整直接报错"。
# 实测只有"缺入口"会报错，孤立节点和缺出口都不报 —— 见下面实测结果。
# ============================================================

def demo8_compile_details() -> None:
    show_title("Demo 8 · compile() 专项：它到底校验了什么（离线）")

    class TinyState(TypedDict):
        x: int

    def inc(state: TinyState) -> dict:
        return {"x": state["x"] + 1}

    # ---------------- ① 缺入口 → 报错 ----------------
    print("① 缺入口（没有 START 出来的边）→ 报错")
    builder = StateGraph(TinyState)
    builder.add_node("a", inc)
    builder.add_edge("a", END)
    try:
        builder.compile()
        print("   编译成功了？")
    except ValueError as e:
        print(f"   ValueError: {e}")
        print("   ← 这是 compile() 唯一会硬拦的情况")

    # ---------------- ② 孤立节点 → 不报错 ----------------
    print("\n② 孤立节点（加了但从没连边）→ 不报错，被静默忽略")
    builder = StateGraph(TinyState)
    builder.add_node("a", inc)
    builder.add_node("orphan", inc)      # 没连任何边
    builder.add_edge(START, "a")
    builder.add_edge("a", END)
    app = builder.compile()
    print(f"   编译成功，执行结果 = {app.invoke({'x': 0})}")
    print("   节点列表 =", list(app.get_graph().nodes.keys()))
    print("   ← orphan 还在图里，但永远不会执行")
    print("     所以'节点没跑'这种问题，compile 不会帮你发现")

    # ---------------- ③ 缺出口 → 也不报错 ----------------
    print("\n③ 缺出口（节点没有出边）→ 不报错，执行到那儿就当结束")
    builder = StateGraph(TinyState)
    builder.add_node("a", inc)
    builder.add_edge(START, "a")
    app = builder.compile()
    print(f"   编译成功，执行结果 = {app.invoke({'x': 0})}")
    print("   ← 隐式结束。所以忘记加 add_edge('a', END) 不会报错，")
    print("     但如果有后续逻辑没执行，你只能靠日志发现")

    # ---------------- ④ compile 的参数 ----------------
    print("\n④ compile() 的主要参数")
    builder = StateGraph(TinyState)
    builder.add_node("a", inc)
    builder.add_edge(START, "a")
    builder.add_edge("a", END)

    app_full = builder.compile(
        checkpointer=MemorySaver(),      # 持久化（2.3 详讲）
        interrupt_before=[],             # 静态断点（2.4 详讲）
        interrupt_after=[],
        debug=False,                     # True 会打印每一步的执行细节
        name="my_tiny_graph",            # 给图起名，LangSmith trace 里能看出来
    )
    print(f"   checkpointer     → 启用持久化，invoke 时必须给 thread_id")
    print(f"   interrupt_before → 静态断点，执行某节点前挂起")
    print(f"   interrupt_after  → 执行某节点后挂起")
    print(f"   debug            → 打印执行细节，调试用，生产别开")
    print(f"   name             → 图的名字，实测 = {app_full.name!r}")

    # ---------------- ⑤ 编译后还能改结构吗 ----------------
    print("\n⑤ 编译后再 add_node → 警告，且不影响已编译的图")
    builder2 = StateGraph(TinyState)
    builder2.add_node("a", inc)
    builder2.add_edge(START, "a")
    builder2.add_edge("a", END)
    compiled = builder2.compile()
    builder2.add_node("late", inc)      # 编译后才加
    print(f"   已编译的图包含 late 吗 = {'late' in compiled.get_graph().nodes}")
    print("   ← 会打一条 warning：Adding a node to a graph that has already been compiled.")
    print("     要包含新节点必须【重新 compile】")
    recompiled = builder2.compile()
    print(f"   重新 compile 后包含 = {'late' in recompiled.get_graph().nodes}")

    # ---------------- ⑥ 编译产物是什么 ----------------
    print("\n⑥ 编译产物")
    print(f"   类型 = {type(compiled).__name__}")
    print("   ← CompiledStateGraph，它本身也是 Runnable，")
    print("     所以可以当子图塞进父图（2.5 会用）")
    print(f"\n   反复 invoke 互不影响：")
    print(f"     invoke({{'x': 0}})   = {compiled.invoke({'x': 0})}")
    print(f"     invoke({{'x': 100}}) = {compiled.invoke({'x': 100})}")
    print("   ← 编译一次，用无数次。不要在请求处理函数里每次 compile")

    print("\n【修正手册的一句话】")
    print("  手册写'compile 会校验图的完整性（孤立节点、入口出口），不完整直接报错'。")
    print("  实测在 langgraph 1.2.16 上：")
    print("    缺入口   → ValueError ✅ 会报")
    print("    孤立节点 → 静默忽略 ❌ 不报")
    print("    缺出口   → 隐式结束 ❌ 不报")
    print("")
    print("  所以别指望 compile 帮你查图结构问题，")
    print("  该用 draw_flow(app) 把图打印出来肉眼过一遍。")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], None], bool]] = [
    # ("1", "节点的三种写法", demo1_node_forms, False),
    # ("2", "普通边", demo2_normal_edges, False),
    # ("3", "条件边", demo3_conditional_edges, False),
    # ("4", "条件边三种映射", demo4_conditional_mapping, False),
    # ("5", "完整 ReAct 图", demo5_react_graph, True),
    # ("6", "手写条件路由", demo6_manual_routing, True),
    # ("7", "可视化 + recursion_limit", demo7_visualize_and_limit, False),
    ("8", "compile 专项", demo8_compile_details, False),
]


def main() -> None:
    args = sys.argv[1:]
    offline_only = "--offline" in args
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print(f"2.2 节点、边与编译 | 模型 = {MODEL_CODE}")
    if offline_only:
        print("模式：--offline（只跑 Demo 1/2/3/4/7）")
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
