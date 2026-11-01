"""1.5 工具定义（@tool / args_schema / bind_tools）

【跑这个文件能看到什么】
Demo 1  最小工具：裸 @tool 靠函数签名 + docstring 生成工具
Demo 2  ★ 裸 @tool 的参数没有 description —— 为什么必须用 args_schema
Demo 3  docstring 与工具名的硬约束（没 docstring 直接报错）
Demo 4  直接执行工具：tool.invoke 与参数校验失败
Demo 5  好 docstring 的四段式写法
Demo 6  ★ bind_tools 之后，看模型到底怎么调工具
Demo 7  ★ docstring 写含糊 vs 写精确，模型的调用行为差异

【对应手册】Part 1 · 1.5 工具定义
【对应简历】"实现 MCP 工具发现与白名单注册、字段与查询条件校验"

【怎么跑】
    cd studyLangChain_LangGraph/mini-project

    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_05_tool_definition.py
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_05_tool_definition.py --offline
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_05_tool_definition.py 2

【和前面模块的关系】
    模块 C  的 Tool 类      → @tool 帮你自动生成的东西
    模块 D  的 Pydantic     → args_schema 用的就是它
    模块 G  的装饰器        → @tool 本身就是一个装饰器
    1.4 的结构化输出        → 底层就是"借工具调用"，这里看到正面
"""

import json
import os
import sys
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
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
# 假数据（模拟真实 MES / QMS）
#
# 真实项目里这些会换成数据库查询，但工具定义部分完全一样。
# ============================================================

FAKE_WORKORDERS: dict = {
    ("3号线", "2026-10-24"): [
        {"batch": "B001", "status": "正常"},
        {"batch": "B002", "status": "异常", "defect": "焊缝气孔"},
        {"batch": "B003", "status": "异常", "defect": "虚焊"},
        {"batch": "B004", "status": "正常"},
        {"batch": "B005", "status": "异常", "defect": "气孔"},
    ],
}

FAKE_QUALITY: dict = {
    "B002": {
        "defect": "焊缝气孔",
        "peak_temp": 228,
        "standard": "235-245",
        "operator": "张三",
    },
}


# ============================================================
# Demo 1 · 最小工具
# ============================================================

def demo1_minimal_tool() -> None:
    show_title("Demo 1 · 最小工具：裸 @tool（离线）")

    @tool
    def query_workorder(line: str, date: str = "昨天") -> str:
        """查询指定产线在某天的工单记录。

        适用于：用户询问某条产线的生产情况、批次数量、异常批次。

        Args:
            line: 产线编号，例如 "3号线"
            date: 日期，格式 YYYY-MM-DD
        """
        records = FAKE_WORKORDERS.get((line, date))  # 模拟从 ERP 系统查数据
        if not records:
            return f"{line} {date} 没有记录"
        abnormal = [r for r in records if r["status"] == "异常"]
        return f"{line} {date} 共 {len(records)} 个批次，{len(abnormal)} 个异常" #按照格式结果输出

    # ① 加了 @tool 之后，它变成了什么
    print(f"type = {type(query_workorder).__name__}")#打的是tool的类型
    print(f"name = {query_workorder.name}")#打的是tool的工具名称
    print(f"desc = {query_workorder.description}")#查询指定产线在某天的工单记录
    #args = {'line': {'title': 'Line', 'type': 'string'}, 'date': {'default': '昨天', 'title': 'Date', 'type': 'string'}}
    print(f"args = {query_workorder.args}")  # 坑：只有 title/type，没有 description

    # ② 直接执行，不经过模型
    print("直接输出：",query_workorder.invoke({"line": "3号线", "date": "2026-10-24"}))

    # ③ 不传 date → 默认值 '昨天' → 假数据里没有，返回"没有记录"
    print(f"default = {query_workorder.args['date']['default']!r}")
    print(query_workorder.invoke({"line": "3号线"}))


# ============================================================
# Demo 2 · args_schema（本文件最重要），告诉工具对象，参数的长什么样
# ============================================================

def demo2_args_schema() -> None:
    show_title("Demo 2 · 为什么必须用 args_schema（离线）")

    # ---------------- 写法 A：裸 @tool ----------------
    @tool
    def query_workorder_a(line: str, date: str) -> str:
        """查询指定产线在某天的工单记录。

        Args:
            line: 产线编号，例如 "3号线"
            date: 日期，格式 YYYY-MM-DD
        """
        return f"A: {line} {date}"

    print(f"A 裸 @tool     args = {query_workorder_a.args}\n")  # 无 description

    # ---------------- 写法 B：args_schema  Pydantic写法----------------
    class WorkorderQuery(BaseModel):
        """查询工单的参数"""

        line: str = Field(
            description="产线编号，只能是 '3号线' / '5号线' 这种格式，不要传产品名"
        )
        date: str = Field(
            description="日期，格式必须是 YYYY-MM-DD，例如 2026-10-24"
        )

    #定义工具，如果在@Tool中写入名字，说明覆盖默认函数名（默认将函数名作为工具名）
    @tool("query_workorder", args_schema=WorkorderQuery)
    def query_workorder_b(line: str, date: str) -> str:
        """查询指定产线在某天的工单记录。用户问产线生产情况、批次数量时必须用这个工具。"""
        return f"B: {line} {date}"

    print(f"B args_schema  args = {query_workorder_b.args}\n")  # 有 description

    schema_a = query_workorder_a.tool_call_schema.model_json_schema()
    schema_b = query_workorder_b.tool_call_schema.model_json_schema()
    print(f"\nA schema = {json.dumps(schema_a, ensure_ascii=False)}")
    print(f"\nB schema = {json.dumps(schema_b, ensure_ascii=False)}")



