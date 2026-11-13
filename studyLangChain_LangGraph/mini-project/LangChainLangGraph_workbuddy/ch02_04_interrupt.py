"""2.4 interrupt：人工介入与断点续跑（Human-in-the-Loop）

【跑这个文件能看到什么】
Demo 1  ★ 最小 interrupt：挂起 + 恢复的完整流程
Demo 2  ★★ 恢复时节点会【从头重跑】—— 最大的坑
Demo 3  ★ 完整审批流程：批准 / 驳回 两条路
Demo 4  interrupt 的返回值：bool / dict / str 都行
Demo 5  interrupt_before / interrupt_after：静态断点
Demo 6  不配 checkpointer 会直接报错
Demo 7  生产设计：审批接口该怎么写

【对应手册】Part 2 · 2.7 interrupt
【对应简历】"设计调查计划确认机制"、"审批检查点续跑，解决审批失效"
【面试高频】"当图运行到'工具执行节点'前会自动触发 interrupt 挂起并释放计算资源；
          待业务人员在前端确认后，后端通过 Command(resume=...) 唤醒该 thread_id
          从断点处继续往下执行。"

【怎么跑】
    cd studyLangChain_LangGraph/mini-project
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_04_interrupt.py

【全部离线，不调模型，秒出结果】
"""

import sys
from typing import Callable, TypedDict

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
# Demo 1 · 最小 interrupt
# ============================================================

class ApprovalState(TypedDict):
    plan: str
    approved: bool
    result: str


def demo1_minimal_interrupt() -> None:
    show_title("Demo 1 · 最小 interrupt：挂起 + 恢复（离线）")

    def plan_node(state: ApprovalState) -> dict:
        return {"plan": "第一步：查工单；第二步：查质检"}

    def review_node(state: ApprovalState) -> dict:
        # ★ 核心：interrupt() 会在这里把图挂起
        # 传给它的值会原样交给调用方（前端 / 命令行）
        decision = interrupt({
            "需要审批": state["plan"],
            "问题": "是否批准这个调查计划？",
        })
        # 下面这行只有在 resume 之后才会执行
        return {"approved": bool(decision)}

    def execute_node(state: ApprovalState) -> dict:
        if state["approved"]:
            return {"result": "已按计划执行"}
        return {"result": "计划被驳回，未执行"}

    builder = StateGraph(ApprovalState)
    builder.add_node("plan", plan_node)
    builder.add_node("review", review_node)
    builder.add_node("execute", execute_node)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "review")
    builder.add_edge("review", "execute")
    builder.add_edge("execute", END)

    # ★ 必须配 checkpointer，否则挂起后状态就丢了
    app = builder.compile(checkpointer=MemorySaver())

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {plan: '', approved: False, result: ''}",
            "plan": "生成调查计划",
            "review": "★ interrupt() 在这里挂起，等人工审批",
            "execute": "审批通过才执行",
            "END": "写回 result",
        },
        edge_notes={
            ("START", "plan"): ["普通边"],
            ("plan", "review"): ["普通边：进审批节点就挂起"],
            ("review", "execute"): ["resume 之后才继续"],
            ("execute", "END"): ["执行完结束"],
        },
        title="Demo 1 · 流程图（interrupt 挂起）",
    )
    config = {"configurable": {"thread_id": "approval-001"}}

    print("① 第一次 invoke：跑到 review 节点会挂起")
    result = app.invoke(
        {"plan": "", "approved": False, "result": ""},
        config,
    )
    print(f"   返回值 = {result}")
    print()
    print("   ← 注意返回值里有 __interrupt__ 这个键")
    print("     里面就是 interrupt() 传出来的值")

    print("\n② 查看挂起状态")
    snapshot = app.get_state(config)
    print(f"   .next       = {snapshot.next}")
    print("   ← ('review',) 表示停在 review 节点，还没执行完")
    print(f"   .interrupts = {snapshot.interrupts}")
    print(f"   .values     = {snapshot.values}")
    print("   ← values 里只有 plan，approved 还是初始值 False")
    print("     说明 review 节点【没有执行完】，卡在 interrupt 那一行")

    print("\n③ 用 Command(resume=True) 恢复执行")
    final = app.invoke(Command(resume=True), config)
    print(f"   返回值 = {final}")

    print("\n④ 恢复后的状态")
    final_snapshot = app.get_state(config)
    print(f"   .next = {final_snapshot.next}   ← 空元组，跑完了")

    print("\n【整个流程，三句话】")
    print("  1. 节点里调 interrupt(要给人看的数据) → 图挂起，进程可以释放")
    print("  2. 人工在前端看到数据，点了'批准'")
    print("  3. 后端调 invoke(Command(resume=批准结果), 同一个 thread_id) → 从断点继续")
    print("")
    print("  注意'释放计算资源'这句：挂起时 Python 进程可以直接退出，")
    print("  状态在数据库里。所以跨天审批也能续上 —— 这就是你简历里那句话的机制。")


