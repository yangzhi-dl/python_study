"""2.1 State 与 Reducer（LangGraph 的地基）

【跑这个文件能看到什么】
Demo 1  最小可用图：State + 两个节点 + 编译 + invoke
Demo 2  ★ 默认行为是【覆盖】，不是追加
Demo 3  operator.add：让列表累加
Demo 4  ★ add_messages：消息专用 reducer（含同 id 替换）
Demo 5  自定义 reducer：去重 / 取最大值
Demo 6  ★ 哪些字段该加 reducer、哪些不该（同一个图对比）
Demo 7  State 定义的六个坑

【对应手册】Part 2 · 2.1 State 定义 + 2.2 Reducer
【面试高频】"为什么 State 里的列表要用 Annotated 配合 Reducer？"
          标准答案：默认情况下节点返回同名字段会直接覆盖原状态，
          用 Reducer 才能实现增量追加。

【怎么跑】
    cd studyLangChain_LangGraph/mini-project
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_01_state_and_reducer.py
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_01_state_and_reducer.py 4

【不需要调模型，全部离线，秒出结果】
"""

import operator
import sys
from typing import Annotated, Callable, NotRequired, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from graph_flow import draw_flow


def show_title(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ============================================================
# Demo 1 · 最小可用图
#
# 图的三要素：State（数据）+ Node（函数）+ Edge（连线）
# ============================================================

class SimpleState(TypedDict):
    """最简单的 State：两个字段。"""

    count: int
    log: list[str]


def node_increment(state: SimpleState) -> dict:
    """节点函数：读 State，返回要更新的字段。

    注意两个细节：
    1. 参数是整个 State（不是某个字段）
    2. 返回值是 dict，只包含要改的字段（不用返回完整 State）
    """
    current = state["count"]
    return {"count": current + 1, "log": [f"increment: {current} -> {current + 1}"]}


def node_report(state: SimpleState) -> dict:
    """另一个节点。"""
    return {"log": [f"report: count={state['count']}"]}


def demo1_minimal_graph() -> None:
    show_title("Demo 1 · 最小可用图（离线）")

    # ① 建图
    builder = StateGraph(SimpleState)


    # ② 加节点：名字 + 函数
    builder.add_node("increment", node_increment)
    builder.add_node("report", node_report)

    # ③ 加边：决定执行顺序
    builder.add_edge(START, "increment")
    builder.add_edge("increment", "report")
    builder.add_edge("report", END)

    # ④ 编译：编译后才能执行
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {count: 0, log: []}",
            "increment": "return {count: 1, log: ['increment: 0 -> 1']}",
            "report": "return {log: ['report: count=1']}",
            "END": "最终 State = {count: 1, log: ['report: count=1']}",
        },
        edge_notes={
            ("START", "increment"): ["初始 State 原样进图，不经过任何 reducer"],
            ("increment", "report"): [
                "log 没有 reducer → 覆盖：[] → ['increment: 0 -> 1']",
                "count 没有 reducer → 覆盖：0 → 1",
            ],
            ("report", "END"): [
                "log 没有 reducer → 覆盖：increment 那条被冲掉",
                "最终 log 只剩 report 这一条",
            ],
        },
        title="Demo 1 · 流程图",
    )

    print("① 图的节点 =", list(app.get_graph().nodes.keys()))
    print("② 开始执行，初始 State = {'count': 0, 'log': []}")

    result = app.invoke({"count": 0, "log": []})

    print("\n③ 执行完的 State")
    print(f"   count = {result['count']}")
    print("   log   =")
    for line in result["log"]:
        print(f"     - {line}")

    print("\n【关键理解】")
    print("  1. 节点函数返回的 dict 不是'新 State'，是'要合并进 State 的补丁'")
    print("  2. 合并规则由 reducer 决定 —— 这就是本文件后面全部内容")
    print("  3. 不写 reducer 时，默认规则是【覆盖】")
    print("")
    print("  看上面 log 只有 1 条（report 那条），")
    print("  increment 写进去的那条被覆盖了 —— Demo 2 详细看这个现象。")


# ============================================================
# Demo 2 · 默认行为：覆盖
# ============================================================

