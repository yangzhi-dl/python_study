"""2.3 Checkpointer：持久化与多轮对话

【跑这个文件能看到什么】
Demo 1  ★ 没有 checkpointer：每次 invoke 都是全新会话（对照实验）
Demo 2  ★ 加 checkpointer + thread_id：真正的多轮对话
Demo 3  thread_id 隔离：不同会话互不干扰
Demo 4  get_state：查看当前状态快照
Demo 5  get_state_history：时间旅行，看每一步快照
Demo 6  update_state：手工改状态（"改上一条消息"怎么实现）
Demo 7  生产提醒：MemorySaver 只能用于开发

【对应手册】Part 2 · 2.6 Checkpointer
【对应简历】"MySQL 持久化 Agent 状态与审批检查点"
【面试高频】"图引擎每执行完一个 Node（super-step），Checkpointer 就会自动
          把当前 State 快照序列化落库并绑定 thread_id。"
          —— 这句话能说出来，说明真理解了机制。

【怎么跑】
    cd studyLangChain_LangGraph/mini-project
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_03_checkpointer.py
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch02_03_checkpointer.py --offline
"""

import os
import sys
from pathlib import Path
from typing import Annotated, Callable, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

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
# 二、共用的图定义
#
# 一个最简单的聊天图：收到消息 → 模型回复 → 结束
# ============================================================

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]


def chat_node(state: ChatState) -> dict:
    """调模型回复。"""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def build_chat_graph(checkpointer=None, show=False):
    """建一个聊天图，可选是否带 checkpointer。"""
    builder = StateGraph(ChatState)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    app = builder.compile(checkpointer=checkpointer)

    if show:
        draw_flow(
            app,
            node_notes={
                "START": "invoke 传进来的 messages",
                "chat": "调模型，return {'messages': [AIMessage]}",
                "END": "messages 里多了模型回复",
            },
            edge_notes={
                ("START", "chat"): [
                    "有 checkpointer：先按 thread_id 取回旧 State",
                    "再把这次的 messages 合并进去（走 add_messages）",
                ],
                ("chat", "END"): [
                    "模型回复追加进 messages",
                ],
            },
            title="聊天图的流程图",
        )
    return app

#系统提示词
SYSTEM = SystemMessage(
    content="你是产线质量助手。回答简洁，20 字以内。记住用户告诉你的信息。"
)


# ============================================================
# Demo 1 · 没有 checkpointer 的后果
# ============================================================

def demo1_without_checkpointer() -> None:
    show_title("Demo 1 · 没有 checkpointer：每次都是全新会话")

    app = build_chat_graph()      # 注意：没传 checkpointer

    print("① 第一轮：告诉它名字")
    r1 = app.invoke({
        "messages": [SYSTEM, HumanMessage(content="我叫 Ember，记一下。")]
    })
    print(f"   模型回复：{r1['messages'][-1].text}")
    print(f"   State 里 messages 共 {len(r1['messages'])} 条")

    print("\n② 第二轮：问它名字")
    r2 = app.invoke({
        "messages": [SYSTEM, HumanMessage(content="我叫什么？")]
    })
    print(f"   模型回复：{r2['messages'][-1].text}")
    print(f"   State 里 messages 共 {len(r2['messages'])} 条")

    print("\n【看到了吗】")
    print("  第二轮只有 3 条消息（system + 你的问题 + 回复），")
    print("  第一轮那两条完全不见了。")
    print("  模型不知道你叫什么 —— 因为每次 invoke 都是一个全新的 State。")

    print("\n【本质】")
    print("  invoke 结束 → State 就丢了。")
    print("  LangGraph 不会自动保存任何东西，除非你给它一个 checkpointer。")
    print("")
    print("  这就是 1.2 讲的'模型无状态'在图层面的体现：")
    print("  1.2 是你手动维护 messages 列表，")
    print("  这里是把维护工作交给 checkpointer。")


# ============================================================
# Demo 2 · 加 checkpointer
# ============================================================

