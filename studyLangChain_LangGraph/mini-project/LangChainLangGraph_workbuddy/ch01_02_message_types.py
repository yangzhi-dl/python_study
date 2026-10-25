"""1.2 消息类型（Messages）

【跑这个文件能看到什么】
Demo 1  四种消息类型 system / human / ai / tool，各自有哪些字段
Demo 2  dict 简写 和 消息对象，两种写法怎么互转、能力差在哪
Demo 3  content 不只是字符串，还可以是"内容块列表"
Demo 4  多轮对话的本质：模型没有记忆，历史全靠你传
Demo 5  模型返回的 AIMessage 里，除了 content 还有什么（token 用量、元数据）
Demo 6  流式返回的是 AIMessageChunk，可以相加拼成完整消息

【对应手册】Part 1 · 1.2 消息类型

【怎么跑】
    cd studyLangChain_LangGraph/mini-project

    # 全部跑（会调模型约 6 次）
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_02_message_types.py

    # 只跑完全离线的 Demo 1（秒出结果、不花钱）
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_02_message_types.py --offline

    # 只跑指定 Demo
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_02_message_types.py 4

【跑之前确认】
    .env 在 mini-project/ 下，含 DASHSCOPE_API_KEY / BASE_URL / MODEL_CODE
"""

import os
import sys
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    convert_to_messages,
)
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
# 和 1.1 完全一样，不重复解释。
# ============================================================

llm_kwargs: dict = {
    "model": MODEL_CODE,
    "api_key": API_KEY,
    "temperature": 0,
}
if BASE_URL:
    llm_kwargs["base_url"] = BASE_URL

llm = ChatOpenAI(**llm_kwargs)


def show_title(title: str) -> None:
    """打印一个醒目的分隔标题，方便在长输出里定位。"""
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ============================================================
# Demo 1 · 四种消息类型
#
# 这一节全部离线，不调模型。目的是让你看清"对象里到底存了什么"。
# ============================================================

def demo1_four_message_types() -> None:
    show_title("Demo 1 · 四种消息类型（离线，不调模型）")

    # ① system：给模型的角色设定和规则。一次对话通常只有一条，放最前面
    system_msg = SystemMessage(
        content="你是不良品根因分析助手，回答必须基于查询到的数据，不要猜测。"
    )

    # ② human：用户说的话。name 和 id 都是可选的
    human_msg = HumanMessage(
        content="3号线昨天的不良原因是什么？",
        name="ember",           # 可选：多用户场景下区分是谁说的
        id="msg-h-001",         # 可选：消息唯一 id，做追踪/去重时有用
    )

    # ③ ai：模型说的话。注意 tool_calls —— 模型"想调工具"时，内容在这里
    ai_msg = AIMessage(
        content="我先查一下 3号线 昨天的工单。",
        tool_calls=[
            {
                "name": "query_workorder",
                "args": {"line": "3号线", "date": "2026-10-24"},
                "id": "call-abc123",
            }
        ],
    )

    # ④ tool：工具执行完的结果，回填给模型。
    #    必须带 tool_call_id，而且要等于上面 AIMessage 里那个 tool_calls 的 id
    tool_msg = ToolMessage(
        content=(
            "3号线 2026-10-24 共 5 个批次："
            "B001 正常 / B002 异常 / B003 异常 / B004 正常 / B005 异常"
        ),
        tool_call_id="call-abc123",
        name="query_workorder",
    )

    all_messages = [system_msg, human_msg, ai_msg, tool_msg] #四种消息

    for msg in all_messages:
        print(f"\n--- {type(msg).__name__} ---")
        print(f"  .type    = {msg.type!r}")
        print(f"  .content = {msg.content!r}")
        print(f"  .text    = {msg.text!r}")
        print(f"  .id      = {msg.id!r}")
        print(f"  .name    = {msg.name!r}")

    print("\n--- AIMessage 额外字段 ---")
    print(f"  .tool_calls = {ai_msg.tool_calls}")#tool_calls 是自动补的

    print("\n【关键点 1】.type 的取值和 API 的 role 不是一套词")
    print("  SystemMessage → type='system'   API role='system'")
    print("  HumanMessage  → type='human'    API role='user'        ← 不一致！")
    print("  AIMessage     → type='ai'       API role='assistant'   ← 不一致！")
    print("  ToolMessage   → type='tool'     API role='tool'")
    print("  记忆法：.type 是 LangChain 内部的叫法，role 是 OpenAI 协议的叫法，")
    print("         两边转换由 langchain_openai 自动完成，你只需要用对类。")

    print("\n【关键点 2】tool_calls 里的 type 字段是自动补的")
    print("  你只传了 name / args / id，读出来却多了 type='tool_call'。")
    print("  别手动去写它，也别被它吓到。")

    print("\n【关键点 3】ToolMessage 的 tool_call_id 必须和 AIMessage 对上")
    print("  对不上会报错，或者模型收到结果后不知道为什么会有这条结果。")
    print("  这是手写工具循环（阶段 3）最容易错的地方。")


