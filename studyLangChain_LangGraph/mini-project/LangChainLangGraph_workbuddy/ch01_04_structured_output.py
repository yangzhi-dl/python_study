"""1.4 结构化输出（Pydantic + with_structured_output）

【跑这个文件能看到什么】
Demo 1  不用结构化输出的痛：让模型"输出 JSON"，然后手工解析
Demo 2  第一个 BaseModel + with_structured_output
Demo 3  ★ method 三选一对比：默认方式在你这个网关上会失败
Demo 4  嵌套模型：根因分析报告（结论 + 证据列表 + 建议）
Demo 5  include_raw=True：生产环境必须开的开关
Demo 6  model_json_schema()：后端双重校验用的就是这个（离线）
Demo 7  校验失败怎么兜底（离线）
Demo 8  生产级封装：失败不崩，降级返回

【对应手册】Part 1 · 1.4 结构化输出
【对应简历】"设计调查计划确认机制，通过 JSON Schema 与后端双重校验"

【怎么跑】
    cd studyLangChain_LangGraph/mini-project

    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_04_structured_output.py
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_04_structured_output.py --offline
    .venv/Scripts/python.exe LangChainLangGraph_workbuddy/ch01_04_structured_output.py 3

【跑之前确认】
    .env 在 mini-project/ 下，含 DASHSCOPE_API_KEY / BASE_URL / MODEL_CODE

【这个文件最重要的结论，先看这里】
    你这个网关（百炼专属实例）**不支持** json_schema 严格模式。
    llm.with_structured_output(Model) 默认走 json_schema，会直接报 ValidationError。
    必须显式写 method="function_calling"。
"""

import json
import os
import sys
from pathlib import Path
from typing import Callable, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
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
# 二、数据模型定义
#
# 这几个类放在文件顶部，多个 Demo 共用。
# 注意 Field(description=...) —— 它不是给人看的注释，
# 是【给模型看的指令】，会原样进入 schema 发给模型。
# ============================================================

class RootCause(BaseModel):
    """不良根因分析结论"""

    root_cause: str = Field(description="根本原因，一句话说清，不要罗列可能性")
    severity: Literal["high", "medium", "low"] = Field(
        description="严重程度：high=可能导致批量报废，medium=影响局部，low=外观问题"
    )
    confidence: float = Field(
        description="置信度，0 到 1 之间的小数。证据充分给 0.8 以上，靠推测给 0.5 以下",
        ge=0,
        le=1,
    )


class Evidence(BaseModel):
    """一条支撑证据"""

    source: str = Field(description="数据来源，只能是 MES / QMS / 设备参数 / 工艺文件 之一")
    content: str = Field(description="证据的具体内容，引用原始数据，不要转述")
    supports: bool = Field(description="这条证据是否支持上面的结论")


class AnalysisReport(BaseModel):
    """不良根因分析报告"""

    batch_id: str = Field(description="批次号")
    root_cause: str = Field(description="根本原因，一句话说清")
    severity: Literal["high", "medium", "low"] = Field(description="严重程度")
    evidences: list[Evidence] = Field(description="支撑证据列表，至少 1 条")
    next_actions: list[str] = Field(
        description="排查建议，按优先级从高到低排序，每条一句话"
    )


# 本文件反复用的测试问题
QUESTION = (
    "批次 B002 的不良项是焊缝气孔。"
    "MES 记录：3号线 2026-10-24 生产，操作员张三。"
    "设备参数：回流焊峰值温度 228 度（标准 235-245）。"
    "请给出根因分析报告。"
)


# ============================================================
# Demo 1 · 不用结构化输出的痛
# ============================================================