def demo2_default_overwrite() -> None:
    show_title("Demo 2 · 默认行为是【覆盖】（离线）")

    class State(TypedDict):
        log: list[str]

    def node_a(state: State) -> dict:
        return {"log": ["来自 a"]}

    def node_b(state: State) -> dict:
        return {"log": ["来自 b"]}

    builder = StateGraph(State)
    builder.add_node("a", node_a)
    builder.add_node("b", node_b)
    builder.add_edge(START, "a")
    builder.add_edge("a", "b")
    builder.add_edge("b", END)
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {log: []}",
            "a": "return {log: ['来自 a']}",
            "b": "return {log: ['来自 b']}",
            "END": "最终 State = {log: ['来自 b']}",
        },
        edge_notes={
            ("START", "a"): ["log 没加 reducer"],
            ("a", "b"): ["log 覆盖：[] → ['来自 a']"],
            ("b", "END"): [
                "log 覆盖：['来自 a'] → ['来自 b']",
                "a 写的那条没了 —— 这就是默认行为",
            ],
        },
        title="Demo 2 · 流程图",
    )

    result = app.invoke({"log": []})

    print("① 两个节点各自返回 {'log': [...]}")
    print("   a 返回 ['来自 a']")
    print("   b 返回 ['来自 b']")
    print(f"\n② 最终 State 的 log = {result['log']}")
    print("   ← 只剩 b 的！a 的写丢了。")

    print("\n【为什么会这样】")
    print("  没有 reducer 时，LangGraph 的合并规则是：")
    print("      新值直接替换旧值（dict 的 update 语义）")
    print("")
    print("  所以第二次写入把第一次的覆盖了。")
    print("  这在'只记录最终结果'时没问题，")
    print("  但'要累积历史'时就完全错了。")

    print("\n【典型翻车场景】")
    print("  Agent 状态里放 messages 列表，没加 reducer：")
    print("  模型说了 5 轮，State 里只剩最后 1 条消息。")
    print("  表现是'Agent 失忆了'，但你会以为是模型的问题。")


# ============================================================
# Demo 3 · operator.add：累加
# ============================================================

def demo3_operator_add() -> None:
    show_title("Demo 3 · operator.add：让列表累加（离线）")

    class State(TypedDict):
        # 关键：Annotated[类型, reducer函数]
        log: Annotated[list[str], operator.add]
        count: int

    def node_a(state: State) -> dict:
        return {"log": ["来自 a"], "count": state["count"] + 1}

    def node_b(state: State) -> dict:
        return {"log": ["来自 b"], "count": state["count"] + 1}

    builder = StateGraph(State)
    builder.add_node("a", node_a)
    builder.add_node("b", node_b)
    builder.add_edge(START, "a")
    builder.add_edge("a", "b")
    builder.add_edge("b", END)
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {log: [], count: 0}",
            "a": "return {log: ['来自 a'], count: 1}",
            "b": "return {log: ['来自 b'], count: 2}",
            "END": "最终 State = {log: ['来自 a', '来自 b'], count: 2}",
        },
        edge_notes={
            ("START", "a"): ["log 用 operator.add，count 用默认覆盖"],
            ("a", "b"): [
                "log  + 累加：[] + ['来自 a'] = ['来自 a']",
                "count 覆盖：0 → 1",
            ],
            ("b", "END"): [
                "log  + 累加：['来自 a'] + ['来自 b'] = ['来自 a', '来自 b']",
                "count 覆盖：1 → 2（节点自己算好的，不加 reducer 也对）",
            ],
        },
        title="Demo 3 · 流程图",
    )

    result = app.invoke({"log": [], "count": 0})

    print("① log 加了 operator.add reducer")
    print(f"   最终 log = {result['log']}")
    print("   ← 两条都在了，顺序就是执行顺序")

    print("\n② count 没加 reducer，但依然正确累加")
    print(f"   最终 count = {result['count']}")
    print("   ← 因为节点里读的是 state['count']，自己算好了再返回")
    print("     整数这种'标量'通常不需要 reducer，节点自己算就行")

    print("\n【Annotated 的读法】")
    print("   log: Annotated[list[str], operator.add]")
    print("        └──┬──┘ └──┬──┘ └────┬─────┘")
    print("        字段名   类型      reducer 函数")
    print("")
    print("   翻译成人话：")
    print("   'log 这个字段，合并时不要覆盖，用 operator.add 加起来'")
    print("")
    print("   operator.add 对列表就是 + 运算：[] + ['a'] + ['b'] = ['a', 'b']")

    print("\n【同样的 reducer，对字符串和数字的行为】")
    print(f"   ['a'] + ['b']        = {['a'] + ['b']}")
    print(f"   1 + 2                = {1 + 2}          ← 数字会相加，注意别乱用")
    print(f"   'x' + 'y'            = {'x' + 'y'!r}       ← 字符串会拼接")