# ============================================================
# Demo 2 · 最大的坑：恢复时节点重跑
# ============================================================

def demo2_node_reruns() -> None:
    show_title("Demo 2 · 恢复时节点会【从头重跑】（最大的坑）")

    # 用全局列表记录执行轨迹
    trace: list[str] = []

    class State(TypedDict):
        step: str

    def risky_node(state: State) -> dict:
        # 这行在挂起前执行一次，恢复后又执行一次！
        trace.append("① 节点开始执行")

        # 假设这里有个危险操作：发通知
        trace.append("② 准备发通知给车间主任（危险：会重复发）")

        decision = interrupt("请确认是否继续")
        trace.append(f"③ 恢复，拿到 {decision}")

        return {"step": "done"}

    builder = StateGraph(State)
    builder.add_node("risky", risky_node)
    builder.add_edge(START, "risky")
    builder.add_edge("risky", END)

    app = builder.compile(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "rerun-demo"}}

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {step: 'start'}",
            "risky": "★ 里面有 interrupt()，恢复时会【从头重跑】",
            "END": "step = 'done'",
        },
        edge_notes={
            ("START", "risky"): ["普通边"],
            ("risky", "END"): ["注意：resume 时整个 risky 节点会重新执行"],
        },
        title="Demo 2 · 流程图（节点重跑）",
    )

    print("① 第一次 invoke（挂起）")
    app.invoke({"step": "start"}, config)
    print("   执行轨迹：")
    for line in trace:
        print(f"     {line}")

    print("\n② Command(resume='ok') 恢复")
    trace.clear()
    app.invoke(Command(resume="ok"), config)
    print("   执行轨迹：")
    for line in trace:
        print(f"     {line}")

    print("\n【看到了吗】")
    print("   恢复后，'① 节点开始执行' 和 '② 准备发通知' 【又跑了一遍】！")
    print("   interrupt() 不是'暂停在这一行'，")
    print("   而是'整个节点函数从头再执行，走到 interrupt 时直接返回 resume 值'。")

    print("\n【为什么这么设计】")
    print("  图引擎没法'恢复一个函数的栈帧'（Python 做不到跨进程保存执行位置）。")
    print("  所以它的做法是：重新跑这个节点，")
    print("  但把 interrupt() 变成一个'直接返回结果'的普通调用。")
    print("")
    print("  这是权衡：实现简单、可跨进程，代价是节点内的代码会重跑。")

    print("\n【必须遵守的规则】")
    print("  ❌ interrupt() 之前不要放有副作用的操作：")
    print("     写数据库、发消息、调外部 API、累加计数器")
    print("  ✅ 副作用放在 interrupt() 之后，或者放在【独立的后续节点】里")
    print("")
    print("  正确结构：")
    print("     def review_node(state):")
    print("         decision = interrupt(...)     # 前面什么都不做")
    print("         return {'approved': decision} # 后面只改 State")
    print("     # 真正有副作用的操作放到下一个节点")
    print("     def execute_node(state):")
    print("         写数据库(...)")
    print("")
    print("  这样重跑 review_node 不会有任何副作用，")
    print("  而 execute_node 只在 resume 之后执行一次。")

    print("\n【第二个坑：interrupt 的 id 会变】")
    print("  同一个节点里如果有多个 interrupt()，")
    print("  靠调用顺序匹配 resume 值。所以不要在循环里调 interrupt()，")
    print("  否则恢复时匹配可能错位。")