def demo2_with_checkpointer() -> None:
    show_title("Demo 2 · 加 checkpointer + thread_id：真正的多轮对话")

    saver = MemorySaver()
    app = build_chat_graph(checkpointer=saver, show=True)

    # 关键：config 里必须有 thread_id
    config = {"configurable": {"thread_id": "session-ember-001"}}
    print(f"① 会话标识 thread_id = {config['configurable']['thread_id']}")

    print("\n② 第一轮：告诉它名字")
    r1 = app.invoke(
        {"messages": [SYSTEM, HumanMessage(content="我叫 Ember，记一下。")]},
        config,
    )
    print(f"   模型回复：{r1['messages'][-1].text}")
    print(f"   messages 共 {len(r1['messages'])} 条")

    print("\n③ 第二轮：问它名字（注意：这次只传新消息）")
    r2 = app.invoke(
        {"messages": [HumanMessage(content="我叫什么？")]},
        config,
    )
    print(f"   模型回复：{r2['messages'][-1].text}")
    print(f"   messages 共 {len(r2['messages'])} 条")

    print("\n④ 第三轮：再问一句")
    r3 = app.invoke(
        {"messages": [HumanMessage(content="我刚才问了什么？")]},
        config,
    )
    print(f"   模型回复：{r3['messages'][-1].text}")
    print(f"   messages 共 {len(r3['messages'])} 条")

    print("\n【关键差异】")
    print("  Demo 1 每次 invoke 都要传完整的 messages 列表（1.2 的做法）")
    print("  Demo 2 只传新消息，历史由 checkpointer 自动恢复")
    print("")
    print("  而且 messages 是【累加】的（含 system，所以是 3 → 5 → 7 条）。")
    print("  为什么能累加？因为 State 里 messages 有 add_messages reducer，")
    print("  恢复出来的旧 messages + 你新传的 = 合并后的完整列表。")

    print("\n【机制，面试就答这段】")
    print("  1. 图每执行完一个 super-step，checkpointer 就把当前 State 存一份快照")
    print("  2. 快照和 thread_id 绑定，存进 MemorySaver（内存字典）")
    print("  3. 下次同 thread_id 的 invoke，先按 thread_id 取出最后一个快照")
    print("  4. 用快照的 State 作为起点，再把新输入合并进去（走 reducer）")
    print("  5. 继续执行")
    print("")
    print("  所以'多轮对话'的本质不是模型有记忆，")
    print("  是 checkpointer 帮你把历史 State 存下来又恢复出来。")


# ============================================================
# Demo 3 · thread_id 隔离
# ============================================================

def demo3_thread_isolation() -> None:
    show_title("Demo 3 · thread_id 隔离：不同会话互不干扰")

    saver = MemorySaver()
    app = build_chat_graph(checkpointer=saver)

    config_a = {"configurable": {"thread_id": "user-ember"}}
    config_b = {"configurable": {"thread_id": "user-alice"}}

    print("① Ember 的会话里说名字")
    app.invoke(
        {"messages": [SYSTEM, HumanMessage(content="我叫 Ember。")]},
        config_a,
    )
    print("   已写入 thread_id='user-ember'")

    print("\n② Alice 的会话里问名字")
    r_b = app.invoke(
        {"messages": [SYSTEM, HumanMessage(content="我叫什么？")]},
        config_b,
    )
    print(f"   模型回复：{r_b['messages'][-1].text}")
    print("   ← 它不知道，因为这是另一个 thread，看不到 Ember 的会话")

    print("\n③ Ember 的会话里再问一次")
    r_a = app.invoke(
        {"messages": [HumanMessage(content="我叫什么？")]},
        config_a,
    )
    print(f"   模型回复：{r_a['messages'][-1].text}")
    print("   ← 它知道，因为同一个 thread")

    print("\n④ 两个 thread 的消息数对比")
    state_a = app.get_state(config_a)
    state_b = app.get_state(config_b)
    print(f"   user-ember: {len(state_a.values['messages'])} 条")
    print(f"   user-alice: {len(state_b.values['messages'])} 条")

    print("\n【thread_id 怎么设计】")
    print("  它就是你业务上的'会话 id'，常见方案：")
    print("    f'user-{user_id}-chat-{chat_id}'    多轮对话")
    print("    f'batch-{batch_id}-analysis'        按批次追溯（一个批次一条会话）")
    print("    f'ticket-{ticket_id}'               按工单")
    print("")
    print("  关键原则：")
    print("  1. 一个用户一次对话 = 一个 thread_id，不要复用")
    print("  2. thread_id 要能反查出业务对象，出问题时才好排查")
    print("  3. 不要用自增数字，用业务 id 或 uuid")

    print("\n【坑】忘记传 thread_id 会直接报错")
    print("   编译时传了 checkpointer，invoke 时就必须给 config。")
    print("   报错：Checkpointer requires one or more of the following")
    print("         configurable keys: thread_id, checkpoint_ns, checkpoint_id")