# ============================================================
# Demo 4 · add_messages：消息专用
#
# 这是 LangGraph 里最重要的一个 reducer，Agent 全靠它。
# ============================================================

def demo4_add_messages() -> None:
    show_title("Demo 4 · add_messages：消息专用 reducer（离线）")

    class State(TypedDict):
        messages: Annotated[list, add_messages]

    def node_reply(state: State) -> dict:
        last = state["messages"][-1]
        return {"messages": [AIMessage(content=f"收到：{last.content}")]}

    builder = StateGraph(State)
    builder.add_node("reply", node_reply)
    builder.add_edge(START, "reply")
    builder.add_edge("reply", END)
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 messages（3 次 invoke 各不一样，见下面 ①②③）",
            "reply": "return {messages: [AIMessage('收到：...')]}",
            "END": "messages 由 add_messages 合并",
        },
        edge_notes={
            ("START", "reply"): [
                "① HumanMessage('你好') → 原样进 State",
                "② {'role':'user'} → 自动转 HumanMessage + 补 UUID",
                "③ 同 id 的消息 → 后一条替换前一条，不追加",
            ],
            ("reply", "END"): [
                "节点返回的 AIMessage 追加到末尾（并自动补 id）",
            ],
        },
        title="Demo 4 · 流程图",
    )

    print("① 基本用法：追加")
    result = app.invoke({"messages": [HumanMessage(content="你好")]})
    print(f"   messages 条数 = {len(result['messages'])}")
    for i, msg in enumerate(result["messages"]):
        print(f"   [{i}] {type(msg).__name__:14} {msg.content}")

    print("\n② add_messages 比 operator.add 多了什么")
    print("   它不只是追加，还会做三件事：")

    print("\n   (1) 自动转换：dict 会转成消息对象")
    result2 = app.invoke({
        "messages": [{"role": "user", "content": "dict 形式"}]
    })
    print(f"       输入 dict，输出类型 = {type(result2['messages'][0]).__name__}")

    print("\n   (2) 自动生成 id：没 id 的消息会补一个 UUID")
    print(f"       自动 id = {result2['messages'][0].id}")

    print("\n   (3) 同 id 替换，不是追加")
    result3 = app.invoke({
        "messages": [
            HumanMessage(content="第一句", id="m1"),
            HumanMessage(content="第二句", id="m2"),
            HumanMessage(content="第二句改过了", id="m2"),   # 同 id
        ]
    })
    print(f"       messages 条数 = {len(result3['messages'])}")
    for msg in result3["messages"]:
        print(f"       {msg.id}: {msg.content}")
    print("       ← m2 被'第二句改过了'替换了，不是多出一条")
    print("         这个特性用来做'消息编辑'和'状态回滚'")

    print("\n【为什么 Agent 必须用 add_messages 而不是 operator.add】")
    print("  1. 类型安全：dict 自动转消息对象，不用手动构造")
    print("  2. 消息编辑：同 id 可以替换，支持'改上一条'")
    print("  3. 和 checkpointer 配合：恢复会话时能正确重建消息列表")
    print("")
    print("  记住这个写法，它是 LangGraph Agent 的标准开头：")
    print("      class State(TypedDict):")
    print("          messages: Annotated[list, add_messages]")


# ============================================================
# Demo 5 · 自定义 reducer
# ============================================================