# ============================================================
# Demo 3 · 完整审批流程（含驳回）
# ============================================================

def demo3_full_approval() -> None:
    show_title("Demo 3 · 完整审批流程：批准 / 驳回（离线）")

    trace: list[str] = []

    class State(TypedDict):
        batch_id: str
        plan: list[str]
        decision: str          # approved / rejected / modified
        final_plan: list[str]
        result: str

    def generate_plan(state: State) -> dict:
        """Agent 生成调查计划。真实场景这里调模型。"""
        trace.append("generate_plan")
        return {"plan": ["查工单", "查质检记录", "查设备参数"]}

    def human_review(state: State) -> dict:
        """人工审批节点：只做挂起，不做副作用。"""
        trace.append("human_review 开始")
        response = interrupt({
            "batch_id": state["batch_id"],
            "proposed_plan": state["plan"],
            "options": ["approved", "rejected", "modified"],
        })
        trace.append(f"human_review 恢复：{response}")

        # 支持三种返回：字符串 / dict（含修改后的计划）
        if isinstance(response, dict):
            return {
                "decision": response.get("decision", "modified"),
                "final_plan": response.get("plan", state["plan"]),
            }
        return {
            "decision": str(response),
            "final_plan": state["plan"],
        }

    def route_after_review(state: State) -> str:
        """条件边：批准才执行，驳回直接结束。"""
        if state["decision"] in ("approved", "modified"):
            return "execute"
        return "reject"

    def execute_plan(state: State) -> dict:
        """真正执行：这里才有副作用。"""
        trace.append("execute_plan")
        done = "；".join(state["final_plan"])
        return {"result": f"已执行：{done}"}

    def reject_node(state: State) -> dict:
        trace.append("reject")
        return {"result": "计划被驳回，已通知提交人"}

    builder = StateGraph(State)
    builder.add_node("generate_plan", generate_plan)
    builder.add_node("human_review", human_review)
    builder.add_node("execute", execute_plan)
    builder.add_node("reject", reject_node)

    builder.add_edge(START, "generate_plan")
    builder.add_edge("generate_plan", "human_review")
    builder.add_conditional_edges(
        "human_review",
        route_after_review,
        {"execute": "execute", "reject": "reject"},
    )
    builder.add_edge("execute", END)
    builder.add_edge("reject", END)

    app = builder.compile(checkpointer=MemorySaver())

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {batch_id, plan, decision, ...}",
            "generate_plan": "Agent 生成调查计划",
            "human_review": "★ interrupt() 等人工审批",
            "execute": "批准 / 修改后执行",
            "reject": "驳回，直接结束",
            "END": "写回 result",
        },
        branch_targets={"human_review": ["execute", "reject"]},
        title="Demo 3 · 流程图（审批分流）",
    )

    # ---------------- 场景 A：批准 ----------------
    print("=" * 72)
    print("场景 A：批准")
    print("=" * 72)
    trace.clear()
    config_a = {"configurable": {"thread_id": "batch-B002-approved"}}

    paused = app.invoke({
        "batch_id": "B002", "plan": [], "decision": "",
        "final_plan": [], "result": "",
    }, config_a)
    print(f"① 挂起，等待审批。提议的计划 = {paused['plan']}")

    snap = app.get_state(config_a)
    print(f"   .next = {snap.next}")
    print(f"   审批单内容 = {snap.interrupts[0].value if snap.interrupts else None}")

    final_a = app.invoke(Command(resume="approved"), config_a)
    print(f"\n② 批准后执行")
    print(f"   decision = {final_a['decision']}")
    print(f"   result   = {final_a['result']}")
    print(f"   轨迹     = {trace}")

    # ---------------- 场景 B：修改后执行 ----------------
    print()
    print("=" * 72)
    print("场景 B：人工修改计划后执行")
    print("=" * 72)
    trace.clear()
    config_b = {"configurable": {"thread_id": "batch-B002-modified"}}

    app.invoke({
        "batch_id": "B002", "plan": [], "decision": "",
        "final_plan": [], "result": "",
    }, config_b)

    final_b = app.invoke(
        Command(resume={
            "decision": "modified",
            "plan": ["查工单", "查质检记录"],     # 人工砍掉了"查设备参数"
        }),
        config_b,
    )
    print(f"① 修改后执行")
    print(f"   decision   = {final_b['decision']}")
    print(f"   final_plan = {final_b['final_plan']}")
    print(f"   result     = {final_b['result']}")
    print("   ← 人工删掉了'查设备参数'，执行的是修改后的计划")

    # ---------------- 场景 C：驳回 ----------------
    print()
    print("=" * 72)
    print("场景 C：驳回")
    print("=" * 72)
    trace.clear()
    config_c = {"configurable": {"thread_id": "batch-B002-rejected"}}

    app.invoke({
        "batch_id": "B002", "plan": [], "decision": "",
        "final_plan": [], "result": "",
    }, config_c)

    final_c = app.invoke(Command(resume="rejected"), config_c)
    print(f"① 驳回")
    print(f"   decision = {final_c['decision']}")
    print(f"   result   = {final_c['result']}")
    print(f"   轨迹     = {trace}")
    print("   ← 直接走 reject 分支，execute 节点根本没执行")

    print("\n【这个结构就是简历里那句话的完整实现】")
    print("  generate_plan → human_review(interrupt) → 条件边 → execute / reject")
    print("")
    print("  三个设计要点：")
    print("  1. human_review 节点【只做挂起和改 State】，没有任何副作用")
    print("  2. 条件边按 decision 分流，驳回不进 execute")
    print("  3. execute 节点里才写库 —— 它只在 resume 之后执行一次")