def demo1_pain_without_structured() -> None:
    show_title("Demo 1 · 不用结构化输出的痛")

    print("做法：在提示词里要求'输出 JSON'，然后自己 json.loads")
    print()

    prompt = (
        "分析下面的不良问题，输出 JSON，包含 root_cause / severity / confidence 三个字段。\n"
        "不要输出任何其他内容。\n\n"
        + QUESTION
    )

    reply = llm.invoke(prompt)
    raw_text = reply.text

    print("① 模型返回的原始文本（注意看它的'包装'）：")
    print("-" * 72)
    print(raw_text)
    print("-" * 72)

    print("\n② 直接 json.loads 会怎样：")
    try:
        parsed = json.loads(raw_text)
        print(f"   成功：{parsed}")
    except json.JSONDecodeError as e:
        print(f"   json.JSONDecodeError: {e}")
        print("   ← 十有八九是因为模型加了 ```json 包裹，或者前面写了'好的，分析如下：'")

    print("\n③ 于是你开始写补丁：剥 markdown、找第一个 {、截最后一个 }")
    cleaned = raw_text.strip()
    if "```" in cleaned:
        # 剥掉 markdown 代码块
        parts = cleaned.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{"):
                cleaned = candidate
                break
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]

    try:
        parsed = json.loads(cleaned)
        print(f"   补丁后解析成功：{parsed}")
    except json.JSONDecodeError as e:
        print(f"   补丁后仍然失败：{e}")
        parsed = None

    print("\n④ 最关键的一步：json.loads 成功，不代表数据能用")
    print("   拿解析出来的 dict 去校验 RootCause：")
    if parsed is not None:
        try:
            checked = RootCause.model_validate(parsed)
            print(f"   校验通过：{checked}")
        except ValidationError as e:
            print(f"   校验失败：{e.error_count()} 个错误")
            for err in e.errors():
                print(f"   - {err['loc']}: {err['msg']} [input={err.get('input')!r}]")
            print()
            print("   ← 看到了吗？JSON 本身是合法的，但字段值完全不能用。")
            print("     severity 给了中文'高'，confidence 给了'高' 而不是 0-1 的小数。")
            print("     你后面写 if report.confidence > 0.8 会直接 TypeError。")
            print("     这种错误最恶心：解析没报错，跑到业务逻辑深处才炸。")

    print("\n【痛点总结】这就是为什么需要 with_structured_output")
    print("  1. 模型可能加 markdown 包裹、加解释文字 → 解析失败")
    print("  2. 字段名可能被模型自己改掉（root_cause 写成 conclusion）→ 解析成功但取不到值")
    print("  3. 类型和取值不保证（severity 给'高'、confidence 给字符串）→ 后续代码崩")
    print("  4. 补丁越写越多，最后还是会有漏网的情况")
    print("")
    print("  with_structured_output 干的事：把'要求模型输出 JSON'变成")
    print("  '在 API 层面强制模型按 schema 填参数'，然后自动转成 Pydantic 对象。")
    print("")
    print("  注意区分两件事：")
    print("    json.loads        → 只保证'是合法 JSON'")
    print("    Pydantic 校验     → 保证'字段对、类型对、取值在范围内'")
    print("  前者是语法检查，后者才是业务检查。")


# ============================================================
# Demo 2 · 第一个 BaseModel
# ============================================================