def demo5_custom_reducer() -> None:
    show_title("Demo 5 · 自定义 reducer（离线）")

    # ---------------- reducer 1：去重追加 ----------------
    def merge_unique(left: list[str], right: list[str]) -> list[str]:
        """追加但去重，保持顺序。

        注意：left 可能是 None（首次执行时字段还没值）。
        """
        if left is None:
            left = []
        result = list(left)
        for item in right:
            if item not in result:
                result.append(item)
        return result

    # ---------------- reducer 2：取最大值 ----------------
    def keep_max(left: int | None, right: int) -> int:
        """保留最大值。用于'最严重等级'这类字段。"""
        if left is None:
            return right
        return max(left, right)

    class State(TypedDict):
        sources: Annotated[list[str], merge_unique]
        max_severity: Annotated[int, keep_max]

    def node_a(state: State) -> dict:
        # 故意重复 'MES'，看会不会被去重
        return {"sources": ["MES", "QMS"], "max_severity": 2}

    def node_b(state: State) -> dict:
        return {"sources": ["MES", "设备参数"], "max_severity": 5}

    def node_c(state: State) -> dict:
        return {"sources": ["QMS"], "max_severity": 1}

    builder = StateGraph(State)
    builder.add_node("a", node_a)
    builder.add_node("b", node_b)
    builder.add_node("c", node_c)
    builder.add_edge(START, "a")
    builder.add_edge("a", "b")
    builder.add_edge("b", "c")
    builder.add_edge("c", END)
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {sources: [], max_severity: 0}",
            "a": "return {sources: ['MES','QMS'], max_severity: 2}",
            "b": "return {sources: ['MES','设备参数'], max_severity: 5}",
            "c": "return {sources: ['QMS'], max_severity: 1}",
            "END": "最终 sources 去重、max_severity 取最大",
        },
        edge_notes={
            ("START", "a"): [
                "sources 用 merge_unique（追加去重）",
                "max_severity 用 keep_max（只留最大值）",
            ],
            ("a", "b"): [
                "sources：[] + ['MES','QMS'] = ['MES','QMS']",
                "max_severity：keep_max(0, 2) = 2",
            ],
            ("b", "c"): [
                "sources：MES 重复跳过 → ['MES','QMS','设备参数']",
                "max_severity：max(2, 5) = 5",
            ],
            ("c", "END"): [
                "sources：QMS 已存在跳过 → 不变",
                "max_severity：max(5, 1) = 5 ← 不是 1，节点说了不算",
            ],
        },
        title="Demo 5 · 流程图",
    )

    result = app.invoke({"sources": [], "max_severity": 0})

    print("① 三个节点分别返回：")
    print("   a: sources=['MES','QMS']      max_severity=2")
    print("   b: sources=['MES','设备参数']  max_severity=5")
    print("   c: sources=['QMS']            max_severity=1")

    print("\n② 合并结果")
    print(f"   sources      = {result['sources']}")
    print("   ← MES 和 QMS 都只出现一次，去重生效了")
    print(f"   max_severity = {result['max_severity']}")
    print("   ← 保留了最大值 5，不是最后一次的 1")

    print("\n【自定义 reducer 的三个硬要求】")
    print("  1. 签名必须是 (left, right) -> 新值")
    print("     left 是 State 里已有的值，right 是节点返回的新值")
    print("")
    print("  2. left 可能是 None")
    print("     首次执行时字段还没值，必须处理 None，否则 TypeError")
    print("")
    print("  3. 必须返回【新对象】，不能原地改 left")
    print("     left.append(...) 然后 return left 是错的：")
    print("     checkpointer 存快照时可能拿到被改过的旧对象，状态就乱了")

    print("\n【实际业务里的用法】")
    print("  max_severity  → 多个证据算出不同严重等级，取最高的")
    print("  merge_unique  → 收集证据来源，避免重复")
    print("  这两个在你的根因追溯里都能直接用。")


# ============================================================
# Demo 6 · 哪些字段该加 reducer，哪些不该
#
# 面试如果只答"列表要加 reducer"是半对，
# 能说出"哪些不该加"才是真懂。
# ============================================================

