"""2.5 SubGraph：子图隔离与脏数据治理

【跑这个文件能看到什么】
Demo 1  最小 SubGraph：把一张编译好的图当成节点
Demo 2  ★★ 父子 State 的映射机制：只传【同名字段】
Demo 3  ★★ 脏数据隔离实证：200 行原始数据怎么被挡在子图里
Demo 4  多个子图调度：父图按条件选不同的子 Agent
Demo 5  坑：字段名不一致时会静默失效
Demo 6  子图要不要自己的 checkpointer
Demo 7  什么时候该拆子图（判断标准）

【对应手册】Part 2 · 2.8 SubGraph
【对应简历】"配合只读子 Agent 限权限与轮数"、"解决子 Agent 回传无关数据"
【面试高频】"为什么能解决子 Agent 回传脏数据？
          因为子图使用独立的私有 State 跑多轮只读查询，中间成百上千行的原始
          数据留在子图内部消化，最终只将提炼后的'干净结论快照'写入父图共享
          State。" —— 但这句话只说结论，追问机制要能答出 Demo 2 的内容。

【怎么跑】
    cd studyLangChain_LangGraph/mini-project
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_05_subgraph.py

【全部离线，不调模型】
"""

import sys
from typing import Annotated, Callable, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from graph_flow import draw_flow