# ============================================================
# Demo 4 · get_state
# ============================================================

def demo4_get_state() -> None:
    show_title("Demo 4 · get_state：查看当前状态快照")

    saver = MemorySaver()
    app = build_chat_graph(checkpointer=saver, show=True)
    config = {"configurable": {"thread_id": "demo-get-state"}}

    app.invoke(
        {"messages": [SYSTEM, HumanMessage(content="3号线昨天有几个批次？")]},
        config,
    )

    snapshot = app.get_state(config)

    print(f"① 返回类型 = {type(snapshot).__name__}")
    print("\n② 七个字段")
    print("   .values        → 当前 State 的内容（你要的答案在这）")
    print("   .next          → 下一步要执行的节点，空元组 () 表示已结束")
    print("   .config        → 这份快照的完整配置（含 checkpoint_id）")
    print("   .metadata      → 执行信息（source / step / parents）")
    print("   .created_at    → 创建时间")
    print("   .parent_config → 上一份快照的 config（时间旅行用）")
    print("   .tasks         → 待执行任务列表")
    print("   .interrupts    → 中断信息（2.4 会讲）")

    print("\n③ 实际值")
    print(f"   .next        = {snapshot.next}   ← 空表示图已跑完")
    print(f"   .metadata    = {snapshot.metadata}")
    print(f"   .created_at  = {snapshot.created_at}")
    print(f"   .values 的字段 = {list(snapshot.values.keys())}")
    print(f"   messages 条数 = {len(snapshot.values['messages'])}")

    print("\n④ .next 最有用：判断图停在哪")
    print("   ()              → 正常跑完了")
    print("   ('tools',)      → 停在 tools 节点前（可能是 interrupt 挂起）")
    print("   ('human_review',) → 等人工审批")

    print("\n【生产用途】")
    print("  1. 接口返回进度：'当前在 execute 节点，等待审批'")
    print("  2. 断点续跑：服务重启后，按 thread_id 查 .next 看该从哪继续")
    print("  3. 排查卡死：图不动了，查 .next 卡在哪个节点")


# ============================================================
# Demo 5 · get_state_history（时间旅行）
# ============================================================