def demo2_first_structured_output() -> None:
    show_title("Demo 2 · 第一个 with_structured_output")

    print("① 先看默认用法会怎样（这是坑，别急着抄）")
    try:
        structured_default = llm.with_structured_output(RootCause)
        result = structured_default.invoke(QUESTION)
        print(f"   成功了：{result}")
        print("   ← 如果你的网关支持 json_schema，就会走到这里")
    except ValidationError as e:
        print("   ValidationError:")
        for line in str(e).splitlines()[:6]:
            print(f"   {line}")
        print("   ...")
        print()
        print("   ← 这个网关【没有真正执行 json_schema 约束】：")
        print("     模型返回的东西不符合 RootCause 的字段定义。")
        print("     有时是字段名自己改了（root_cause → conclusion），")
        print("     有时干脆返回垃圾（比如只给一个 [3]）。")
        print("     行为还不稳定 —— 同一段代码跑两次，报错内容可能不一样。")

    print("\n② 正确用法：显式指定 method='function_calling'")
    structured = llm.with_structured_output(RootCause, method="function_calling")
    result = structured.invoke(QUESTION)

    print(f"   返回类型 = {type(result).__name__}")
    print(f"   root_cause = {result.root_cause}")
    print(f"   severity   = {result.severity}")
    print(f"   confidence = {result.confidence}")

    print("\n③ 拿到的是 Pydantic 对象，不是 dict")
    print("   所以可以直接点属性：result.root_cause")
    print("   也可以转 dict：result.model_dump()")
    print(f"   model_dump() = {result.model_dump()}")

    print("\n【关键理解】这一步到底发生了什么")
    print("  1. LangChain 把 RootCause 的 schema 转成'一个工具的参数定义'")
    print("  2. 发给模型时，带上 tools=[这个工具] 和 tool_choice=强制调用")
    print("  3. 模型必须按工具参数填，填错就校验不过")
    print("  4. LangChain 拿到 tool_calls 的 args，转成 RootCause 实例")
    print("")
    print("  所以它本质上是【借工具调用的机制来强制结构】。")
    print("  这也是为什么 function_calling 比 json_schema 兼容性好——")
    print("  工具调用是各家模型都支持的老功能，json_schema 是新特性。")


# ============================================================
# Demo 3 · method 三选一对比（本文件最重要）
# ============================================================

def demo3_method_comparison() -> None:
    show_title("Demo 3 · method 三选一对比")

    print("with_structured_output 有三种 method，行为完全不同：")
    print("  json_schema     （默认）用 response_format 传 schema，最严格但兼容性最差")
    print("  function_calling 借工具调用强制结构，兼容性最好")
    print("  json_mode        只要求模型输出合法 JSON，字段靠 prompt 说明，最不可靠")
    print()

    # ---------------- json_schema ----------------
    print("① method='json_schema'（也就是不写 method 的默认值）")
    try:
        s = llm.with_structured_output(RootCause, method="json_schema")
        r = s.invoke(QUESTION)
        print(f"   ✅ 成功：{r}")
    except Exception as e:
        print(f"   ❌ 失败：{type(e).__name__}")
        print(f"   {str(e).splitlines()[0]}")

    # ---------------- function_calling ----------------
    print("\n② method='function_calling'")
    try:
        s = llm.with_structured_output(RootCause, method="function_calling")
        r = s.invoke(QUESTION)
        print(f"   ✅ 成功：severity={r.severity}, confidence={r.confidence}")
    except Exception as e:
        print(f"   ❌ 失败：{type(e).__name__}: {str(e)[:100]}")

    # ---------------- json_mode ----------------
    print("\n③ method='json_mode'（不塞 schema 说明会怎样）")
    try:
        s = llm.with_structured_output(RootCause, method="json_mode")
        r = s.invoke(QUESTION)
        print(f"   ✅ 成功：{r}")
    except Exception as e:
        print(f"   ❌ 失败：{type(e).__name__}")
        print(f"   {str(e).splitlines()[0]}")
        print("   ← json_mode 只保证'输出是合法 JSON'，")
        print("     不保证字段名对。必须在 prompt 里把 schema 讲清楚才行。")

    print("\n【结论 · 记这一条就够】")
    print("  你这个环境（百炼专属实例 + deepseek-v4-flash）必须用：")
    print("      llm.with_structured_output(Model, method='function_calling')")
    print("")
    print("  换模型/换厂商时，先跑这个 Demo 3 确认哪种 method 能用，")
    print("  别假设默认值一定行——默认值失败是最浪费时间的一种坑。")


# ============================================================
# Demo 4 · 嵌套模型
# ============================================================