def show_title(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ============================================================
# Demo 1 · 最小 SubGraph
# ============================================================

def demo1_minimal_subgraph() -> None:
    show_title("Demo 1 · 最小 SubGraph：子图当节点（离线）")

    # ---------------- 子图 ----------------
    class SubState(TypedDict):
        value: int

    def sub_step_a(state: SubState) -> dict:
        return {"value": state["value"] * 2}

    def sub_step_b(state: SubState) -> dict:
        return {"value": state["value"] + 1}

    sub_builder = StateGraph(SubState)
    sub_builder.add_node("a", sub_step_a)
    sub_builder.add_node("b", sub_step_b)
    sub_builder.add_edge(START, "a")
    sub_builder.add_edge("a", "b")
    sub_builder.add_edge("b", END)
    sub_graph = sub_builder.compile()

    # ---------------- 父图 ----------------
    class ParentState(TypedDict):
        value: int
        note: str

    def parent_step(state: ParentState) -> dict:
        return {"note": f"子图算完得到 {state['value']}"}

    parent_builder = StateGraph(ParentState)
    # ★ 关键：直接把编译好的图 add_node
    parent_builder.add_node("child", sub_graph)
    parent_builder.add_node("finish", parent_step)
    parent_builder.add_edge(START, "child")
    parent_builder.add_edge("child", "finish")
    parent_builder.add_edge("finish", END)
    app = parent_builder.compile()

    print("① 用法只有一行：add_node('child', sub_graph)")
    print("   编译好的图本身就是一个 Runnable，可以直接当节点")

    result = app.invoke({"value": 5, "note": ""})
    print(f"\n② 执行结果：value = {result['value']}，note = {result['note']}")
    print("   计算过程：5 × 2 = 10，10 + 1 = 11")

    print("\n③ 图的结构（child 会自动展开成子图框）")
    draw_flow(
        app,
        node_notes={
            "START": "父图初始 State = {value: 5, note: ''}",
            "child": "★ 子图节点：框里就是子图自己的 a → b",
            "finish": "读子图算完的 value，写 note",
            "END": "value = 11",
        },
        edge_notes={
            ("START", "child"): ["父图把同名 value 传进子图"],
            ("child", "finish"): ["内部：5×2=10，再 +1=11"],
            ("finish", "END"): ["父图收尾"],
        },
        title="Demo 1 · 父图流程图（子图已展开）",
    )

    print("\n【和直接写两个节点的区别】")
    print("  直接写节点：sub_step_a、sub_step_b 都在父图里，")
    print("             共享同一个 State，字段混在一起")
    print("  用子图：    子图有独立的 State，")
    print("             父子之间只交换同名字段（Demo 2 详解）")
    print("")
    print("  所以子图的价值不是'代码组织'，是【状态隔离】。")


# ============================================================
# Demo 2 · 父子 State 的映射机制
#
# 这是本文件最核心的一节。面试被追问机制就答这个。
# ============================================================

def demo2_state_mapping() -> None:
    show_title("Demo 2 · 父子 State 的映射机制（离线）")

    # 子图 State：4 个字段，其中 2 个和父图同名
    class SubState(TypedDict):
        batch_id: str        # ← 与父图同名
        raw_rows: list       # ← 父图【没有】
        summary: str         # ← 与父图同名
        sub_internal: int    # ← 父图【没有】

    def sub_load(state: SubState) -> dict:
        # 模拟拉原始数据
        rows = [{"id": i, "detail": "很长的原始数据" * 5} for i in range(50)]
        return {"raw_rows": rows, "sub_internal": 999}

    def sub_summarize(state: SubState) -> dict:
        return {"summary": f"{state['batch_id']} 共 {len(state['raw_rows'])} 行"}

    sub_builder = StateGraph(SubState)
    sub_builder.add_node("load", sub_load)
    sub_builder.add_node("summarize", sub_summarize)
    sub_builder.add_edge(START, "load")
    sub_builder.add_edge("load", "summarize")
    sub_builder.add_edge("summarize", END)
    sub_graph = sub_builder.compile()

    # 父图 State：3 个字段
    class ParentState(TypedDict):
        batch_id: str
        summary: str
        verdict: str

    def parent_judge(state: ParentState) -> dict:
        return {"verdict": f"基于「{state['summary']}」判定：需复核"}

    parent_builder = StateGraph(ParentState)
    parent_builder.add_node("child", sub_graph)
    parent_builder.add_node("judge", parent_judge)
    parent_builder.add_edge(START, "child")
    parent_builder.add_edge("child", "judge")
    parent_builder.add_edge("judge", END)
    app = parent_builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "父图 State = {batch_id, summary, verdict}",
            "child": "★ 子图：load → summarize 两步",
            "judge": "读子图传回的 summary 写 verdict",
            "END": "父图只拿到同名2个字段",
        },
        edge_notes={
            ("START", "child"): ["同名 batch_id 传进子图"],
            ("child", "judge"): ["子图只回传 summary，raw_rows 留在子图里"],
            ("judge", "END"): ["父图收尾"],
        },
        title="Demo 2 · 父图流程图（State 映射）",
    )

    draw_flow(
        sub_graph,
        node_notes={
            "START": "子图 State = {batch_id, raw_rows, summary, sub_internal}",
            "load": "拉 50 行原始数据 + sub_internal=999",
            "summarize": "把 raw_rows 压成一句 summary",
            "END": "只回传 batch_id / summary 给父图",
        },
        edge_notes={
            ("START", "load"): ["子图内部"],
            ("load", "summarize"): ["raw_rows 只存在于子图"],
            ("summarize", "END"): ["子图结束"],
        },
        title="Demo 2 · 子图内部流程图（50 行数据不出子图）",
    )

    print("① 字段对照")
    print("   子图 State: batch_id / raw_rows / summary / sub_internal")
    print("   父图 State: batch_id / summary / verdict")
    print("   交集（同名）: batch_id / summary")

    result = app.invoke({"batch_id": "B002", "summary": "", "verdict": ""})

    print("\n② 执行结果（父图视角）")
    print(f"   返回的字段 = {list(result.keys())}")
    print(f"   batch_id = {result['batch_id']}")
    print(f"   summary  = {result['summary']}")
    print(f"   verdict  = {result['verdict']}")

    print("\n③ 关键观察")
    print("   ✓ batch_id 从父图【传进】子图了（子图能读到）")
    print("   ✓ summary 从子图【传回】父图了")
    print("   ✗ raw_rows 没有出现在父图结果里")
    print("   ✗ sub_internal 没有出现在父图结果里")
    print("   ✗ verdict 子图读不到（父图独有字段）")

    print("\n【机制，一句话】")
    print("  父图调子图时，只把【同名字段】传进去；")
    print("  子图返回时，也只把【父图有的同名字段】写回来。")
    print("")
    print("  所以：")
    print("    - 子图独有的字段 → 天然隔离，父图看不到")
    print("    - 父图独有的字段 → 子图读不到")
    print("    - 同名字段 → 双向流动")

    print("\n【这就是'脏数据治理'的全部原理】")
    print("  不是靠约定'子 Agent 不要回传脏数据'，")
    print("  是【State schema 本身在物理上限制】了能传什么。")
    print("")
    print("  子图的 raw_rows 想传回父图都传不了 ——")
    print("  因为父图 State 里没有这个字段，写回去会被丢弃。")
    print("")
    print("  面试答到这一层，比背'子图有独立 State'深一档。")