def demo5_state_history() -> None:
    show_title("Demo 5 · get_state_history：时间旅行（离线）")

    # 用纯离线图，跑得快，快照更清晰
    class CountState(TypedDict):
        count: int
        log: Annotated[list[str], lambda l, r: (l or []) + r]

    def step_one(state: CountState) -> dict:
        return {"count": state["count"] + 1, "log": ["step_one"]}

    def step_two(state: CountState) -> dict:
        return {"count": state["count"] + 10, "log": ["step_two"]}

    def step_three(state: CountState) -> dict:
        return {"count": state["count"] + 100, "log": ["step_three"]}

    builder = StateGraph(CountState)
    builder.add_node("one", step_one)
    builder.add_node("two", step_two)
    builder.add_node("three", step_three)
    builder.add_edge(START, "one")
    builder.add_edge("one", "two")
    builder.add_edge("two", "three")
    builder.add_edge("three", END)

    saver = MemorySaver()
    app = builder.compile(checkpointer=saver)

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {count: 0, log: []}",
            "one": "count +1，每个 super-step 存一份快照",
            "two": "count +10",
            "three": "count +100",
            "END": "一共 5 份快照（含虚拟的 __start__）",
        },
        edge_notes={
            ("START", "one"): ["快照 1：next=('__start__',)"],
            ("one", "two"): ["快照 2：next=('two',)"],
            ("two", "three"): ["快照 3：next=('three',)"],
            ("three", "END"): ["快照 4/5：next=()，结束"],
        },
        title="Demo 5 · 流程图（3 个节点产生 5 份快照）",
    )

    config = {"configurable": {"thread_id": "history-demo"}}

    app.invoke({"count": 0, "log": []}, config)

    history = list(app.get_state_history(config))

    print(f"① 一共产生 {len(history)} 份快照")
    print("   为什么是 5 份而不是 3 份（只有 3 个节点）：")
    print("   每执行完一个 super-step 就存一份，包括虚拟的 __start__：")
    print("     next=('__start__',)  还没开始")
    print("     next=('one',)        start 执行完")
    print("     next=('two',)        one 执行完")
    print("     next=('three',)      two 执行完")
    print("     next=()              three 执行完，图结束\n")

    print("② 按时间倒序（最新的在前）")
    for i, snap in enumerate(history):
        count = snap.values.get("count", "-")
        log = snap.values.get("log", [])
        next_node = snap.next if snap.next else "结束"
        print(f"   [{i}] count={count:>4}  log={len(log)} 条  next={next_node}")

    print("\n③ 怎么用：回滚到某一步")
    print("   每份快照的 .config 里有 checkpoint_id，")
    print("   拿它当 config 再 invoke，就是从那个点继续：")
    print()
    target = history[3] if len(history) > 3 else history[-1]
    print(f"   target_config = history[3].config")
    print(f"   这份快照的 count = {target.values.get('count')}")
    print(f"   next = {target.next}")
    print()
    print("   app.invoke(None, target.config)   ← 从这点重跑")

    print("\n【真实用途】")
    print("  1. 调试：'模型第 3 步就答错了'，回滚到第 3 步重跑，")
    print("     不用从头再花一遍 token")
    print("  2. 分支对比：同一份快照，用两种不同的 prompt 各跑一次，比较结果")
    print("  3. 审计：完整还原'当时 Agent 每一步看到了什么'")
    print("")
    print("  第 3 点在制造业场景是硬需求 —— 出了问题要能复现。")


# ============================================================
# Demo 6 · update_state
# ============================================================

def demo6_update_state() -> None:
    show_title("Demo 6 · update_state：手工改状态（离线）")

    class State(TypedDict):
        messages: Annotated[list, add_messages]
        approved: bool

    def echo_node(state: State) -> dict:
        # 只读 approved，不做任何修改
        return {"messages": [HumanMessage(content=f"当前 approved={state['approved']}")]}

    builder = StateGraph(State)
    builder.add_node("echo", echo_node)
    builder.add_edge(START, "echo")
    builder.add_edge("echo", END)

    saver = MemorySaver()
    app = builder.compile(checkpointer=saver)

    draw_flow(
        app,
        node_notes={
            "START": "初始 State = {messages: [...], approved: False}",
            "echo": "只读 approved，不改它",
            "END": "update_state 可以在两步之间手工改 State",
        },
        edge_notes={
            ("START", "echo"): ["messages 有 reducer → 追加"],
            ("echo", "END"): ["approved 无 reducer → 直接覆盖"],
        },
        title="Demo 6 · 流程图（update_state 改的是这份 State）",
    )

    config = {"configurable": {"thread_id": "update-demo"}}

    app.invoke(
        {"messages": [HumanMessage(content="初始")], "approved": False},
        config,
    )
    print(f"① 初始状态 approved = {app.get_state(config).values['approved']}")

    # 手工改成 True
    app.update_state(config, {"approved": True})
    print(f"② update_state 后 approved = {app.get_state(config).values['approved']}")

    print("\n③ update_state 会走 reducer")
    # messages 有 add_messages reducer，所以这里是【追加】不是替换
    before = len(app.get_state(config).values["messages"])
    app.update_state(config, {"messages": [HumanMessage(content="人工插入的一条")]})
    after = len(app.get_state(config).values["messages"])
    print(f"   追加前 {before} 条 → 追加后 {after} 条")

    print("\n【三个真实用途】")
    print("  1. 人工修正：Agent 答错了，人工改一条消息再继续（走 reducer 是追加）")
    print("  2. 注入上下文：审批时人工补充'这批已确认是来料问题'，塞进 State")
    print("  3. 覆盖字段：直接把 approved 改成 True，跳过审批")

    print("\n【坑】update_state 不是'替换整个 State'")
    print("   它是'合并补丁'，走的是每个字段的 reducer：")
    print("     有 reducer 的字段 → 按 reducer 规则合并（messages 是追加）")
    print("     没 reducer 的字段 → 直接覆盖")
    print("")
    print("   想替换 messages 全部内容，得用 update_state 的 as_node 参数")
    print("   或先清空再写，别指望它自动清空。")