# ============================================================
# Demo 3 · docstring 与工具名的硬约束
# ============================================================

def demo3_constraints() -> None:
    show_title("Demo 3 · docstring 与工具名的硬约束（离线）")

    # ① 没有 docstring → 创建时就报错，不是调用时
    try:
        @tool
        def no_doc(line: str) -> str:
            return f"{line}"
    except ValueError as e:
        print(f"① 无 docstring   ValueError: {e}")#Function must have a docstring if description not provided.

    # ② 工具名带空格 —— 本网关不报错，但 OpenAI 要求 ^[a-zA-Z0-9_-]+$
    @tool("query workorder")
    def bad_name(line: str) -> str:
        """查询工单"""
        return f"{line}"

    print(f"② 名字带空格    创建成功，name = {bad_name.name!r}")

    # ③ 工具名和函数名可以不一致，模型只认 @tool 里那个
    @tool("query_quality")
    def query_quality_b(line: str) -> str:
        """查询质检记录"""
        return f"{line}"

    print(
        f"③ 名字不一致    name = {query_quality_b.name!r}，"
        f"函数名 = {query_quality_b.func.__name__!r}"
    )


# ============================================================
# Demo 4 · 直接执行工具
# ============================================================

def demo4_invoke_tool() -> None:
    show_title("Demo 4 · 直接执行工具：tool.invoke（离线）")

    class QualityQuery(BaseModel):
        """查询质检记录"""

        batch_id: str = Field(description="批次号，例如 B002")
        include_raw: bool = Field(
            default=False, description="是否包含原始检测数据"
        )

    @tool("query_quality", args_schema=QualityQuery)
    def query_quality(batch_id: str, include_raw: bool = False) -> str:
        """查询指定批次的质检记录，返回不良项与检测参数。"""
        record = FAKE_QUALITY.get(batch_id)
        if not record:
            return f"批次 {batch_id} 没有质检记录"
        return (
            f"{batch_id}: 不良项={record['defect']}, "
            f"峰值温度={record['peak_temp']}℃ (标准 {record['standard']})"
        )

    print(f"① 正常     {query_quality.invoke({'batch_id': 'B002'})}")
    print(f"② 查不到   {query_quality.invoke({'batch_id': 'B999'})}")  # 返回文字，不抛异常

    # ③ 参数类型不对 → Pydantic 在进业务逻辑前就拦下
    try:
        query_quality.invoke({"batch_id": 123})
    except ValidationError as e:
        err = e.errors()[0]
        print(f"③ 类型错   {err['loc']} → {err['msg']} (input={err.get('input')!r})") # ('batch_id',) → Input should be a valid string (input=123)

    # ④ 缺必填参数 → 同样是校验失败
    try:
        query_quality.invoke({})
    except ValidationError as e:
        err = e.errors()[0]
        print(f"④ 缺参数   {err['loc']} → {err['msg']}")


# ============================================================
# Demo 5 · 好 docstring 的四段式
# ============================================================

def demo5_good_docstring() -> None:
    show_title("Demo 5 · 好 docstring 的四段式（离线）")

    print("差的写法：")
    print('   """查询"""                      ← 不知道查什么、什么时候用')
    print('   """查询批次信息"""              ← 没说清场景和返回')
    print('   """查询批次 B002 的质检记录"""   ← 写死具体数据，模型以为只能查 B002')

    print("\n好的写法（四段式）：")
    print('   """查询指定批次的质检记录。                            ← ① 做什么')
    print("   适用于：已知批次号，需要查看该批次的检测数据。         ← ② 什么时候用")
    print("   不适用于：只有产线号和日期时，先用 query_workorder。   ← ③ 什么时候不用")
    print('   返回：不良项名称、关键参数实测值与标准值。"""          ← ④ 返回什么')


# ============================================================
# Demo 6 · bind_tools 之后看模型怎么调
# ============================================================