# ============================================================
# Demo 3 · 脏数据隔离实证
# ============================================================

def demo3_dirty_data_isolation() -> None:
    show_title("Demo 3 · 脏数据隔离实证（离线）")

    # 子图模拟真实场景：查 ERP 拉了 500 行，逐行清洗
    class SubState(TypedDict):
        batch_id: str
        raw_rows: list
        clean_rows: list
        conclusion: str
        iteration: int

    def sub_fetch(state: SubState) -> dict:
        """模拟从 ERP 拉数据：500 行，字段杂乱。"""
        rows = []
        for i in range(500):
            rows.append({
                "row_id": i,
                "material": f"MAT-{i:04d}",
                "qty": i % 7,
                "noise_field_1": "无关数据" * 20,
                "noise_field_2": None,
            })
        return {"raw_rows": rows}

    def sub_clean(state: SubState) -> dict:
        """清洗：只留关心的行。"""
        clean = [r for r in state["raw_rows"] if r["qty"] > 4]
        return {"clean_rows": clean}

    def sub_conclude(state: SubState) -> dict:
        """提炼结论：只输出一句话。"""
        return {
            "conclusion": (
                f"批次 {state['batch_id']}：原始 {len(state['raw_rows'])} 行，"
                f"清洗后 {len(state['clean_rows'])} 行异常，"
                f"疑似物料用量异常"
            ),
            "iteration": 3,
        }

    sub_builder = StateGraph(SubState)
    sub_builder.add_node("fetch", sub_fetch)
    sub_builder.add_node("clean", sub_clean)
    sub_builder.add_node("conclude", sub_conclude)
    sub_builder.add_edge(START, "fetch")
    sub_builder.add_edge("fetch", "clean")
    sub_builder.add_edge("clean", "conclude")
    sub_builder.add_edge("conclude", END)
    sub_graph = sub_builder.compile()

    # 父图 State：只有干净的字段
    class ParentState(TypedDict):
        batch_id: str
        conclusion: str
        report: str

    def parent_report(state: ParentState) -> dict:
        return {"report": f"【分析报告】{state['conclusion']}"}

    parent_builder = StateGraph(ParentState)
    parent_builder.add_node("investigate", sub_graph)
    parent_builder.add_node("report", parent_report)
    parent_builder.add_edge(START, "investigate")
    parent_builder.add_edge("investigate", "report")
    parent_builder.add_edge("report", END)
    app = parent_builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "父图 State = {batch_id, conclusion, report}",
            "investigate": "★ 子图：fetch → clean → conclude",
            "report": "把结论包成报告",
            "END": "父图只看到一句话结论",
        },
        edge_notes={
            ("START", "investigate"): ["同名 batch_id 传进子图"],
            ("investigate", "report"): ["500 行脏数据留在子图里"],
            ("report", "END"): ["父图干净收尾"],
        },
        title="Demo 3 · 父图流程图（脏数据隔离）",
    )

    draw_flow(
        sub_graph,
        node_notes={
            "START": "子图 State = {batch_id, raw_rows, clean_rows, conclusion, iteration}",
            "fetch": "拉 500 行原始数据（体积大）",
            "clean": "过滤出异常行",
            "conclude": "压成一句结论",
            "END": "只回传 conclusion",
        },
        edge_notes={
            ("START", "fetch"): ["子图内部"],
            ("fetch", "clean"): ["raw_rows 不往父图传"],
            ("clean", "conclude"): ["clean_rows 也不往父图传"],
            ("conclude", "END"): ["子图结束"],
        },
        title="Demo 3 · 子图内部流程图（脏数据不出子图）",
    )

    print("① 子图内部做了什么")
    print("   fetch     → 拉 500 行原始数据（含大量无关字段）")
    print("   clean     → 清洗，只剩 qty > 4 的行")
    print("   conclude  → 提炼成一句话结论")

    result = app.invoke({"batch_id": "B002", "conclusion": "", "report": ""})

    print("\n② 父图拿到什么")
    print(f"   字段 = {list(result.keys())}")
    print(f"   conclusion = {result['conclusion']}")
    print(f"   report     = {result['report']}")

    print("\n③ 对比数据量")
    print("   子图内部流转：500 行 × 5 个字段 = 2500 个值")
    print("   父图收到：      1 个字符串")
    print("   ← 99.96% 的数据被挡在子图里了")

    print("\n【为什么这很重要】")
    print("  1. 上下文长度：父图如果拿着 500 行去调模型，")
    print("     光这一块就几万 token，几轮下来上下文就爆了")
    print("  2. 状态体积：checkpointer 每存一份快照都要序列化整个 State，")
    print("     500 行 × 每步一份，数据库很快撑不住")
    print("  3. 注意力稀释：模型看到 500 行噪音，")
    print("     真正的关键信息（3 行异常）会被淹没，判断质量下降")
    print("")
    print("  这三条合起来，就是'子 Agent 回传脏数据'为什么是真问题。")

    print("\n【设计原则】")
    print("  子图内部：可以脏、可以大、可以多轮迭代")
    print("  父图只收：结论 + 证据 id + 置信度")
    print("")
    print("  要保留原始数据的话，让子图写到外部存储（数据库 / 文件），")
    print("  把 id 传回父图。父图需要时再按 id 去取。")