# ============================================================
# Demo 4 · interrupt 的返回值形态
# ============================================================

def demo4_resume_value_types() -> None:
    show_title("Demo 4 · interrupt 的返回值：三种形态（离线）")

    class State(TypedDict):
        received: str

    def node(state: State) -> dict:
        value = interrupt("请给个值")
        return {"received": f"{type(value).__name__}: {value!r}"}

    builder = StateGraph(State)
    builder.add_node("n", node)
    builder.add_edge(START, "n")
    builder.add_edge("n", END)
    app = builder.compile(checkpointer=MemorySaver())

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {received: ''}",
            "n": "拿到 resume 的值，写进 received",
            "END": "received 里是值的类型和内容",
        },
        edge_notes={
            ("START", "n"): ["进入节点后 interrupt() 挂起"],
            ("n", "END"): ["Command(resume=任意值) 恢复"],
        },
        title="Demo 4 · 流程图",
    )

    cases = [
        ("bool", True),
        ("str", "approved"),
        ("dict", {"decision": "modified", "plan": ["查工单"]}),
        ("list", ["a", "b"]),
        ("int", 42),
    ]

    print("① resume 可以传任何可序列化的值\n")
    for i, (label, value) in enumerate(cases):
        config = {"configurable": {"thread_id": f"type-{i}"}}
        app.invoke({"received": ""}, config)
        result = app.invoke(Command(resume=value), config)
        print(f"   传 {label:6} → 节点收到 {result['received']}")

    print("\n② 实践建议")
    print("  简单确认（批准/拒绝）→ bool 或 'approved'/'rejected' 字符串")
    print("  带修改内容           → dict，语义最清楚")
    print("  不建议用位置参数式的裸值（如直接传 True），")
    print("  因为半年后回看代码，没人知道 True 代表什么。")
    print("")
    print("  推荐统一格式：")
    print("      Command(resume={'decision': 'approved', 'note': '...'})")

    print("\n③ 坑：resume 的值必须能序列化")
    print("  传自定义对象会失败（checkpointer 要存进数据库）。")
    print("  只传 dict / list / str / int / bool / None。")