# ============================================================
# Demo 2 · dict 简写 vs 消息对象
# ============================================================

def demo2_dict_vs_object() -> None:
    show_title("Demo 2 · dict 简写 vs 消息对象")

    question = "回流焊峰值温度偏低，通常会导致什么焊接缺陷？"

    # ---------------- 写法 A：dict 列表 ----------------
    # 这是最省事的写法，官方 quickstart 里到处都是
    messages_as_dict: list[dict] = [
        {"role": "system", "content": "你是产线质量助手，回答控制在 30 字内。"},
        {"role": "user", "content": question},# 中间解析成HumanMessage  type=‘human’
    ]

    print("① 直接传 dict 列表")
    reply_a = llm.invoke(messages_as_dict)
    print(f"   返回类型 : {type(reply_a).__name__}") #AIMessage  AI返回的内容，type类型
    print(f"   内容     : {reply_a.text}")

    # ---------------- 中间：看看 dict 被转成了什么 ----------------
    # 这一步纯离线，不调模型
    print("\n② dict 传给 LangChain 后，内部被转成了什么")
    converted = convert_to_messages(messages_as_dict)
    for msg in converted:
        print(f"   {type(msg).__name__:16} type={msg.type!r:10} content={msg.content!r}")

    # ---------------- 写法 B：消息对象列表 ----------------
    messages_as_object = [
        SystemMessage(content="你是产线质量助手，回答控制在 30 字内。"),
        HumanMessage(content=question), #使用HumanMessage
    ]

    print("\n③ 传消息对象列表")
    reply_b = llm.invoke(messages_as_object)
    print(f"   返回类型 : {type(reply_b).__name__}")
    print(f"   内容     : {reply_b.text}")

    print("\n【关键点】两种写法都能跑，但能力不同")
    print("  dict     → 只能表达 role + content，够用但受限")
    print("  消息对象 → 能带 name / id / tool_calls / usage_metadata")
    print("  建议：临时试手写 dict；正式代码用消息对象，")
    print("        尤其要处理工具调用时，dict 根本表达不了 tool_calls。")
    print("  补充：两种写法可以混用，LangChain 会自动转换，但混用会让代码难读。")


# ============================================================
# Demo 3 · content 不只是字符串
# ============================================================