# ============================================================
# Demo 4 · 多子图调度
# ============================================================

def demo4_multi_subgraph() -> None:
    show_title("Demo 4 · 多子图调度：父图按条件选子 Agent（离线）")

    class SharedState(TypedDict):
        question_type: str
        batch_id: str
        answer: str
        trace: Annotated[list[str], lambda l, r: (l or []) + r]

    # ---------------- 子图 A：查工单 ----------------
    class WorkorderState(TypedDict):
        batch_id: str
        answer: str
        trace: Annotated[list[str], lambda l, r: (l or []) + r]

    def wo_node(state: WorkorderState) -> dict:
        return {
            "answer": f"{state['batch_id']} 工单：5 个批次，3 个异常",
            "trace": ["子图A-查工单"],
        }

    wo_builder = StateGraph(WorkorderState)
    wo_builder.add_node("wo", wo_node)
    wo_builder.add_edge(START, "wo")
    wo_builder.add_edge("wo", END)
    wo_graph = wo_builder.compile()

    # ---------------- 子图 B：查质检 ----------------
    class QualityState(TypedDict):
        batch_id: str
        answer: str
        trace: Annotated[list[str], lambda l, r: (l or []) + r]

    def q_node(state: QualityState) -> dict:
        return {
            "answer": f"{state['batch_id']} 质检：焊缝气孔，峰值温度 228℃",
            "trace": ["子图B-查质检"],
        }

    q_builder = StateGraph(QualityState)
    q_builder.add_node("q", q_node)
    q_builder.add_edge(START, "q")
    q_builder.add_edge("q", END)
    q_graph = q_builder.compile()

    # ---------------- 父图：路由 ----------------
    def route(state: SharedState) -> str:
        if state["question_type"] == "workorder":
            return "ask_workorder"
        return "ask_quality"

    def finalize(state: SharedState) -> dict:
        return {"trace": [f"父图-汇总：{state['answer'][:30]}"]}

    parent_builder = StateGraph(SharedState)
    parent_builder.add_node("ask_workorder", wo_graph)
    parent_builder.add_node("ask_quality", q_graph)
    parent_builder.add_node("finalize", finalize)
    parent_builder.add_edge(START, "router_dummy")
    # 用一个小节点做路由入口
    parent_builder.add_node("router_dummy", lambda s: {})
    parent_builder.add_conditional_edges(
        "router_dummy",
        route,
        {"ask_workorder": "ask_workorder", "ask_quality": "ask_quality"},
    )
    parent_builder.add_edge("ask_workorder", "finalize")
    parent_builder.add_edge("ask_quality", "finalize")
    parent_builder.add_edge("finalize", END)
    app = parent_builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "父图 State = {question_type, batch_id, answer, trace}",
            "router_dummy": "空节点，只为挂条件边",
            "ask_workorder": "子图 A：查工单",
            "ask_quality": "子图 B：查质检",
            "finalize": "汇总 answer",
            "END": "trace 里能看到走了哪条路",
        },
        title="Demo 4 · 父图流程图（两个子图按条件分流）",
    )

    draw_flow(
        wo_graph,
        node_notes={
            "START": "子图 A State = {batch_id, answer, trace}",
            "wo": "查工单",
            "END": "写回 answer",
        },
        title="Demo 4 · 子图 A（查工单）流程图",
    )

    draw_flow(
        q_graph,
        node_notes={
            "START": "子图 B State = {batch_id, answer, trace}",
            "q": "查质检",
            "END": "写回 answer",
        },
        title="Demo 4 · 子图 B（查质检）流程图",
    )

    print("① 父图有两个子图节点，按 question_type 路由\n")

    print("② question_type='workorder'")
    r1 = app.invoke({
        "question_type": "workorder", "batch_id": "B002",
        "answer": "", "trace": [],
    })
    print(f"   answer = {r1['answer']}")
    print(f"   trace  = {r1['trace']}")

    print("\n③ question_type='quality'")
    r2 = app.invoke({
        "question_type": "quality", "batch_id": "B002",
        "answer": "", "trace": [],
    })
    print(f"   answer = {r2['answer']}")
    print(f"   trace  = {r2['trace']}")

    print("\n【这个结构就是多 Agent 协作的骨架】")
    print("  父图 = 调度器，负责：")
    print("    - 判断该找哪个子 Agent")
    print("    - 收集各子 Agent 的结论")
    print("    - 汇总成最终答案")
    print("  子图 = 专家，负责：")
    print("    - 自己领域内的多轮查询和清洗")
    print("    - 只回传结论")
    print("")
    print("  注意：这不是'Agent 之间自由对话'，")
    print("  是【父图确定性调度】—— 谁什么时候被调，由条件边决定。")
    print("  这样可控、可审计，比让模型自己决定调谁稳得多。")


