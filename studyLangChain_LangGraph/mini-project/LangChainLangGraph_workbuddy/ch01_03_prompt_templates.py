"""1.3 提示词模板（Prompts）

【跑这个文件能看到什么】
Demo 1  PromptTemplate：单条字符串模板，变量怎么识别、怎么填
Demo 2  ChatPromptTemplate：多角色模板，system / human 怎么写
Demo 3  MessagesPlaceholder：把多轮历史插进模板（多轮对话的关键）
Demo 4  变量校验：缺变量报什么错、多传变量会怎样
Demo 5  花括号转义：想输出 JSON 必踩的坑
Demo 6  partial：预填固定变量，只留变化的那个
Demo 7  管道 prompt | llm：LCEL 的最小形态
Demo 8  实证：system prompt 到底有多大用（同一个问题两种结果）

【对应手册】Part 1 · 1.3 提示词模板

【怎么跑】
    cd studyLangChain_LangGraph/mini-project

    # 全部跑（Demo 7/8 会调模型）
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_03_prompt_templates.py

    # 只跑离线部分（Demo 1-6，秒出、不花钱）
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_03_prompt_templates.py --offline

    # 只跑指定 Demo
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_03_prompt_templates.py 5

【跑之前确认】
    .env 在 mini-project/ 下，含 DASHSCOPE_API_KEY / BASE_URL / MODEL_CODE
"""

import json
import os
import sys
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from langchain_openai import ChatOpenAI


# ============================================================
# 一、加载配置（和 1.1 / 1.2 一致）
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
# Demo 1 · PromptTemplate（离线）
# ============================================================

def demo1_prompt_template() -> None:
    show_title("Demo 1 · PromptTemplate：单条字符串模板（离线）")

    # from_template 会自动扫描 {} 里的变量名
    template = PromptTemplate.from_template(
        "产线 {line} 在 {date} 有哪些异常批次？"
    )

    print("① 模板自动识别出的变量")
    print(f"   input_variables = {template.input_variables}")
    print("   注意：是【排序后】的，不是你写的顺序")
    print("   （模板里先写 line 后写 date，结果是 ['date', 'line']）")

    print("\n② 填变量，生成最终文本")
    text_1 = template.format(line="3号线", date="2026-10-24")
    print(f"   {text_1}")

    print("\n③ 换个参数再生成一次（模板可以反复用）")
    text_2 = template.format(line="5号线", date="2026-10-25")
    print(f"   {text_2}")

    # ---------------- 和 f-string 对比 ----------------
    # f-string 写法：立刻求值，拼完就固定了
    line = "3号线"
    text_fstring = f"产线 {line} 在 2026-10-24 有哪些异常批次？"
    print("\n④ 同样的内容用 f-string 写")
    print(f"   {text_fstring}")
    print("   看起来一模一样，但能力差很多 ↓")

    print("\n【为什么用模板，不用 f-string】")
    print("  f-string        → 立刻求值，一次性的，拼完就是死字符串")
    print("  PromptTemplate  → 延迟填充，可复用、可校验、可 partial、可接管道")
    print("")
    print("  三个模板独有的能力：")
    print("    1. .input_variables 能列出要哪些参数 → 可以自动生成前端表单、做校验")
    print("    2. .partial() 能预填部分变量 → 会话级参数只传一次")
    print("    3. 能接管道 prompt | llm → LCEL 的基础")
    print("  f-string 一个都做不到。")


# ============================================================
# Demo 2 · ChatPromptTemplate（离线）
# ============================================================

def demo2_chat_prompt_template() -> None:
    show_title("Demo 2 · ChatPromptTemplate：多角色模板（离线）")

    # from_messages 收一个列表，每项是 (角色, 内容模板)
    template = ChatPromptTemplate.from_messages([
        ("system", "你是不良品根因分析助手，当前负责产线：{line}"),
        ("human", "{question}"),
    ])

    print("① 变量")
    print(f"   input_variables = {template.input_variables}")

    print("\n② format_messages 生成消息列表")
    messages = template.format_messages(line="3号线", question="昨天有哪些异常？")
    for i, msg in enumerate(messages):
        print(f"   [{i}] {type(msg).__name__:14} {msg.text}")

    print("\n③ invoke 返回的不是消息列表，是 ChatPromptValue")
    value = template.invoke({"line": "3号线", "question": "昨天有哪些异常？"})
    print(f"   类型            = {type(value).__name__}")
    print(f"   .to_messages()  = {len(value.to_messages())} 条")
    print("   （这个对象能直接喂给 llm，所以管道里不用你手动转）")

    print("\n【元组简写和消息类的对应关系】")
    print("   ('system', '...') → SystemMessage")
    print("   ('human',  '...') → HumanMessage")
    print("   ('ai',     '...') → AIMessage")
    print("   ('tool',   '...') → ToolMessage（要额外带 tool_call_id，一般不用模板生成）")

    print("\n【关键点】一条模板里可以有多个 human / ai")
    multi = ChatPromptTemplate.from_messages([
        ("system", "你是质量助手"),
        ("human", "3号线昨天情况？"),
        ("ai", "共 5 个批次，3 个异常。"),
        ("human", "{question}"),
    ])
    print(f"   这样能直接写死一段'历史对话'，变量只有 {multi.input_variables}")
    print("   适合做 few-shot 示例（给模型看几个正确示范）")