def demo3_content_blocks() -> None:
    show_title("Demo 3 · content 不一定是字符串")

    # ---------------- ① 字符串形式 ----------------
    text_only = HumanMessage(content="用一句话说明什么是回流焊。")
    print("① 字符串 content（99% 的场景都是这个）")
    print(f"   .content = {text_only.content!r}")
    print(f"   类型     = {type(text_only.content).__name__}")# str

    # ---------------- ② 内容块列表形式 ----------------
    # 图片、文件、缓存标记等，都必须用块表达
    block_form = HumanMessage(
        content=[
            {"type": "text", "text": "用一句话说明什么是回流焊。"},
        ]
    )
    print("\n② 内容块列表 content（多模态 / 结构化场景）")
    print(f"   .content        = {block_form.content}")
    print(f"   类型            = {type(block_form.content).__name__}")# list
    print(f"   .text           = {block_form.text!r}")
    print(f"   .content_blocks = {block_form.content_blocks}")

    # ---------------- ③ 真的发一次，确认模型能接受 ----------------
    reply = llm.invoke([block_form])
    print(f"\n③ 用内容块形式真的发一次请求 → {reply.text}")

    print("\n【关键点】")
    print("  字符串 content 只是简写，底层统一是内容块列表。")
    print("  .text 会自动把 text 块拼成纯文本；.content_blocks 是统一后的标准块格式。")
    print("  想拿纯文本一律用 .text —— 不要自己遍历 content 去拼，")
    print("  因为 content 有时是 str、有时是 list，自己拼必然写出两套分支。")
    print("  图片输入的形状：{'type': 'image_url', 'image_url': {'url': '...'}}")


# ============================================================
# Demo 4 · 多轮对话的本质
#
# 这是本文件最重要的一节。
# 核心事实：模型 API 是无状态的，每一轮都要把"全部历史"重新发一遍。
# ============================================================

def demo4_multi_turn() -> None:
    show_title("Demo 4 · 多轮对话：模型没有记忆，历史全靠你传")

    # 注意：system 里【故意不写】任何批次数据。
    # 数据只存在于"对话历史"里，这样对照实验才有意义。
    system_msg = SystemMessage(
        content=(
            "你是不良品根因分析助手。回答只基于对话中出现过的数据；"
            "如果缺少必要信息，直接反问，绝对不要猜测。"
        )
    )

    # ---------------- ① 手工构造一段"上一轮已经查过工单"的历史 ----------------
    # 这条序列就是阶段 3 手写工具循环时，模型真实会产出的消息链：
    #   Human 提问 → AI 请求调工具 → Tool 返回结果 → AI 总结
    history: list = [
        system_msg,
        HumanMessage(content="3号线 2026-10-24 的情况怎么样？"),
        AIMessage(
            content="",  # 只请求调工具时，content 可以是空的
            tool_calls=[
                {
                    "name": "query_workorder",
                    "args": {"line": "3号线", "date": "2026-10-24"},
                    "id": "call-001",
                }
            ],
        ),
        ToolMessage(
            content=(
                "3号线 2026-10-24 共 5 个批次："
                "B001 正常 / B002 异常（焊缝气孔）/ B003 异常（虚焊）/ "
                "B004 正常 / B005 异常（气孔）"
            ),
            tool_call_id="call-001",
            name="query_workorder",
        ),
        AIMessage(
            content="3号线 2026-10-24 共 5 个批次，其中 3 个异常："
                    "B002 焊缝气孔、B003 虚焊、B005 气孔。"
        ),
    ]

    print("① 已经存在的对话历史（模拟上一轮刚查完工单）")
    for i, msg in enumerate(history):
        brief = msg.text if msg.text else f"<tool_calls: {[c['name'] for c in msg.tool_calls]}>"
        print(f"   [{i}] {type(msg).__name__:14} {brief[:60]}")

    # ---------------- ② 带历史继续问 ----------------
    # 这句话里只有"那"和"B002"，没有任何背景信息
    # 能答对，完全靠前面那段历史
    history.append(HumanMessage(content="那 B002 是什么问题？"))

    print("\n② 第二轮：带完整历史提问")
    print(f"   发送 {len(history)} 条消息")
    reply_2 = llm.invoke(history)
    print(f"   回复：{reply_2.text}")

    # 关键动作：把模型的回复也追加进历史，否则下一轮就"忘了自己说过什么"
    history.append(reply_2)

    # ---------------- ③ 对照实验：同样的问法，历史清空 ----------------
    print("\n③ 对照实验：同样的问题，但只发 system + 这一句（模拟新开会话）")
    fresh_messages = [
        system_msg,
        HumanMessage(content="那 B002 是什么问题？"),
    ]
    print(f"   发送 {len(fresh_messages)} 条消息")
    reply_3 = llm.invoke(fresh_messages)
    print(f"   回复：{reply_3.text}")

    print("\n【关键点 1】对比 ② 和 ③")
    print("  ② 答得出，是因为历史里有 B002 的出现语境；")
    print("  ③ 答不出（应该反问或说不知道），因为上下文断了。")
    print("  模型本身完全无状态——所谓'多轮对话'，就是客户端反复重发整个列表。")
    print("  如果 ③ 也答对了，说明你的 system prompt 里泄露了答案，对照就失效了。")

    print("\n【关键点 2】所以 messages 列表 = 上下文本身")
    print("  列表越长 → token 越多 → 越贵越慢，最终撞上模型的上下文上限。")
    print("  这就是为什么需要'上下文裁剪'和'摘要压缩'（模块 E 场景 4、Pi Agent 的压缩机制）。")

    print("\n【关键点 3】LangGraph 里的对应物")
    print("  State 里的 messages 字段 + add_messages reducer，")
    print("  干的事就是'自动帮你把新消息追加进这个列表'。")
    print("  没有 reducer，新消息会覆盖旧列表，历史就丢了。")