# ============================================================
# Demo 5 · 坑：字段名不一致
# ============================================================

def demo5_field_name_pitfall() -> None:
    show_title("Demo 5 · 坑：字段名不一致会静默失效（离线）")

    # 子图字段名和父图不一样
    class SubState(TypedDict):
        batch_no: str        # ← 父图叫 batch_id
        out: str

    def sub_node(state: SubState) -> dict:
        # 读不到 batch_no，会 KeyError 或拿到空值
        value = state.get("batch_no", "<读不到>")
        return {"out": f"子图读到的 batch_no = {value}"}

    sub_builder = StateGraph(SubState)
    sub_builder.add_node("n", sub_node)
    sub_builder.add_edge(START, "n")
    sub_builder.add_edge("n", END)
    sub_graph = sub_builder.compile()

    class ParentState(TypedDict):
        batch_id: str        # ← 子图叫 batch_no
        out: str

    parent_builder = StateGraph(ParentState)
    parent_builder.add_node("child", sub_graph)
    parent_builder.add_edge(START, "child")
    parent_builder.add_edge("child", END)
    app = parent_builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "父图 State = {batch_id: 'B002', out: ''}",
            "child": "子图字段叫 batch_no → 读不到 batch_id",
            "END": "out 是空的（数据静默丢失）",
        },
        edge_notes={
            ("START", "child"): ["父子字段名必须一致才会自动映射"],
            ("child", "END"): ["对不上就静默丢数据，不报错"],
        },
        title="Demo 5 · 流程图（字段名坑）",
    )

    print("① 父图字段 batch_id，子图字段 batch_no（名字不一致）")
    result = app.invoke({"batch_id": "B002", "out": ""})
    print(f"   执行结果 = {result}")
    print()
    print("   ← 子图读不到 batch_id（名字不同），")
    print("     父图也拿不到子图的 batch_no。")
    print("     整个过程【没有报错】，只是数据静默丢了。")

    print("\n② 这是最危险的失败模式")
    print("  报错还好排查，静默失效最难查：")
    print("  图跑通了、没异常、返回结构也对，就是值是空的。")

    print("\n③ 排查方法")
    print("  1. 父子 State 字段名对齐 —— 建议直接用同一个基类：")
    print("     class BaseState(TypedDict):")
    print("         batch_id: str")
    print("         trace: Annotated[list[str], ...]")
    print("     class SubState(BaseState):")
    print("         raw_rows: list          # 只加私有字段")
    print("")
    print("  2. 每个节点入口打印一行：")
    print("     print(f'[{node_name}] 收到字段 {list(state.keys())}')")
    print("     跑一次就知道谁没收到什么")
    print("")
    print("  3. 用 Pydantic 定义 State（严格模式），字段缺失会报错")
    print("     代价是灵活性下降，但能提前暴露问题")