# ============================================================
# Demo 7 · 生产提醒
# ============================================================

def demo7_production_notes() -> None:
    show_title("Demo 7 · 生产提醒：MemorySaver 只能开发用（离线）")

    print("① MemorySaver 存在哪")
    print("   内存里的 Python 字典。")
    print("   进程一退出，全部消失。")
    print("   多进程部署时，A 进程存的快照 B 进程读不到。")
    print("")
    print("   所以它只能用于：本地开发、单元测试、demo。")

    print("\n② 生产要换什么")
    print("   官方提供（需要额外装包）：")
    print("     langgraph-checkpoint-sqlite    → SqliteSaver（单机小项目够用）")
    print("     langgraph-checkpoint-postgres  → PostgresSaver（生产推荐）")
    print("   社区实现：")
    print("     MySQL / Redis 的 saver（要自己实现 BaseCheckpointSaver 接口）")

    print("\n③ 换 saver 的代码改动极小")
    print("   开发：")
    print("       from langgraph.checkpoint.memory import MemorySaver")
    print("       saver = MemorySaver()")
    print("   生产：")
    print("       from langgraph.checkpoint.postgres import PostgresSaver")
    print("       saver = PostgresSaver.from_conn_string(DB_URL)")
    print("       saver.setup()      # 首次要建表")
    print("   compile(checkpointer=saver) 这行不用改。")
    print("")
    print("   这是接口抽象的好处 —— 你简历里'MySQL 持久化'就是这么做的：")
    print("   实现 BaseCheckpointSaver 接口，底层换成 MySQL。")

    print("\n④ 三个生产必须考虑的点")
    print("   (1) 快照体积")
    print("       State 里 messages 越攒越多，每份快照都存全量。")
    print("       长会话要配合'上下文裁剪'（模块 E 场景 4），否则表会爆。")
    print()
    print("   (2) 清理策略")
    print("       不是所有 thread 都要永久保留。")
    print("       按业务定 TTL：聊天 7 天、追溯分析 90 天（合规要求）。")
    print()
    print("   (3) 敏感数据")
    print("       快照里会有完整对话，可能含工艺参数、客户信息。")
    print("       落库前要考虑脱敏，或者加密存储。")

    print("\n【面试话术】")
    print("  '开发阶段用 MemorySaver，生产换成基于 MySQL 的 saver，")
    print("   实现 BaseCheckpointSaver 接口。图引擎每执行完一个 super-step")
    print("   自动落一份 State 快照，按 thread_id 绑定，")
    print("   服务重启或跨天审批时，传同一个 thread_id 就能原地恢复上下文。'")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], None], bool]] = [
    # ("1", "没有 checkpointer 的后果", demo1_without_checkpointer, True),
    # ("2", "加 checkpointer 多轮对话", demo2_with_checkpointer, True),
    # ("3", "thread_id 隔离", demo3_thread_isolation, True),
    # ("4", "get_state", demo4_get_state, True),
    # ("5", "get_state_history 时间旅行", demo5_state_history, False),
    # ("6", "update_state", demo6_update_state, False),
    ("7", "生产提醒", demo7_production_notes, False),
]


def main() -> None:
    args = sys.argv[1:]
    offline_only = "--offline" in args
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print(f"2.3 Checkpointer | 模型 = {MODEL_CODE}")
    if offline_only:
        print("模式：--offline（只跑 Demo 5/6/7）")
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