def demo4_nested_model() -> None:
    show_title("Demo 4 · 嵌套模型：完整的根因分析报告")

    structured = llm.with_structured_output(AnalysisReport, method="function_calling")
    report = structured.invoke(QUESTION)

    print("① 顶层字段")
    print(f"   batch_id    = {report.batch_id}")
    print(f"   severity    = {report.severity}")
    print(f"   root_cause  = {report.root_cause}")

    print("\n② 嵌套的证据列表（list[Evidence]）")
    for i, ev in enumerate(report.evidences):
        mark = "支持" if ev.supports else "不支持"
        print(f"   [{i}] 来源={ev.source} | {mark}")
        print(f"       内容={ev.content[:70]}")

    print("\n③ 排查建议（list[str]）")
    for i, action in enumerate(report.next_actions):
        print(f"   {i + 1}. {action}")

    print("\n④ 完整 dict 形式（可以直接存库 / 返回给前端）")
    print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2)[:500] + " ...")#这里是把回答结果JSON化处理

    print("\n【关键点】嵌套不是靠'让模型自己组织'，是靠 schema 逐层约束")
    print("  list[Evidence] 告诉模型：这里必须是数组，每项必须有 source/content/supports")
    print("  模型没法偷懒返回一句'证据充分'——它必须填结构化字段。")


# ============================================================
# Demo 5 · include_raw=True
# ============================================================

def demo5_include_raw() -> None:
    show_title("Demo 5 · include_raw=True：生产环境必须开")

    structured = llm.with_structured_output(
        AnalysisReport,
        method="function_calling",
        include_raw=True,     # ← 关键
    )
    result = structured.invoke(QUESTION)

    print("① 返回的不是模型对象，是一个 dict，有三个键")
    print(f"   keys = {list(result.keys())}")
    print()
    print("   raw           → 原始 AIMessage（含 tool_calls、token 用量）")
    print("   parsed        → 解析成功的 Pydantic 对象（失败时是 None）")
    print("   parsing_error → 解析失败的原因（成功时是 None）")

    print("\n② parsed 部分")
    print(f"   类型 = {type(result['parsed']).__name__}")
    print(f"   batch_id = {result['parsed'].batch_id}")

    print("\n③ parsing_error 部分")
    print(f"   {result['parsing_error']}   ← None 表示解析成功")

    print("\n④ raw 部分（这才是 include_raw 的价值）")
    raw = result["raw"]
    print(f"   类型 = {type(raw).__name__}")
    print(f"   tool_calls 个数 = {len(raw.tool_calls)}")
    if raw.tool_calls:
        print(f"   工具名 = {raw.tool_calls[0]['name']}")
        print(f"   参数键 = {list(raw.tool_calls[0]['args'].keys())}")
    print(f"   usage_metadata = {raw.usage_metadata}")

    print("\n【为什么生产必须开 include_raw】")
    print("  1. 算成本：只有 raw 里有 token 用量，parsed 对象里没有")
    print("  2. 审计：要把模型原始输出存档（合规检查要的就是这个）")
    print("  3. 调试：解析失败时，raw 里能看到模型到底返回了什么")
    print("  4. 兜底：解析失败但 raw 有内容时，可以自己再救一次")

    print("\n【注意】开了 include_raw 之后，取值要改")
    print("   不开：result.root_cause")
    print("   开了：result['parsed'].root_cause   ← 多一层")
    print("   很多人开了之后忘记改取值方式，报 AttributeError: 'dict' object has no attribute")


# ============================================================
# Demo 6 · model_json_schema（离线）
#
# 这一节直接对应简历里的"JSON Schema 与后端双重校验"
# ============================================================