# ============================================================
# Demo 6 · 子图要不要自己的 checkpointer
# ============================================================

def demo6_subgraph_checkpointer() -> None:
    show_title("Demo 6 · 子图要不要自己的 checkpointer（离线）")

    print("① 默认情况：子图不编译 checkpointer")
    print("   子图的中间步骤【是存快照的】，只是不单独开一份存储。")
    print("   父图跑子图这个节点时，会把自己的 checkpointer 借给它，")
    print("   子图的快照写进同一个库、同一个 thread、嵌套的 namespace 下。")
    print("   → 一份存储，一棵树。这是最常见也最推荐的配置。")
    print("")
    print("   namespace 长这样：")
    print("     父图这一层：''")
    print("     子图那一层：'child:<task_id>'")
    print("   所以 get_state(config) 查父图，")
    print("      get_state(config, subgraphs=True) 能把子图那层也查出来。")

    print("\n② 子图也 compile(checkpointer=...)")
    print("   实际不会变成'两套存储' —— 父图借下来的那个优先级更高，")
    print("   子图自己配的会被【静默忽略】。")
    print("   源码里 _resolve_checkpointer 的顺序：")
    print("     config 里有父图借来的 → 用它")
    print("     否则                 → 才用自己的")
    print("   所以这不是'多一份保险'，是'写了不生效'，更要命。")
    print("")
    print("   真想单独留一份历史，用 checkpointer=True：")
    print("     它仍然借父图的 saver，但会把 namespace 里的 task_id 去掉，")
    print("     同一个子图被调多次，历史合并到一处。")
    print("   适用场景很窄：")
    print("     - 子图需要单独被调用（既当子图用，也当独立图用）")
    print("     - 子图里也有 interrupt，需要独立恢复")

    print("\n③ 子图里有 interrupt 怎么办")
    print("   ✅ 子图不配、父图配。")
    print("      interrupt 挂起时，子图这一层的节点状态已经写进父图的 checkpointer，")
    print("      所以你用父图的 thread_id 就能把子图从断点接着跑。")
    print("      这是标准做法 —— 用户体验上就是'父流程暂停等我审批'。")
    print("")
    print("   反过来说：正因为子图状态被存下来了，interrupt 才恢复得了。")
    print("   如果子图真的一点快照都不存，挂起之后就没有起点可以接着跑。")
    print("   下面的 ④ 就是这个的实证。")

    print("\n④ 实测：父图有 cp、子图没有，子图里 interrupt")
    trace: list[str] = []

    class SubState(TypedDict):
        x: str

    def sub_review(state: SubState) -> dict:
        trace.append("子图 review 开始")
        decision = interrupt("子图需要确认")
        trace.append(f"子图拿到 {decision}")
        return {"x": str(decision)}

    sub_builder = StateGraph(SubState)
    sub_builder.add_node("review", sub_review)
    sub_builder.add_edge(START, "review")
    sub_builder.add_edge("review", END)
    sub_graph = sub_builder.compile()      # 注意：没配 checkpointer

    class ParentState(TypedDict):
        x: str
        done: bool

    parent_builder = StateGraph(ParentState)
    parent_builder.add_node("child", sub_graph)
    parent_builder.add_edge(START, "child")
    parent_builder.add_edge("child", END)
    app = parent_builder.compile(checkpointer=MemorySaver())

    draw_flow(
        app,
        node_notes={
            "START": "父图 State = {x: '', done: False}",
            "child": "★ 子图内部有 interrupt()",
            "END": "resume 后写回 x",
        },
        edge_notes={
            ("START", "child"): ["子图不配 checkpointer，借父图那份"],
            ("child", "END"): ["子图状态存在父图 cp 的嵌套 ns 里"],
        },
        title="Demo 6 · 父图流程图（子图 interrupt）",
    )

    draw_flow(
        sub_graph,
        node_notes={
            "START": "子图 State = {x: ''}",
            "review": "★ interrupt('子图需要确认')",
            "END": "写回 x",
        },
        edge_notes={
            ("START", "review"): ["进节点即挂起"],
            ("review", "END"): ["Command(resume='ok') 恢复"],
        },
        title="Demo 6 · 子图内部流程图",
    )

    config = {"configurable": {"thread_id": "sub-interrupt"}}
    app.invoke({"x": "", "done": False}, config)
    print(f"   挂起成功，轨迹 = {trace}")
    print(f"   .next = {app.get_state(config).next}")

    # 关键实证：子图这层的快照确实存在于父图的 checkpointer 里
    print("\n   ↓ 子图的中间状态在父图 checkpointer 的嵌套 ns 下：")
    for sub_state in app.get_state(config, subgraphs=True).tasks and []:
        pass
    try:
        snap = app.get_state(config, subgraphs=True)
        found = False
        for sub in snap.tasks:
            if getattr(sub, "state", None) is not None:
                print(f"     子图 ns = {sub.state.config['configurable'].get('checkpoint_ns')}")
                print(f"     子图 values = {sub.state.values}")
                found = True
        if not found:
            print("     （当前挂起点在父图层，子图快照在恢复时写入）")
    except Exception as exc:                       # noqa: BLE001
        print(f"     （读取子图快照失败：{exc}）")
    print("   ← 这就是'子图不单独存，而是挂在父图树上'的直接证据")

    trace.clear()
    result = app.invoke(Command(resume="ok"), config)
    print(f"\n   恢复成功，结果 = {result}")
    print(f"   轨迹 = {trace}")
    print("   ← 子图里的 interrupt 正常工作，借用的是父图的 checkpointer")