# ============================================================
# Demo 5 · AIMessage 里除了 content 还有什么
# ============================================================

def demo5_ai_message_metadata() -> None:
    show_title("Demo 5 · AIMessage 的完整结构")

    reply = llm.invoke(
        [
            SystemMessage(content="回答控制在 20 字内。"),
            HumanMessage(content="回流焊峰值温度偏低会导致什么缺陷？"),
        ]
    )

    print(f"① .content          = {reply.content!r}")
    print(f"② .text             = {reply.text!r}")
    print(f"③ .type             = {reply.type!r}")
    print(f"④ .id               = {reply.id!r}")
    print(f"⑤ .usage_metadata   = {reply.usage_metadata}")
    print(f"⑥ .response_metadata 的键 = {list(reply.response_metadata.keys())}")
    print(f"   finish_reason    = {reply.response_metadata.get('finish_reason')!r}")
    print(f"   model_name       = {reply.response_metadata.get('model_name')!r}")
    print(f"⑦ .additional_kwargs 的键 = {list(reply.additional_kwargs.keys())}")

    # reasoning_content 是 DeepSeek 系思考模型的思维链，放在 response_metadata 里
    reasoning = reply.response_metadata.get("reasoning_content")
    if reasoning:
        print(f"\n   （检测到思维链 reasoning_content，前 100 字）")
        print(f"   {reasoning[:100]}...")

    print("\n【注意 1】.id 是 LangChain 生成的 run id，不是模型返回的")
    print("  它长这样：'lc_run--01a1734f-...'，前缀固定是 lc_run--。")
    print("  作用：日志追踪、和 LangSmith 的 trace 对齐。")
    print("  自己构造消息时（比如 Demo 1），id 可以手填业务上的 id。")

    print("\n【注意 2】看 output_token_details")
    print("  usage_metadata 里如果有 output_token_details={'reasoning': N}，")
    print("  说明这个模型在走思考模式，N 个 token 花在推理上，而且照样计费。")
    print("  要关掉思考模式，得在 ChatOpenAI 里传 extra_body（参数名以厂商文档为准）。")

    print("\n【关键点】三个 metadata 别混")
    print("  usage_metadata    → 标准化后的 token 用量（input / output / total）")
    print("                      跨厂商统一格式，算成本的唯一依据")
    print("  response_metadata → 厂商原始返回：finish_reason / model_name /")
    print("                      reasoning_content / system_fingerprint 等")
    print("  additional_kwargs → 请求侧附加参数的回显，老代码里 tool_calls 曾放这里")

    print("\n【坑】usage_metadata 可能是 None")
    print("  部分 OpenAI 兼容接口不返回 usage 字段。")
    print("  直接 reply.usage_metadata['total_tokens'] 会 TypeError，必须先判空。")

    print("\n【坑】finish_reason 要看")
    print("  'stop'     正常结束")
    print("  'length'   撞到 max_tokens 被截断 → 输出不完整")
    print("  'tool_calls' 模型在请求调工具 → content 可能是空的，看 tool_calls")