def demo6_json_schema() -> None:
    show_title("Demo 6 · model_json_schema()：双重校验的落地依据（离线）")

    schema = AnalysisReport.model_json_schema()

    print("① Pydantic 模型生成的 JSON Schema")
    print(json.dumps(schema, ensure_ascii=False, indent=2))

    print("\n② 关键字段解读")
    print(f"   顶层 required = {schema.get('required')}")
    print("   ← 列在这里的字段是必填的，模型必须给")

    severity_schema = schema["properties"]["severity"]
    print(f"\n   severity 的约束 = {json.dumps(severity_schema, ensure_ascii=False)}")
    print("   ← Literal 被转成了 enum，模型只能从这三档里选")

    print("\n   $defs 里是嵌套模型的独立定义：")
    print(f"   {list(schema.get('$defs', {}).keys())}")
    print("   ← Evidence 被抽出来单独定义，然后在 evidences 里用 $ref 引用")

    print("\n【这就是'双重校验'的第一重】")
    print("  前端 / 后端拿到这份 schema，可以做：")
    print("    1. 渲染表单（字段名 + 描述 + 枚举值都有了）")
    print("    2. 提交前校验（用户改完的计划，先按 schema 校验一遍）")
    print("    3. 版本管理（schema 变了能 diff 出来）")
    print("")
    print("  第二重校验是模型侧：with_structured_output 让模型必须按 schema 输出。")
    print("  两重加起来，才是'模型给的结构可信'。")

    print("\n【面试可以直接这么说】")
    print("  '我们用 Pydantic 定义调查计划的 Schema，通过 model_json_schema()")
    print("   导出给前端做表单渲染和后端入库前校验；模型侧用 with_structured_output")
    print("   强制按同一份 schema 生成，两边共用一份定义，不会漂移。'")


# ============================================================
# Demo 7 · 校验失败怎么兜底（离线）
# ============================================================

def demo7_validation_failure() -> None:
    show_title("Demo 7 · 校验失败长什么样、怎么兜底（离线）")

    print("① 故意传一个字段名不对的 dict")
    bad_data = {
        "conclusion": "温度偏低",     # 应该是 root_cause
        "severity": "high",
        "confidence": 0.9,
    }
    try:
        RootCause.model_validate(bad_data)
    except ValidationError as e:
        print(f"   ValidationError: {e.error_count()} 个错误")
        for err in e.errors():
            print(f"   - 字段 {err['loc']}: {err['msg']} [{err['type']}]")

    print("\n② 故意传一个超范围的值")
    bad_range = {
        "root_cause": "温度偏低",
        "severity": "high",
        "confidence": 1.5,          # 超过 le=1
    }
    try:
        RootCause.model_validate(bad_range)
    except ValidationError as e:
        for err in e.errors():
            print(f"   - 字段 {err['loc']}: {err['msg']} [input={err.get('input')}]")

    print("\n③ 故意传一个枚举外的值")
    bad_enum = {
        "root_cause": "温度偏低",
        "severity": "critical",     # 不在 high/medium/low 里
        "confidence": 0.9,
    }
    try:
        RootCause.model_validate(bad_enum)
    except ValidationError as e:
        for err in e.errors():
            print(f"   - 字段 {err['loc']}: {err['msg']}")

    print("\n【关键理解】Pydantic 是【运行时】校验，不是类型注解")
    print("  Python 的 : str 注解只是注释，运行时不检查。")
    print("  只有 Pydantic 会在运行时真的拦住错误数据。")
    print("  这就是为什么 1.4 比 1.2/1.3 重要 —— 它是唯一真正'强制'的一层。")

    print("\n【生产上的处理原则】")
    print("  校验失败不要直接抛给用户，分三种情况：")
    print("    1. 偶发（模型抽风）→ 重试一次")
    print("    2. 系统性（schema 和模型不匹配）→ 换 method 或简化 schema")
    print("    3. 数据问题（原始数据本身缺失）→ 返回'信息不足'，别硬编")


# ============================================================
# Demo 8 · 生产级封装
# ============================================================