def demo6_which_fields_need_reducer() -> None:
    show_title("Demo 6 · 哪些字段该加、哪些不该（离线）")

    # ---------------- 错误示范：全都加 ----------------
    class BadState(TypedDict):
        messages: Annotated[list, add_messages]
        plan: Annotated[list[str], operator.add]        # 计划不该累加
        approved: Annotated[bool, lambda a, b: b or a]  # 审批不该这样合
        retry_count: Annotated[int, operator.add]       # 计数不该累加

    # ---------------- 正确示范：分开处理 ----------------
    class GoodState(TypedDict):
        messages: Annotated[list, add_messages]   # 追加
        plan: list[str]                           # 覆盖：新计划顶掉旧计划
        approved: bool                            # 覆盖：本次审批结果
        retry_count: int                          # 覆盖：节点自己算好

    def run_bad() -> dict:
        def node_plan(state: BadState) -> dict:
            return {"plan": ["查工单", "查质检"], "retry_count": 1}

        def node_replan(state: BadState) -> dict:
            # 重新规划，应该是"替换"而不是"追加"
            return {"plan": ["直接查质检"], "retry_count": 1}

        builder = StateGraph(BadState)
        builder.add_node("plan", node_plan)
        builder.add_node("replan", node_replan)
        builder.add_edge(START, "plan")
        builder.add_edge("plan", "replan")
        builder.add_edge("replan", END)

        app = builder.compile()
        draw_flow(
            app,
            node_notes={
                "START": "初始 State = {plan: [], retry_count: 0}",
                "plan": "return {plan: ['查工单','查质检'], retry_count: 1}",
                "replan": "return {plan: ['直接查质检'], retry_count: 1}",
                "END": "错误结果：两个计划混在一起了",
            },
            edge_notes={
                ("START", "plan"): ["BadState：plan 和 retry_count 都加了 reducer"],
                ("plan", "replan"): [
                    "plan  + 累加：[] + ['查工单','查质检']",
                    "retry + 累加：0 + 1 = 1",
                ],
                ("replan", "END"): [
                    "plan  + 累加 → ['查工单','查质检','直接查质检']  ✗ 混了",
                    "retry + 累加 → 1 + 1 = 2",
                ],
            },
            title="Demo 6 · 错误示范（BadState）的图结构",
        )
        return app.invoke(
            {"messages": [], "plan": [], "approved": False, "retry_count": 0}
        )

    def run_good() -> dict:
        def node_plan(state: GoodState) -> dict:
            return {"plan": ["查工单", "查质检"], "retry_count": 1}

        def node_replan(state: GoodState) -> dict:
            return {"plan": ["直接查质检"], "retry_count": state["retry_count"] + 1}

        builder = StateGraph(GoodState)
        builder.add_node("plan", node_plan)
        builder.add_node("replan", node_replan)
        builder.add_edge(START, "plan")
        builder.add_edge("plan", "replan")
        builder.add_edge("replan", END)

        app = builder.compile()
        draw_flow(
            app,
            node_notes={
                "START": "初始 State = {plan: [], retry_count: 0}",
                "plan": "return {plan: ['查工单','查质检'], retry_count: 1}",
                "replan": "return {plan: ['直接查质检'], retry_count: 旧值+1}",
                "END": "正确结果：新计划干净替换旧计划",
            },
            edge_notes={
                ("START", "plan"): ["GoodState：plan 和 retry_count 都不加 reducer"],
                ("plan", "replan"): [
                    "plan  覆盖 → ['查工单','查质检']",
                    "retry 覆盖 → 1",
                ],
                ("replan", "END"): [
                    "plan  覆盖 → ['直接查质检']  ✓ 旧计划退场",
                    "retry 覆盖 → 2（节点自己 +1 算好再返回）",
                ],
            },
            title="Demo 6 · 正确示范（GoodState）的图结构",
        )
        return app.invoke(
            {"messages": [], "plan": [], "approved": False, "retry_count": 0}
        )

    print("场景：先规划 ['查工单','查质检']，然后重新规划 ['直接查质检']\n")

    bad = run_bad()
    print("① 全都加 reducer（错误）")
    print(f"   plan        = {bad['plan']}")
    print("   ← 旧计划没被顶掉，两个计划混在一起了，执行时全乱")
    print(f"   retry_count = {bad['retry_count']}")
    print("   ← 只跑了 2 个节点，计数却是 2（因为累加）")

    good = run_good()
    print("\n② 分开处理（正确）")
    print(f"   plan        = {good['plan']}")
    print("   ← 新计划干净地替换了旧计划")
    print(f"   retry_count = {good['retry_count']}")
    print("   ← 节点自己 +1，语义明确")

    print("\n【判断标准，一句话】")
    print("  这个字段是【累积历史】还是【当前快照】？")
    print("    累积历史 → 加 reducer（messages / evidences / sources / 日志）")
    print("    当前快照 → 不加（plan / approved / status / 当前步骤 / 计数）")

    print("\n【常见字段归类】")
    print("   必须加 reducer：")
    print("     messages      消息历史")
    print("     evidences     证据列表（越查越多）")
    print("     sources       数据来源集合")
    print("     errors        错误记录")
    print("   不该加 reducer：")
    print("     plan          调查计划（新计划替换旧的）")
    print("     approved      审批结果（本次的）")
    print("     current_step  当前步骤")
    print("     final_answer  最终答案（只留最后一版）")

    print("\n【面试加分点】")
    print("  如果只说'列表都要加 reducer'，面试官会追问：")
    print("  '那计划列表呢？重新规划时你要追加还是替换？'")
    print("  答'替换'，并说明'所以不加 reducer'，这层就过了。")