# ============================================================
# Demo 6 · 流式返回的 AIMessageChunk
# ============================================================

def demo6_streaming_chunks() -> None:
    show_title("Demo 6 · 流式返回的是 AIMessageChunk")

    print("实时输出（打字机效果）：")
    print("  ", end="", flush=True)

    merged: AIMessageChunk | None = None
    chunk_count = 0
    first_chunk_usage = None

    for chunk in llm.stream([HumanMessage(content="用三句话说明什么是回流焊。")]):
        chunk_count += 1
        # chunk 不是 str，是 AIMessageChunk —— 要 .text 才拿到文本
        print(chunk.text, end="", flush=True)# 输出文本

        if first_chunk_usage is None:
            first_chunk_usage = chunk.usage_metadata

        # 相加 = 按规则合并 content 片段和 tool_calls 片段
        merged = chunk if merged is None else merged + chunk

    print()
    print(f"\n共收到 {chunk_count} 个 chunk")
    print(f"单个 chunk 类型 = {type(chunk).__name__}")
    print(f"相加后的类型    = {type(merged).__name__}")
    print(f"第一个 chunk 的 usage_metadata = {first_chunk_usage}")
    print(f"拼接后的 usage_metadata        = {merged.usage_metadata if merged else None}")
    print(f"拼出的全文长度  = {len(merged.text) if merged else 0} 字")

    print("\n【关键点 1】chunk 不是字符串")
    print("  直接 print(chunk) 会打出 AIMessageChunk(...) 的 repr，看着像乱码。")
    print("  一律用 chunk.text 取文本。")

    print("\n【关键点 2】chunk 相加是 LangGraph 流式的基础")
    print("  astream_events / stream_mode='messages' 吐出来的也是 chunk，")
    print("  要把它们拼成完整消息，靠的就是 + 运算。")

    print("\n【关键点 3】usage_metadata 出现在哪个 chunk，不同厂商不一样")
    print("  有的实现放在最后一个 chunk，本环境实测【第一个 chunk 就带全量 usage】。")
    print("  所以不要假设它在末尾 —— 循环结束后统一读 merged.usage_metadata 最稳。")


# ============================================================
# 三、入口
# ============================================================

# (编号, 标题, 函数, 是否需要调模型)
DEMOS: list[tuple[str, str, Callable[[], None], bool]] = [
    # ("1", "四种消息类型", demo1_four_message_types, False),
    # ("2", "dict 简写 vs 消息对象", demo2_dict_vs_object, True),
    # ("3", "content 内容块", demo3_content_blocks, True),
    # ("4", "多轮对话的本质", demo4_multi_turn, True),
    # ("5", "AIMessage 完整结构", demo5_ai_message_metadata, True),
    ("6", "流式 chunk 拼接", demo6_streaming_chunks, True),
]


def main() -> None:
    args = sys.argv[1:]
    offline_only = "--offline" in args
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print(f"1.2 消息类型 | 模型 = {MODEL_CODE}")
    if offline_only:
        print("模式：--offline（跳过所有需要调模型的 Demo）")
    print("=" * 72)

    for key, title, func, needs_model in DEMOS:
        # 指定了编号，就只跑指定的
        if picked and key not in picked:
            continue
        # --offline 模式跳过需要模型的
        if offline_only and needs_model:
            continue
        func()

    print()
    print("=" * 72)
    print("全部完成")
    print("=" * 72)


if __name__ == "__main__":
    main()