# ============================================================
# Demo 7 · 什么时候该拆子图
# ============================================================

def demo7_when_to_use() -> None:
    show_title("Demo 7 · 什么时候该拆子图（离线）")

    print("① 该拆的四种情况")
    print()
    print("   (1) 有一段逻辑会产生大量中间数据")
    print("       比如查 ERP 拉几百行、逐行清洗、最后只要一句结论")
    print("       → 拆子图，原始数据留在里面")
    print()
    print("   (2) 有一段逻辑要独立复用")
    print("       比如'查批次完整信息'这个能力，")
    print("       既在追溯流程里用，也在报告生成流程里用")
    print("       → 拆子图，两处都能 add_node")
    print()
    print("   (3) 需要独立的轮数限制")
    print("       主流程最多 5 轮，但'查证据'这个子任务最多 3 轮")
    print("       → 拆子图，各自设 recursion_limit")
    print()
    print("   (4) 需要不同的权限范围")
    print("       主流程能调写工具，'查证据'子图只给只读工具")
    print("       → 拆子图，各自 bind_tools 不同的白名单")
    print("       这就是简历里'配合只读子 Agent 限权限'的实现方式")

    print("\n② 不该拆的情况")
    print()
    print("   ✗ 只是想让代码文件小一点 → 用函数拆分，不用子图")
    print("   ✗ 只有两三个简单节点 → 拆了反而多一层，调试更绕")
    print("   ✗ 父子字段几乎完全重叠 → 隔离没意义，白白多一层")

    print("\n③ 拆分后的调试代价")
    print("   子图在父图的图可视化里是一个黑盒（只有一个方块）。")
    print("   要单独看子图结构，得 draw_flow(sub_graph) 再画一张。")
    print("   出错时要在两层日志里找，比扁平图麻烦。")
    print("")
    print("   所以：先写成扁平图，等真的出现'数据太脏/权限要分开/轮数要分开'")
    print("   再拆。别一上来就设计三层子图。")

    print("\n【一句话总结】")
    print("  子图的价值是【状态隔离】，不是【代码组织】。")
    print("  只有当'必须隔离'时才拆 —— 否则扁平图更简单。")