# ============================================================
# Demo 5 · 静态断点 interrupt_before / after
# ============================================================

def demo5_static_breakpoints() -> None:
    show_title("Demo 5 · 静态断点：interrupt_before / after（离线）")

    trace: list[str] = []

    class State(TypedDict):
        step: str

    def step_one(state: State) -> dict:
        trace.append("one")
        return {"step": "one done"}

    def step_two(state: State) -> dict:
        trace.append("two")
        return {"step": "two done"}

    builder = StateGraph(State)
    builder.add_node("one", step_one)
    builder.add_node("two", step_two)
    builder.add_edge(START, "one")
    builder.add_edge("one", "two")
    builder.add_edge("two", END)

    # ★ 编译时指定：执行 two 之前先挂起
    app = builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["two"],       # 执行 two 之前挂起
    )

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {step: ''}",
            "one": "正常执行",
            "two": "★ interrupt_before=['two'] → 进这个节点前挂起",
            "END": "恢复后跑完",
        },
        edge_notes={
            ("START", "one"): ["普通边"],
            ("one", "two"): ["这里被静态断点拦住"],
            ("two", "END"): ["invoke(None) 恢复后执行"],
        },
        title="Demo 5 · 流程图（静态断点）",
    )
    config = {"configurable": {"thread_id": "static-bp"}}

    print("① interrupt_before=['two']：执行 two 之前挂起")
    app.invoke({"step": ""}, config)
    print(f"   轨迹 = {trace}")
    print("   ← 只跑了 one，two 没跑")

    snap = app.get_state(config)
    print(f"   .next = {snap.next}")
    print("   ← ('two',) 表示下一步要执行 two，但被拦住了")

    print("\n② 恢复（这次不用 Command(resume)，直接 invoke(None)）")
    trace.clear()
    app.invoke(None, config)
    print(f"   轨迹 = {trace}")
    print("   ← two 执行了")

    print("\n③ 两种方式对比")
    print("   interrupt()（动态）")
    print("     - 写在节点内部，可以带数据给前端")
    print("     - 可以有条件地挂起（if 某些情况才 interrupt）")
    print("     - 恢复时用 Command(resume=值)")
    print("     - 适用：审批、需要人工填数据")
    print("")
    print("   interrupt_before / after（静态）")
    print("     - 编译时声明，无条件挂起")
    print("     - 不带数据")
    print("     - 恢复时用 invoke(None)")
    print("     - 适用：调试单步执行、简单的'暂停一下'")
    print("")
    print("  生产上审批场景一律用 interrupt()，因为要传审批内容给前端。")

    print("\n④ interrupt_after 同理")
    print("   compile(interrupt_after=['one'])  → one 执行完挂起")


# ============================================================
# Demo 6 · 不配 checkpointer 会怎样
# ============================================================

def demo6_requires_checkpointer() -> None:
    show_title("Demo 6 · 不配 checkpointer 会直接报错（离线）")

    class State(TypedDict):
        x: str

    def node(state: State) -> dict:
        value = interrupt("停一下")
        return {"x": str(value)}

    builder = StateGraph(State)
    builder.add_node("n", node)
    builder.add_edge(START, "n")
    builder.add_edge("n", END)

    print("① 编译时不传 checkpointer")
    app_no_cp = builder.compile()

    draw_flow(
        app_no_cp,
        node_notes={
            "START": "初始 State = {x: ''}",
            "n": "★ 有 interrupt()，不配 checkpointer 会直接报错",
            "END": "恢复后写入 x",
        },
        edge_notes={
            ("START", "n"): ["普通边"],
            ("n", "END"): ["interrupt 必须能存快照才能恢复"],
        },
        title="Demo 6 · 流程图（缺 checkpointer）",
    )

    print("② 尝试 invoke")
    try:
        app_no_cp.invoke({"x": ""})
        print("   没报错？")
    except Exception as e:
        print(f"   {type(e).__name__}")
        for line in str(e).splitlines()[:4]:
            print(f"   {line}")
        print()
        print("   ← interrupt 必须配 checkpointer，")
        print("     因为挂起时要把 State 存下来，否则恢复时没东西可恢复。")

    print("\n③ 正确写法")
    app_with_cp = builder.compile(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "need-cp"}}
    app_with_cp.invoke({"x": ""}, config)
    print("   挂起成功")
    result = app_with_cp.invoke(Command(resume="继续"), config)
    print(f"   恢复成功，结果 = {result}")