# ============================================================
# Demo 3 · MessagesPlaceholder（离线）
#
# 这是多轮对话模板的核心。1.2 里你自己 append 列表，
# 这里是把"历史列表"作为一个变量插进去。
# ============================================================

def demo3_messages_placeholder() -> None:
    show_title("Demo 3 · MessagesPlaceholder：把历史插进模板（离线）")

    template = ChatPromptTemplate.from_messages([
        ("system", "你是不良品根因分析助手"),
        MessagesPlaceholder(variable_name="history"),# history 也是别出为一个变量，且是必填的
        ("human", "{question}"),
    ])

    print("① 不加 optional 时")
    print(f"   input_variables = {template.input_variables}")
    print("   history 被当成【必填】变量")

    print("\n② 缺 history 会直接报错")
    try:
        template.format_messages(question="还有别的吗？")
    except KeyError as e:
        print(f"   KeyError: {e}")
        print("   ← 报的是裸 KeyError，没有友好提示，第一次遇到会懵")

    print("\n③ 填了 history 才正常")
    history = [
        HumanMessage(content="3号线昨天有异常吗？"),
        AIMessage(content="有 3 个异常批次：B002 焊缝气孔、B003 虚焊、B005 气孔"),
    ]
    messages = template.format_messages( # 这里的history 补上了 template中的history变量内容
        history=history,
        question="那 B002 具体是什么问题？",# 这个成了HumanMessage
    )
    for i, msg in enumerate(messages):
        print(f"   [{i}] {type(msg).__name__:14} {msg.text}")

    print("\n④ 更实用的写法：optional=True")
    template_optional = ChatPromptTemplate.from_messages([
        ("system", "你是不良品根因分析助手"),
        MessagesPlaceholder(variable_name="history", optional=True),# 加了optional后，history变量不显示了
        ("human", "{question}"),
    ])
    print(f"   input_variables = {template_optional.input_variables}   ← history 不见了")
    first_turn = template_optional.format_messages(question="第一次提问")
    print(f"   不传 history 也能用，生成 {len(first_turn)} 条")
    print("   这才是多轮对话的正确姿势：第一轮没历史也不该报错")

    print("\n⑤ 简写形式：('placeholder', '{history}')")
    template_short = ChatPromptTemplate.from_messages([
        ("system", "你是不良品根因分析助手"),
        ("placeholder", "{history}"),
        ("human", "{question}"),
    ])
    print(f"   input_variables = {template_short.input_variables}")
    print("   注意：简写形式默认就是 optional，不用额外传参")
    print("   但可读性差一些，正式代码建议写全 MessagesPlaceholder(...)")


# ============================================================
# Demo 4 · 变量校验（离线）
# ============================================================

def demo4_variable_validation() -> None:
    show_title("Demo 4 · 变量校验：缺了会怎样、多了会怎样（离线）")

    template = ChatPromptTemplate.from_messages([
        ("system", "你是 {role}，负责产线 {line}"),
        ("human", "{question}"),
    ])
    print(f"① 模板声明了哪些变量：{template.input_variables}")

    print("\n② 缺变量 → KeyError")
    try:
        template.format_messages(role="质量助手", question="怎么办")
    except KeyError as e:
        print(f"   KeyError: {e}")

    print("\n③ 多传变量 → 静默忽略，不报错")
    messages = template.format_messages(
        role="质量助手",
        line="3号线",
        question="怎么办",
        extra="这个变量模板里根本没有",
    )
    print(f"   正常生成 {len(messages)} 条，extra 被直接丢掉")

    print("\n④ 所以变量名拼错时，症状是「两个一起出现」")
    try:
        # role 拼成了 roles
        template.format_messages(roles="质量助手", line="3号线", question="怎么办")
    except KeyError as e:
        print(f"   把 role 写成 roles → KeyError: {e}")
        print("   报错只说'缺 role'，不会说'roles 是多余的'")
        print("   得自己对一眼变量名")

    print("\n【实用建议】")
    print("  正式代码里把 input_variables 打印一次，或者写个断言：")
    print("    assert set(template.input_variables) == {'role', 'line', 'question'}")
    print("  比到处试参数快得多。")