# ============================================================
# Demo 8 · 分支 + 子图 + 子图内循环（对照官方图）
# ============================================================

def demo8_router_with_weather_subgraph() -> None:
    show_title("Demo 8 · 路由 + 子图（chat / translate / weather）")

    class State(TypedDict):
        question: str
        kind: str
        answer: str
        calls: int      # 子图也写这个字段，所以能回传

    def classify(state: State) -> dict:
        return {"kind": state.get("kind", "weather")}

    def chat_node(state: State) -> dict:
        return {"answer": f"闲聊回复：{state['question']}"}

    def translate_node(state: State) -> dict:
        return {"answer": f"翻译：{state['question']}"}

    # ---------------- 子图 weather ----------------
    class WeatherState(TypedDict):
        question: str
        answer: str
        calls: int      # 与父图同名 → 能写回去

    def weather_llm(state: WeatherState) -> dict:
        calls = state.get("calls", 0) + 1
        return {"calls": calls, "answer": f"第 {calls} 次推理：查天气工具"}

    def weather_tools(state: WeatherState) -> dict:
        return {"calls": state.get("calls", 0)}

    def weather_route(state: WeatherState) -> str:
        # 调一次工具就收工，避免死循环
        return "end" if state["calls"] >= 2 else "tools"

    weather_builder = StateGraph(WeatherState)
    weather_builder.add_node("llm", weather_llm)
    weather_builder.add_node("tools", weather_tools)
    weather_builder.add_edge(START, "llm")
    weather_builder.add_conditional_edges(
        "llm", weather_route, {"tools": "tools", "end": END}
    )
    weather_builder.add_edge("tools", "llm")
    weather_graph = weather_builder.compile()

    # ---------------- 父图 ----------------
    def route(state: State) -> str:
        return state["kind"] if state["kind"] in ("chat", "translate") else "weather"

    parent = StateGraph(State)
    parent.add_node("classify", classify)
    parent.add_node("chat", chat_node)
    parent.add_node("translate", translate_node)
    parent.add_node("weather", weather_graph)
    parent.add_edge(START, "classify")
    parent.add_conditional_edges(
        "classify",
        route,
        {"chat": "chat", "translate": "translate", "weather": "weather"},
    )
    parent.add_edge("chat", END)
    parent.add_edge("translate", END)
    parent.add_edge("weather", END)
    app = parent.compile()

    draw_flow(
        app,
        node_notes={
            "classify": "判断问题类型",
            "chat": "闲聊",
            "translate": "翻译",
            "weather": "子图：llm ↔ tools 循环",
        },
        title="Demo 8 · classify 三路分流，weather 是子图",
    )

    print("\n① weather 子图内部：llm 调 tools，tools 回 llm，直到够轮数才去 END")
    result = app.invoke(
        {"question": "明天天气", "kind": "weather", "answer": "", "calls": 0}
    )
    print(f"   结果 answer = {result['answer']!r}，内部调用轮数 = {result.get('calls')}")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], None]]] = [
    # ("1", "最小 SubGraph", demo1_minimal_subgraph),
    # ("2", "父子 State 映射机制", demo2_state_mapping),
    # ("3", "脏数据隔离实证", demo3_dirty_data_isolation),
    # ("4", "多子图调度", demo4_multi_subgraph),
    # ("5", "字段名不一致的坑", demo5_field_name_pitfall),
    # ("6", "子图的 checkpointer", demo6_subgraph_checkpointer),
    # ("7", "什么时候该拆子图", demo7_when_to_use),
    ("8", "分支 + 子图（对照官方图）", demo8_router_with_weather_subgraph),
]


def main() -> None:
    args = sys.argv[1:]
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print("2.5 SubGraph 子图隔离（全部离线，不调模型）")
    print("=" * 72)

    for key, title, func in DEMOS:
        if picked and key not in picked:
            continue
        func()

    print()
    print("=" * 72)
    print("全部完成")
    print("=" * 72)


if __name__ == "__main__":
    main()