# ============================================================
# Demo 7 · State 定义的六个坑
# ============================================================

def demo7_state_pitfalls() -> None:
    show_title("Demo 7 · State 定义的六个坑（离线）")

    print("① TypedDict 不能有默认值")
    print("   ❌ class State(TypedDict):")
    print("          count: int = 0          ← 语法错误")
    print("   ✅ 默认值在 invoke 时传：")
    print("          app.invoke({'count': 0, ...})")
    print("   或者用 NotRequired 声明可选，节点里自己兜底：")

    class StateWithOptional(TypedDict):
        required_field: str
        optional_field: NotRequired[int]

    def node_optional(state: StateWithOptional) -> dict:
        # 可选字段要自己兜底
        value = state.get("optional_field", 0)
        return {"optional_field": value + 1}

    builder = StateGraph(StateWithOptional)
    builder.add_node("n", node_optional)
    builder.add_edge(START, "n")
    builder.add_edge("n", END)
    app = builder.compile()

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {'required_field': 'x'}（没传 optional_field）",
            "n": "state.get('optional_field', 0) + 1",
            "END": "结果 = {'required_field': 'x', 'optional_field': 1}",
        },
        edge_notes={
            ("START", "n"): ["optional_field 不存在，节点自己兜底成 0"],
            ("n", "END"): ["return {'optional_field': 1}，合并进 State"],
        },
        title="Demo 7 · 流程图",
    )

    result = app.invoke({"required_field": "x"})
    print(f"   不传 optional_field 也能跑，结果是 {result}")

    print("\n② 字段名拼错不会报错，只会静默失效")
    print("   节点 return {'mesages': [...]}（少个 s）")
    print("   LangGraph 不会报错，但 State 里那个字段永远不会被更新。")
    print("   排查方法：打印 invoke 的返回结果，对一眼字段名。")

    print("\n③ 不能放不可序列化的对象")
    print("   ❌ 数据库连接、文件句柄、锁、socket")
    print("   原因：checkpointer 要把 State 序列化存库，遇到这些直接失败。")
    print("   ✅ 正确做法：连接放在节点外部的模块级变量里，State 只存数据。")

    print("\n④ State 里放的东西会【每轮都传】")
    print("   如果你把整个 BOM 表（几万行）塞进 State，")
    print("   每次节点执行、每次 checkpointer 存快照，都要处理这几万行。")
    print("   ✅ 大数据放外部存储，State 里只放 id 或摘要。")

    print("\n⑤ 节点返回值必须是 dict，不能是 State 本身")
    print("   ❌ return state          ← 会把没改的字段也写一遍，可能触发 reducer 重复累加")
    print("   ✅ return {'log': [...]} ← 只返回要改的字段")

    print("\n⑥ 节点函数不能修改 state 里的对象")
    print("   ❌ state['log'].append('x')")
    print("   ✅ return {'log': state['log'] + ['x']}")
    print("   原因和自定义 reducer 一样：checkpointer 存的是快照，")
    print("   原地修改会让'旧快照'也跟着变，时间旅行就错了。")

    print("\n【一句话总结】")
    print("  State 要当成【不可变的纯数据】来对待：")
    print("  只放能序列化的、节点只返回补丁、不改原对象。")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], None]]] = [
    # ("1", "最小可用图", demo1_minimal_graph),
    # ("2", "默认行为是覆盖", demo2_default_overwrite),
    # ("3", "operator.add 累加", demo3_operator_add),
    ("4", "add_messages", demo4_add_messages),
    # ("5", "自定义 reducer", demo5_custom_reducer),
    # ("6", "哪些字段该加 reducer", demo6_which_fields_need_reducer),
    # ("7", "State 的六个坑", demo7_state_pitfalls),
]


def main() -> None:
    args = sys.argv[1:]
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print("2.1 State 与 Reducer（全部离线，不调模型）")
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