# ============================================================
# Demo 5 · 花括号转义（离线）
#
# 这是本文件最值得亲手跑的一节。
# 只要你的提示词里要模型输出 JSON，就一定会撞上。
# ============================================================

def demo5_braces_escaping() -> None:
    show_title("Demo 5 · 花括号转义：想输出 JSON 必踩的坑（离线）")

    print("① 想输出 JSON，直接写单个花括号 → 创建时就报错")
    try:
        PromptTemplate.from_template('输出 JSON：{"cause": "{cause}"}')
    except ValueError as e:
        print(f"   ValueError: {str(e)[:90]}...")
        print("   ← 报错发生在【创建模板】时，不是 format 时")
        print("     所以你会以为'我还没填变量怎么就错了'")

    print("\n② 正确写法：字面花括号要双写")
    template = PromptTemplate.from_template(
        '输出 JSON：{{"root_cause": "{cause}", "confidence": {score}}}'
    )
    print(f"   input_variables = {template.input_variables}")
    print(f"   生成结果 = {template.format(cause='温度偏低', score=0.85)}")#将变量值填入到json中
    print("   ← {{ }} 变成 { }，{cause} 变成实际值")

    print("\n③ 变量【值】里带花括号是安全的（不会报错）")
    value_with_braces = '{"a": 1}'
    print(f"   传值 = {value_with_braces}")
    print(f"   结果 = {template.format(cause=value_with_braces, score=0.5)}")
    print("   因为替换只做一遍，不会对插入进去的值再解析")

    print("\n   ⚠ 但「不报错」不等于「结果正确」")
    print("   上面生成的 JSON 其实是坏的 —— 内层引号没有转义，json.loads 会失败。")
    print("   原因：模板只做字符串替换，不负责 JSON 转义。")

    print("\n   正确的做法不是'给值加转义'，而是【别手工拼 JSON】")
    print("   整个对象一次性交给 json.dumps：")
    data = {"root_cause": '温度偏低（"峰值"未达标）', "confidence": 0.85}
    print(f"   数据     = {data}")
    print(f"   序列化后 = {json.dumps(data, ensure_ascii=False)}")
    print("   ← 引号自动转义，这才是合法 JSON")

    print("\n   反例：手工拼字符串（值里有引号就崩）")
    broken = '{"root_cause": "' + data["root_cause"] + '"}'
    print(f"   手工拼的 = {broken}")
    print("   json.loads 直接报错 —— 这就是为什么生产代码里禁止手工拼 JSON")

    print("\n【规律，记住这三条】")
    print("  模板里的字面花括号  → 双写 {{ }}")
    print("  模板里的变量占位符  → 单写 {name}")
    print("  变量传进去的值      → 不用管，安全")

    print("\n【实战】")
    print("  让模型输出 JSON 时，模板里几乎一定有字面花括号。")
    print("  很多人第一次写 JSON 模板就撞 Invalid format specifier，就是这里。")
    print("  替代方案：用 Pydantic + with_structured_output（1.4 会讲），")
    print("  那样连 JSON 都不用写在提示词里。")


# ============================================================
# Demo 6 · partial（离线）
# ============================================================

def demo6_partial() -> None:
    show_title("Demo 6 · partial：预填固定变量（离线）")

    template = ChatPromptTemplate.from_messages([
        ("system", "你是不良品根因分析助手，负责产线：{line}，工厂：{factory}"),
        ("human", "{question}"),
    ])
    print(f"① 原始变量 = {template.input_variables}")

    step1 = template.partial(factory="华东一厂")
    print(f"② partial(factory=...) 之后 = {step1.input_variables}")

    step2 = step1.partial(line="3号线")
    print(f"③ 再 partial(line=...) 之后 = {step2.input_variables}")

    print("\n④ 最后只剩 question 要传")
    messages = step2.format_messages(question="昨天有哪些异常？")
    for msg in messages:
        print(f"   {type(msg).__name__:14} {msg.text}")

    print("\n⑤ partial 返回新对象，原模板不变")
    print(f"   原模板变量仍是 = {template.input_variables}")

    print("\n【场景】")
    print("  产线、工厂、当前用户这些'会话级固定'的参数，")
    print("  用 partial 预填一次，后面每次只传 question。")
    print("  LangGraph 里对应的做法是'把配置注入节点'，而不是每个节点都传一遍。")

    print("\n【坑】partial 可以覆盖已有变量，不会报错")
    overridden = step2.partial(line="5号线")
    print(f"   把 line 再 partial 成 5号线 → {overridden.format_messages(question='测试')[0].text}")
    print("   这在批量循环里很容易不小心覆盖掉，注意别在循环里 partial 同一个变量")