# ============================================================
# Demo 7 · 生产设计
# ============================================================

def demo7_production_design() -> None:
    show_title("Demo 7 · 生产设计：审批接口怎么写（离线）")

    print("① 后端接口设计（三个接口）")
    print()
    print("   POST /api/analyze")
    print("     入参：{batch_id: 'B002'}")
    print("     逻辑：起一个图，跑到 interrupt 就停")
    print("     返回：{thread_id: 'xxx', status: 'pending_review',")
    print("            plan: [...], interrupt_id: '...'}")
    print()
    print("   GET /api/analyze/{thread_id}")
    print("     逻辑：app.get_state(config)")
    print("     返回：{status, next_node, values, interrupts}")
    print("     用途：前端轮询，或者用户刷新页面后恢复现场")
    print()
    print("   POST /api/analyze/{thread_id}/review")
    print("     入参：{decision: 'approved', note: '...', plan: [...]}")
    print("     逻辑：app.invoke(Command(resume=decision), config)")
    print("     返回：最终结果，或者下一个 interrupt")

    print("\n② 四个必须处理的边界")
    print()
    print("   (1) 重复提交")
    print("       用户连点两次'批准'，会 resume 两次。")
    print("       第二次时图已经跑完，resume 会报错或产生脏数据。")
    print("       解决：resume 前先查 get_state().next，")
    print("             如果为空说明已跑完，直接返回上次结果。")
    print()
    print("   (2) 审批超时")
    print("       挂了三天没人审。")
    print("       解决：给 thread 加超时标记，定时任务扫描后")
    print("             自动 resume 成 'rejected'，或者发提醒。")
    print()
    print("   (3) 权限")
    print("       谁能审批？必须校验 —— 不能只凭 thread_id 就放行。")
    print("       审批人身份要写进 State，事后能追溯是谁批的。")
    print()
    print("   (4) 并发")
    print("       两个人同时审同一单。")
    print("       解决：审批接口加乐观锁（State 里存 version），")
    print("             或者用 Redis 分布式锁按 thread_id 加锁。")

    print("\n③ 审计要记什么")
    print("   - thread_id、batch_id")
    print("   - 谁审的、什么时候、审的哪一版计划")
    print("   - 批准 / 驳回 / 修改成什么")
    print("   - 最终执行了什么")
    print("")
    print("  这些不能只放在 State 里 —— State 会被后续步骤覆盖。")
    print("  要单独写一张审批流水表，只追加不修改。")

    print("\n【面试话术】")
    print("  '审批用 interrupt 实现：图跑到 human_review 节点挂起，")
    print("   State 快照按 thread_id 落库，进程可以释放。")
    print("   前端拿到 interrupt 里的计划内容展示给工程师，")
    print("   确认后调 resume 接口带 decision 恢复执行。")
    print("   有三个细节：审批节点里不写副作用（因为 resume 会重跑该节点），")
    print("   重复提交要查 next 幂等，审批流水单独落表做审计。'")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], None]]] = [
    # ("1", "最小 interrupt", demo1_minimal_interrupt),
    # ("2", "恢复时节点重跑", demo2_node_reruns),
    # ("3", "完整审批流程", demo3_full_approval),
    # ("4", "resume 值的三种形态", demo4_resume_value_types),
    # ("5", "静态断点", demo5_static_breakpoints),
    ("6", "必须配 checkpointer", demo6_requires_checkpointer),
    # ("7", "生产设计", demo7_production_design),
]


def main() -> None:
    args = sys.argv[1:]
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print("2.4 interrupt 人工介入（全部离线，不调模型）")
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