def demo6_bind_tools() -> None:
    show_title("Demo 6 · bind_tools：模型到底怎么调工具")

    class WorkorderQuery(BaseModel):
        line: str = Field(description="产线编号，例如 3号线")
        date: str = Field(description="日期，格式 YYYY-MM-DD")

    class QualityQuery(BaseModel):
        batch_id: str = Field(description="批次号，例如 B002")

    @tool("query_workorder_tool", args_schema=WorkorderQuery)
    def query_workorder(line: str, date: str) -> str:
        """查询指定产线在某天的工单记录。用户问产线情况、批次数量时用这个。

        不适用于：已知批次号要查质检数据时，用 query_quality。
        """
        records = FAKE_WORKORDERS.get((line, date), [])
        if not records:
            return f"{line} {date} 没有记录"
        abnormal = [r for r in records if r["status"] == "异常"]
        return f"{line} {date} 共 {len(records)} 个批次，{len(abnormal)} 个异常：" + \
               ", ".join(r["batch"] for r in abnormal)

    @tool("query_quality_tool", args_schema=QualityQuery)
    def query_quality(batch_id: str) -> str:
        """查询指定批次的质检记录，返回不良项和检测参数。

        不适用于：只有产线号和日期时，应先用 query_workorder 查批次号。
        """
        record = FAKE_QUALITY.get(batch_id)
        if not record:
            return f"批次 {batch_id} 没有质检记录"
        return f"{batch_id}: {record['defect']}, 峰值温度 {record['peak_temp']}℃"

    tools = [query_workorder, query_quality]#工具集合,填的是函数名
    bound = llm.bind_tools(tools)#绑定工具集合

    def show_reply(question: str, reply) -> None:
        print(f"\nQ: {question}")
        print(f"   content    = {reply.text!r}")
        for call in reply.tool_calls:
            print(f"   tool_calls → {call['name']}  {call['args']}")

    print(f"绑定工具：{[t.name for t in tools]}")

    # 场景 1：有产线 + 日期，没有批次号 → 应选 query_workorder
    question_1 = "3号线 2026-10-24 有几个异常批次？"
    show_reply(question_1, bound.invoke(question_1))

    # 场景 2：有批次号 → 应选 query_quality
    question_2 = "B002 这个批次有什么问题？"
    show_reply(question_2, bound.invoke(question_2))


# ============================================================
# Demo 7 · docstring 质量对模型行为的影响
# ============================================================

def demo7_docstring_impact() -> None:
    show_title("Demo 7 · 工具设计质量对模型行为的影响")

    question = "3号线 2026-10-24 有几个异常批次？"
    print(f"同一个问题：{question}")

    # ---------------- 含糊版本：参数揉成一个 key ----------------
    # 常见的错误设计：觉得"查询条件"是一个东西，就塞进一个字符串
    class VagueArgs(BaseModel):
        key: str = Field(description="查询条件")

    @tool("query_vague", args_schema=VagueArgs)
    def query_vague(key: str) -> str:
        """查询"""
        return f"用 key={key!r} 查询，共 5 个批次，3 个异常"

    print(f"\n① 含糊   args = {query_vague.args}")
    reply_vague = llm.bind_tools([query_vague]).invoke(question)
    print(f"         → {reply_vague.tool_calls}")

    # ---------------- 精确版本：参数拆开 + 四段式描述 ----------------
    class PreciseArgs(BaseModel):
        line: str = Field(description="产线编号，例如 3号线、5号线")
        date: str = Field(description="生产日期，格式必须是 YYYY-MM-DD")

    @tool("query_workorder", args_schema=PreciseArgs)
    def query_workorder(line: str, date: str) -> str:
        """查询指定产线在某天的工单记录，返回批次数量和异常批次列表。

        适用于：用户问某条产线某天生产了多少批次、哪些批次异常。
        不适用于：已知批次号要查具体质检参数时，应用 query_quality。

        返回：批次总数、异常批次号列表。
        """
        return f"{line} {date} 共 5 个批次，3 个异常"

    print(f"\n② 精确   args = {query_workorder.args}")
    reply_precise = llm.bind_tools([query_workorder]).invoke(question)
    print(f"    1     → {reply_precise.tool_calls}")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], None], bool]] = [
    # ("1", "最小工具", demo1_minimal_tool, False),
    # ("2", "为什么必须用 args_schema", demo2_args_schema, False),
    # ("3", "docstring 与工具名的约束", demo3_constraints, False),
    # ("4", "直接执行工具 + 校验", demo4_invoke_tool, False),
    # ("5", "好 docstring 三段式", demo5_good_docstring, False),
    # ("6", "bind_tools 看模型怎么调", demo6_bind_tools, True),
    ("7", "docstring 质量的影响", demo7_docstring_impact, True),
]


def main() -> None:
    args = sys.argv[1:]
    offline_only = "--offline" in args
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print(f"1.5 工具定义 | 模型 = {MODEL_CODE}")
    if offline_only:
        print("模式：--offline（只跑 Demo 1-5）")
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