# ============================================================
# Demo 7 · 管道 prompt | llm（需要模型）
# ============================================================

def demo7_pipe() -> None:
    show_title("Demo 7 · 管道：prompt | llm")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是不良品根因分析助手，回答控制在 25 字内。"),
        ("human", "{question}"),
    ])

    chain = prompt | llm
    print(f"① chain 类型 = {type(chain).__name__}")
    print("   这就是 LCEL 的最小形态：一个 Runnable 接另一个 Runnable")
    print("   注意：这里只是【拼好】，还没执行")

    questions = [
        "虚焊的典型特征是什么",
        "气孔一般怎么产生",
        "冷焊和虚焊怎么区分",
    ]
    print("\n② 同一个 chain 跑三个不同输入")
    for question in questions:
        answer = chain.invoke({"question": question})
        print(f"   Q: {question}")
        print(f"   A: {answer.text}")

    print("\n【关键点 1】invoke 的参数是 dict，键必须和模板变量对上")
    try:
        chain.invoke({"q": "变量名写错了"})
    except KeyError as e:
        print(f"   传 {{'q': ...}} 会报 KeyError: {e}")
        print("   不是静默失败，这点比 f-string 安全")

    print("\n【关键点 2】chain 是可复用的对象")
    print("   prompt 定义一次，invoke 无数次 —— 这就是和 f-string 最本质的差别。")


# ============================================================
# Demo 8 · 实证 system prompt 的作用（需要模型）
# ============================================================

def demo8_system_prompt_effect() -> None:
    show_title("Demo 8 · 实证：system prompt 到底有多大用")

    # "气孔" 这个词有两个完全不同的领域含义：
    #   焊接 → 焊点内部的气泡缺陷
    #   生物学 → 植物叶片的呼吸孔
    question = "什么是气孔？"

    print(f"问题：{question}")
    print("（这个词在焊接里是缺陷，在生物学里是植物结构）")

    # 两边都限制长度，不然输出太长看不清对比
    bare = ChatPromptTemplate.from_template("用 80 字以内回答：{question}")
    answer_bare = llm.invoke(bare.format_messages(question=question))
    print("\n① 裸模板（没有 system 约束）")
    print(f"   {answer_bare.text}")

    scoped = ChatPromptTemplate.from_messages([
        ("system", "你是 SMT 焊接工艺专家。只回答焊接领域的问题，不要提其他领域。"),# 通过systemMessage可以约束范围！
        ("human", "用 80 字以内回答：{question}"),
    ])
    answer_scoped = llm.invoke(scoped.format_messages(question=question))
    print("\n② 加了 system 角色约束")
    print(f"   {answer_scoped.text}")#通过SystemMessage约束后的消息

    print("\n【观察什么】")
    print("  对比两段回答：① 很可能扯到植物气孔，或者两个都讲；")
    print("  ② 应该只讲焊点气泡。")
    print("  这不是模型笨，是你没告诉它领域。")

    print("\n【结论】")
    print("  system prompt 的第一职责是【消除歧义】，不是'让模型更聪明'。")
    print("  做根因追溯时，领域词（气孔 / 虚焊 / 冷焊 / 拉丝 / 缩孔）都有多义性，")
    print("  system 里必须锚定'这是 SMT / PCBA 制造场景'。")
    print("")
    print("  这也解释了为什么很多人觉得'加了 system 效果好很多'——")
    print("  不是模型变强了，是它终于知道你在说什么领域。")


# ============================================================
# 三、入口
# ============================================================

# (编号, 标题, 函数, 是否需要调模型)
DEMOS: list[tuple[str, str, Callable[[], None], bool]] = [
    ("1", "PromptTemplate 基础", demo1_prompt_template, False),
    ("2", "ChatPromptTemplate 多角色", demo2_chat_prompt_template, False),
    ("3", "MessagesPlaceholder 历史", demo3_messages_placeholder, False),
    ("4", "变量校验", demo4_variable_validation, False),
    ("5", "花括号转义", demo5_braces_escaping, False),
    ("6", "partial 预填", demo6_partial, False),
    ("7", "管道 prompt | llm", demo7_pipe, True),
    ("8", "system prompt 的作用", demo8_system_prompt_effect, True),
]


def main() -> None:
    args = sys.argv[1:]
    offline_only = "--offline" in args
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print(f"1.3 提示词模板 | 模型 = {MODEL_CODE}")
    if offline_only:
        print("模式：--offline（跳过 Demo 7/8）")
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