def demo8_production_wrapper() -> None:
    show_title("Demo 8 · 生产级封装：失败不崩，降级返回")

    def analyze_safely(
        question: str,
        max_retries: int = 2,
        method: str = "function_calling",
    ) -> dict:
        """生产级的根因分析封装。

        返回固定结构的 dict，永不抛异常。
        调用方不需要 try/except，也不用关心底层是哪种失败。
        """
        structured = llm.with_structured_output(
            AnalysisReport,
            method=method,
            include_raw=True,
        )

        last_error = ""
        for attempt in range(max_retries):
            try:
                result = structured.invoke(question)

                # 情况 1：解析成功
                if result["parsed"] is not None:
                    return {
                        "ok": True,
                        "data": result["parsed"].model_dump(),
                        "error": None,
                        "attempts": attempt + 1,
                        "tokens": (result["raw"].usage_metadata or {}).get("total_tokens"),
                    }

                # 情况 2：模型答了但解析失败
                last_error = str(result["parsing_error"])
                print(f"   [重试 {attempt + 1}] 解析失败：{last_error[:80]}")

            except Exception as e:
                # 情况 3：调用本身失败（网络 / 限流 / 模型报错）
                last_error = f"{type(e).__name__}: {str(e)[:100]}"
                print(f"   [重试 {attempt + 1}] 调用失败：{last_error[:80]}")

        # 全部失败 → 降级返回，不抛异常
        return {
            "ok": False,
            "data": None,
            "error": last_error,
            "attempts": max_retries,
            "tokens": None,
        }

    print("① 正常情况")
    ok_result = analyze_safely(QUESTION)
    print(f"   ok       = {ok_result['ok']}")
    print(f"   attempts = {ok_result['attempts']}")
    print(f"   tokens   = {ok_result['tokens']}")
    if ok_result["data"]:
        print(f"   batch_id = {ok_result['data']['batch_id']}")
        print(f"   severity = {ok_result['data']['severity']}")

    print("\n② 失败情况（用已知不被这个网关支持的 json_schema）")
    fail_result = analyze_safely(QUESTION, max_retries=1, method="json_schema")
    print(f"   ok    = {fail_result['ok']}")
    print(f"   data  = {fail_result['data']}")
    print(f"   error = {(fail_result['error'] or '')[:90]}")

    print("\n   ← 注意这里：调用方只看到 ok=False，")
    print("     不用关心是 ValidationError 还是网络错误。")
    print("     真实业务里就该在这里返回'分析失败，请人工介入'，")
    print("     而不是把异常抛到接口层，让前端看到 500。")

    print("\n【为什么这么写】")
    print("  1. 返回值结构固定：调用方只判断 ok，不用处理各种异常类型")
    print("  2. 永不抛异常：Agent 主循环不会因为一次结构化失败就整个崩掉")
    print("  3. 带 attempts：能看出是'一次成功'还是'重试后成功'，用于监控")
    print("  4. 带 tokens：每次调用的成本可统计")
    print("")
    print("  这正是模块 E 讲的'在 Agent 里，错误不是终点，是给模型的一条信息'。")
    print("  但结构化输出这一步失败，通常不该回填给模型——而是本地重试或降级。")


# ============================================================
# 三、入口
# ============================================================

DEMOS: list[tuple[str, str, Callable[[], None], bool]] = [
    ("1", "不用结构化输出的痛", demo1_pain_without_structured, True),
    ("2", "第一个 with_structured_output", demo2_first_structured_output, True),
    ("3", "method 三选一对比", demo3_method_comparison, True),
    ("4", "嵌套模型", demo4_nested_model, True),
    ("5", "include_raw", demo5_include_raw, True),
    ("6", "model_json_schema", demo6_json_schema, False),
    ("7", "校验失败与兜底", demo7_validation_failure, False),
    ("8", "生产级封装", demo8_production_wrapper, True),
]


def main() -> None:
    args = sys.argv[1:]
    offline_only = "--offline" in args
    picked = [a for a in args if a.isdigit()]

    print("=" * 72)
    print(f"1.4 结构化输出 | 模型 = {MODEL_CODE}")
    print("重要：本环境必须用 method='function_calling'")
    if offline_only:
        print("模式：--offline（只跑 Demo 6/7）")
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
