# LangChain / LangGraph 核心学习步骤（求职向 · 对齐简历）

> **目标**：4 天形成肌肉记忆，面试能讲清"为什么这么设计"，而不只是"我用了什么 API"
> **精力分配**：LangChain **30%** / LangGraph **70%**
> **核心判断**：LangGraph 是面试出彩点，LangChain 只是底座

---

# 一、先明确：学什么、不学什么

**省 50% 时间的关键在这一节。**

## 1.1 直接跳过（旧 API，学了浪费时间）

| 跳过 | 原因 |
|---|---|
| `LLMChain` / `SequentialChain` / `ConversationChain` | 已被 LCEL 取代 |
| `initialize_agent` / `AgentExecutor` | 官方已不推荐，生产级用 LangGraph |
| 老式 Memory（`ConversationBufferMemory` 等） | 已废弃，用 checkpointer |

> **判断方法**：看到教程里出现上面这些名字，直接关掉——那是 0.x 时代的写法。

## 1.2 不必在 Python 重学的

**RAG 的文档加载与切片封装** —— Java 项目里已实现异步入库 + 分片维护，面试讲 Java 实现即可。

> 但**RAG 的概念要能讲**（切块策略、召回质量、幻觉治理），只是不用在 Python 里再写一遍 `DocumentLoader`。

## 1.3 精力分配

| 模块 | 精力 | 定位 |
|---|---|---|
| LangChain | **30%** | 调用模型 + 定义工具 + 结构化输出 |
| LangGraph | **70%** | 流程控制 + 状态管理 + 人工介入 |

---

# 二、四者关系（面试第一问）

| 名字 | 是什么 | 什么时候用 |
|---|---|---|
| **LangChain** | 高层封装，`create_agent` 一把梭 | 快速搭 Agent |
| **LangGraph** | 底层编排，用图控制流程 | **需要精确控制**（你的场景） |
| **LangSmith** | 追踪 / 评估平台 | 调试和评测 |
| **Deep Agents** | 开箱即用的 Agent | 复杂任务、不想自己搭 |

**关键关系**：

> `create_agent` 内部就是一张 LangGraph 图。LangChain 给你现成的图，LangGraph 给你画图的笔。

**你的场景为什么必须用 LangGraph**：

需要"人工审批"、"固定流程"、"状态持久化"、"子图隔离"——这四样 `create_agent` 都给不了。

---

# 三、LangChain 核心（30% 精力）

## 3.1 LCEL 与 Runnable 协议

### 学什么

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是{biz}领域专家"),
    ("human", "{question}"),
])

chain = prompt | ChatOpenAI(model="gpt-4o") | StrOutputParser()

result = chain.invoke({"biz": "制造业质量", "question": "什么是根因分析"})
```

**`|` 的含义**：左边输出 → 右边输入。所有组件都实现 `Runnable` 协议，所以能串。

### 三种调用方式

| 方法 | 用途 |
|---|---|
| `.invoke()` | 同步，一次性 |
| `.ainvoke()` | 异步，Web 服务必须用 |
| **`.astream_events()`** | **流式事件，SSE 的底层** |

### `astream_events` 怎么用（面试重点）

```python
async for event in chain.astream_events(
    {"biz": "制造业质量", "question": "分析3号线不良"},
    version="v2",
):
    kind = event["event"]

    if kind == "on_chat_model_stream":
        # 模型逐 token 输出 → 推给前端做打字机
        print(event["data"]["chunk"].content, end="", flush=True)

    elif kind == "on_tool_start":
        # 工具开始执行 → 前端显示"正在查询工单..."
        print(f"\n[工具] {event['name']} 开始")

    elif kind == "on_tool_end":
        print(f"[工具] {event['name']} 结束")
```

**为什么这个 API 关键**：它不只给你 token，还给你**工具调用状态**。前端可以显示"正在查询工单..."这种进度提示。

### 面试会怎么问

> "Python 的 LangGraph 怎么配合 Java 后端实现 SSE 流式输出与游标补拉？"

**答题要点**：
> "底层用 `astream_events` 捕获三类事件：`on_chat_model_stream` 拿 token 流推给前端做打字机，`on_tool_start` / `on_tool_end` 拿工具状态做进度提示。每条事件带 `run_id`，Java 侧按 `run_id` 做游标，断线后传上次的游标补拉。"

**注意**：LCEL 本身了解即可（`|` 的含义），**重点在 `astream_events`**。

## 3.2 结构化输出（Pydantic + with_structured_output）

### 学什么

```python
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """一个调查步骤"""
    step_id: int = Field(description="步骤序号")
    action: str = Field(description="要做什么，例如'查询3号线工单'")
    tool_name: str = Field(description="要调用的工具名")
    params: dict = Field(default_factory=dict, description="工具参数")


class InvestigationPlan(BaseModel):
    """调查计划"""
    root_question: str = Field(description="要调查的核心问题")
    steps: list[PlanStep] = Field(description="待执行的步骤列表")
    reasoning: str = Field(description="为什么这么规划")


# 强制模型输出符合 Schema 的对象
structured_llm = llm.with_structured_output(InvestigationPlan)
plan = structured_llm.invoke("3号产线昨天有5个批次不良，帮我规划调查步骤")

print(plan.root_question)
for s in plan.steps:
    print(f"{s.step_id}. {s.action} → {s.tool_name}({s.params})")
```

### 底层发生了什么

`with_structured_output` 做三件事：
1. 把 Pydantic 模型转成 **JSON Schema**（`model_json_schema()`）
2. 把 Schema 塞进请求，告诉模型"必须按这个格式输出"
3. 拿到结果后**用 Pydantic 校验**，不合法会重试或报错

### 面试会怎么问

> "你怎么保证大模型输出的是结构化数据？"

**答题要点**：
> "用 Pydantic 定义 `InvestigationPlan`，字段都带 `Field(description=...)` 让模型理解语义，然后 `llm.with_structured_output(InvestigationPlan)`。底层是把 Pydantic 转成 JSON Schema 约束模型输出，拿到结果再用 Pydantic 校验一遍。后端收到后还会做**业务层二次校验**——Schema 只能保证格式对，不能保证业务合理（比如工具名是否在白名单里）。"

**最后那句"双重校验"是简历亮点，一定要说。**

## 3.3 工具定义与动态绑定

### 基础：`@tool`

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class QueryBatchArgs(BaseModel):
    batch_no: str = Field(description="批次号，例如 B002")
    fields: list[str] = Field(default=["defect", "params"], description="要查的字段")


@tool(args_schema=QueryBatchArgs)
def query_erp_batch(batch_no: str, fields: list[str]) -> str:
    """查询 ERP 批次记录。

    适用于：已知批次号，需要查看该批次的质检数据、工艺参数、操作记录。
    """
    # 假数据，真实场景查 ERP
    return f"{batch_no} 质检结果：回流焊峰值温度 228°C（标准 235-245°C）"
```

**`args_schema` 的作用**：用 Pydantic 定义参数结构，比只写类型注解更严格（能加 `description`、默认值、校验规则）。

### 关键技巧：运行时动态绑定（简历亮点）

**问题**：工具太多，模型会乱调。

**解法**：**按当前计划只绑定允许的工具**。

```python
ALL_TOOLS = {
    "query_erp_batch": query_erp_batch,
    "query_workorder": query_workorder,
    "query_bom": query_bom,
    "delete_record": delete_record,          # 危险工具
}


def build_llm_for_step(plan_step: dict):
    """根据当前步骤，只绑定这一步允许的工具"""
    allowed_name = plan_step["tool_name"]

    # 白名单过滤：只把允许的工具给模型
    if allowed_name not in ALL_TOOLS:
        raise ValueError(f"工具不在白名单: {allowed_name}")

    return llm.bind_tools([ALL_TOOLS[allowed_name]])
```

**为什么这样有效**：模型**看不到**未绑定的工具，就不可能调它。这比在 prompt 里写"不要调用 XX"可靠一百倍。

### MCP 工具接入

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "erp": {"url": "http://mcp-server/sse", "transport": "sse"},
})

tools = await client.get_tools()      # 拿到 MCP 工具列表
# 之后按名字过滤、注册到白名单
```

### 面试会怎么问

> "怎么解决 Agent 乱调无关工具？"

**答题要点**：
> "两个层面：**注册层**用 MCP 工具发现 + 白名单注册，只有白名单里的工具才进入工具池；**执行层**用 `bind_tools` 按当前计划步骤动态绑定，只把这一步允许的工具给模型。模型看不到的工具就不可能调——这比在 prompt 里约束可靠得多。"

## 3.4 LangChain 部分的边界

**不学的**：
- 各种 Chain 类型（已被 LCEL 取代）
- `DocumentLoader` / `TextSplitter`（RAG 讲 Java 实现）
- 老式 Memory
- `create_agent` 的用法（你的场景直接用 LangGraph，但**要知道它存在**，面试可能问关系）

---

# 四、LangGraph 核心（70% 精力）

**这是面试出彩的地方。四大痛点在这里都有原生解法。**

## 4.1 StateGraph 三要素

### ① State：全局状态

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]   # 追加
    plan: dict | None                                       # 覆盖
    evidence: Annotated[list[dict], add_messages]           # 追加
    approved: bool                                          # 覆盖
    retry_count: int                                        # 覆盖
```

**关键理解**：**不是所有字段都要 reducer**。

| 字段类型 | 要不要 reducer | 原因 |
|---|---|---|
| 消息列表 | ✅ 要 | 要累积历史 |
| 证据列表 | ✅ 要 | 要累积多条证据 |
| 当前计划 | ❌ 不要 | 新计划应该覆盖旧的 |
| 审批状态 | ❌ 不要 | 只保留最新值 |

### ② Reducer：合并规则

```python
# 没有 Annotated → 默认覆盖
class State1(TypedDict):
    messages: list          # 节点返回新列表，旧的没了

# 有 Annotated → 用 add_messages 合并
class State2(TypedDict):
    messages: Annotated[list, add_messages]   # 追加
```

**面试必背**：
> "默认情况下节点返回同名字段会**直接覆盖**原状态。用 Reducer 才能实现**增量追加**——比如消息历史和证据列表，必须累积而不是覆盖。但像'当前计划'、'审批状态'这类字段，反而应该覆盖，所以不加 reducer。"

**注意最后那句**——能说出"不是所有字段都该加 reducer"，比只说"要加"深一层。

### ③ 节点与条件边

```python
from langgraph.graph import StateGraph, START, END


def plan_node(state: AgentState) -> dict:
    """生成调查计划"""
    plan = structured_llm.invoke(state["messages"])
    return {"plan": plan.model_dump()}


def tool_node(state: AgentState) -> dict:
    """执行计划里的工具"""
    plan = state["plan"]
    results = []
    for step in plan["steps"]:
        tool = ALL_TOOLS[step["tool_name"]]
        results.append({
            "step_id": step["step_id"],
            "result": tool.invoke(step["params"]),
        })
    return {"evidence": results}


def verify_node(state: AgentState) -> dict:
    """校验证据是否充分"""
    if len(state["evidence"]) >= 2:
        return {"retry_count": 0}
    return {"retry_count": state.get("retry_count", 0) + 1}


def route_after_verify(state: AgentState) -> str:
    """校验通过就结束，不通过打回重新规划（最多 3 次）"""
    if state.get("retry_count", 0) >= 3:
        return END                              # 超限降级
    if len(state["evidence"]) >= 2:
        return END
    return "plan"                               # 打回重来
```

**建图**：

```python
builder = StateGraph(AgentState)

builder.add_node("plan", plan_node)
builder.add_node("tool", tool_node)
builder.add_node("verify", verify_node)

builder.add_edge(START, "plan")
builder.add_edge("plan", "tool")
builder.add_edge("tool", "verify")
builder.add_conditional_edges(
    "verify",
    route_after_verify,
    {"plan": "plan", END: END},
)

graph = builder.compile()
```

**图结构**：

```
START → plan → tool → verify ─┬─(证据不足)→ plan（重试）
                              └─(证据够 或 超限)→ END
```

**这就把"不可控的自由 ReAct 循环"变成了"受控的流程图"。**

### 面试会怎么问

> "为什么 State 里的列表要用 Annotated 配合 Reducer？"

**答题要点**：见上面"面试必背"。

> "条件边怎么工作？"

**答题要点**：路由函数读 state 返回字符串，LangGraph 按字符串查映射表跳转。返回值必须在映射表 key 里。

## 4.2 Checkpointer：状态持久化

### 学什么

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "investigation-20261024-001"}}

# 第一次执行
result = graph.invoke({"messages": [HumanMessage(content="3号线有5个批次不良")]}, config)

# 第二次：能接着上次的状态
result2 = graph.invoke({"messages": [HumanMessage(content="继续查质检")]}, config)
```

### 底层机制（面试重点）

> **图每执行完一个 Node（一个 Super-step），Checkpointer 就把当前 State 快照序列化落库，并绑定 `thread_id`。**

**这意味着**：
- 服务重启 → 传同一个 `thread_id` 就能恢复
- 跨天审批 → 状态一直在，随时续跑
- 时间旅行 → 能回看任意一步的状态

### 生产环境怎么存

| Saver | 场景 |
|---|---|
| `MemorySaver` | 本地测试，重启丢失 |
| `SqliteSaver` | 单机持久化 |
| `PostgresSaver` | 生产（官方推荐） |
| **自定义 `BaseCheckpointSaver`** | **你的场景：MySQL** |

**自定义 Saver 的核心是实现三个方法**：

```python
from langgraph.checkpoint.base import BaseCheckpointSaver


class MySQLCheckpointSaver(BaseCheckpointSaver):
    def get_tuple(self, config):
        """按 thread_id + checkpoint_id 读回状态"""
        ...

    def put(self, config, checkpoint, metadata, new_versions):
        """把 State 快照序列化写表"""
        ...

    def list(self, config, **kwargs):
        """列出某个 thread 的所有检查点"""
        ...
```

### 面试会怎么问

> "Agent 服务重启了，正在跑的流程怎么办？"

**答题要点**：
> "用 checkpointer。图每执行完一个节点就自动把 State 快照落库并绑定 `thread_id`，服务重启后传同一个 `thread_id` 就能从断点恢复。我们用的是自定义 `BaseCheckpointSaver` 存 MySQL。"

## 4.3 Human-in-the-Loop：断点续跑

### 两种中断方式

**方式 A · 编译时静态指定**

```python
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["tool"],       # 执行 tool 节点前暂停
)
```

**方式 B · 节点内动态调用**（更灵活，推荐）

```python
from langgraph.types import interrupt


def approval_node(state: AgentState) -> dict:
    """等人工确认计划"""
    decision = interrupt({
        "type": "plan_approval",
        "plan": state["plan"],
        "question": "是否批准执行这个调查计划？",
    })

    if decision.get("action") == "reject":
        return {"approved": False, "plan": None}

    # 允许人工微调计划
    if decision.get("action") == "modify":
        return {"approved": True, "plan": decision["new_plan"]}

    return {"approved": True}
```

**区别**：

| 方式 | 特点 | 适用 |
|---|---|---|
| `interrupt_before` | 编译时定死，简单 | 固定在某节点前暂停 |
| `interrupt()` | 节点内调用，能带上下文、能返回值 | **需要把计划内容给人看** |

### 完整流程

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "inv-001"}}

# ① 跑到 interrupt 处挂起
result = graph.invoke({"messages": [...]}, config)

# ② 查看挂起状态
state = graph.get_state(config)
print(state.next)              # 下一步要去哪个节点
print(state.tasks)             # 里面就有 interrupt 传出的数据（计划内容）

# ③ 人工审批后恢复
result = graph.invoke(
    Command(resume={"action": "approve"}),
    config,
)
```

### 关键理解

**挂起时会释放计算资源** —— 不是"线程卡在那里等"，而是"状态存库，进程可以去干别的"。这对跨天审批是必须的。

### 面试会怎么问

> "审批环节怎么做？"

**答题要点**：
> "用 LangGraph 的 `interrupt`。图执行到审批节点时挂起，把当前 State 和待审批内容存进 checkpointer 并释放资源。前端拿到计划内容展示给业务人员，确认或微调后后端用 `Command(resume=...)` 唤醒这个 `thread_id`，从断点继续执行。**关键是状态在库里，不是进程在等**，所以支持跨天审批。"

## 4.4 SubGraph 与 recursion_limit

### SubGraph：子图隔离

**问题**：子 Agent 跑多轮只读查询，会产生大量原始数据（成百上千行 ERP 记录），如果全塞进父图 State，父图上下文会被污染。

**解法**：把子 Agent 编译成独立子图，作为父图的一个节点。

```python
# ① 定义子图（独立 State）
class ResearchState(TypedDict):
    query: str
    raw_results: Annotated[list, add_messages]      # 大量原始数据，只在子图内
    conclusion: str


def research_node(state: ResearchState) -> dict:
    # 多轮查询，raw_results 越攒越多
    ...


sub_builder = StateGraph(ResearchState)
sub_builder.add_node("research", research_node)
sub_builder.add_edge(START, "research")
sub_builder.add_edge("research", END)
sub_graph = sub_builder.compile()


# ② 作为节点塞进父图
builder.add_node("research", sub_graph)
```

**父子 State 怎么映射**：

父图调用子图时，会把**同名字段**传进去，子图返回时也只把**父图 State 里有的字段**写回。

```python
class ParentState(TypedDict):
    messages: Annotated[list, add_messages]
    conclusion: str          # ← 和子图同名，会被写回

class ResearchState(TypedDict):
    query: str
    raw_results: list        # ← 父图没有这个字段，不会写回
    conclusion: str          # ← 父图有，会写回
```

**效果**：`raw_results` 里的成百上千行脏数据**留在子图内部消化**，父图只拿到提炼后的 `conclusion`。

### `recursion_limit`

```python
result = graph.invoke(
    {"messages": [...]},
    config={
        "configurable": {"thread_id": "inv-001"},
        "recursion_limit": 5,           # 最多 5 个 Super-step
    },
)
```

**超限会抛**：

```python
from langgraph.errors import GraphRecursionError

try:
    result = graph.invoke(inputs, config)
except GraphRecursionError:
    # 降级兜底：返回"需要人工介入"
    ...
```

### 面试会怎么问

> "子 Agent 回传一堆无关数据怎么办？"

**答题要点**：
> "用 SubGraph。子图有**独立的私有 State**，多轮查询产生的原始数据全留在子图内部，只把提炼后的结论快照通过同名字段写回父图。这样父图的上下文不会被脏数据污染。"

> "怎么防止 Agent 无限循环？"

**答题要点**：
> "三层：① `recursion_limit` 硬限制 Super-step 数，超了抛 `GraphRecursionError`，捕获后降级为人工介入；② 条件边里判断重试次数，超过阈值直接走 END；③ 工具层面返回明确错误，让模型知道'查不到了'而不是一直重试。"

---

# 五、四大痛点的 LangGraph 解法（面试王牌）

**这一节是核心竞争力，建议背下来。**

| 简历痛点 | LangGraph 解法 | 面试话术 |
|---|---|---|
| **循环调用** | `recursion_limit` + 条件边重试计数 | "用 `recursion_limit` 硬限制 Super-step 数，超限捕获 `GraphRecursionError` 降级；条件边里也判断重试次数，双保险" |
| **乱调无关工具** | `bind_tools(allowed_tools)` 运行时动态绑定 | "按当前计划步骤动态绑定白名单工具，模型看不到的工具不可能调——比 prompt 约束可靠得多" |
| **审批失效** | `interrupt()` + checkpointer | "图执行到审批节点挂起，状态落库并释放资源，人工确认后用 `Command(resume)` 唤醒同一 `thread_id` 续跑。状态在库里不是进程在等，所以支持跨天审批" |
| **子 Agent 回传无关数据** | SubGraph 独立 State | "子图用私有 State 跑多轮只读查询，成百上千行原始数据留在子图内部消化，只把提炼后的结论快照写回父图" |

## 面试时的组织方式（2 分钟口述）

> "我们这套系统最大的挑战是**Agent 不可控**。传统 ReAct 循环是黑盒，模型想调什么调什么，想跑多久跑多久。
>
> 我们用 LangGraph 把它拆成了受控的流程图：**生成计划 → 人工审批 → 工具执行 → 证据校验**，每个环节都是显式节点。
>
> 具体四个治理点：循环用 `recursion_limit` 加条件边重试计数双保险；工具乱调用运行时 `bind_tools` 白名单；审批用 `interrupt` 加 checkpointer 实现断点续跑；子 Agent 用 SubGraph 的独立 State 隔离脏数据。"

---

# 六、4 天实战路线

**原则：不连真实 ERP，全部用假数据函数。目标是形成肌肉记忆，不是做项目。**

## Day 1 · LangChain 底座

**装包**：

```bash
pip install langchain-core langchain-openai langgraph python-dotenv
```

> 兼容 DeepSeek / 千问：`ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1")`

**写什么**：

1. 一个带 Pydantic 入参校验的 `@tool` 假函数

```python
class QueryBatchArgs(BaseModel):
    batch_no: str = Field(description="批次号，例如 B002")


@tool(args_schema=QueryBatchArgs)
def query_erp_batch(batch_no: str) -> str:
    """查询 ERP 批次记录。"""
    return f"{batch_no} 质检结果：回流焊峰值温度 228°C（标准 235-245°C）"
```

2. 用 `with_structured_output` 让模型输出结构化的调查计划

```python
class PlanStep(BaseModel):
    step_id: int
    action: str
    tool_name: str
    params: dict = Field(default_factory=dict)


class InvestigationPlan(BaseModel):
    root_question: str
    steps: list[PlanStep]
    reasoning: str


structured_llm = llm.with_structured_output(InvestigationPlan)
plan = structured_llm.invoke("3号线有5个批次不良，规划调查步骤")
print(plan.model_dump_json(indent=2))
```

3. 用 `astream_events` 看流式事件

```python
async for event in llm.astream_events("你好", version="v2"):
    print(event["event"], event.get("name", ""))
```

**验收**：能拿到结构化的 `InvestigationPlan` 对象，且能打印出 `astream_events` 的事件类型。

## Day 2 · 最小 StateGraph

**写什么**：三节点图 + 条件边重试

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    plan: dict | None
    evidence: Annotated[list, add_messages]
    retry_count: int
```

- `plan_node`：生成计划
- `tool_node`：执行计划里的工具（假数据）
- `verify_node`：校验证据是否充分

**条件边**：校验不通过 → 打回 `plan`，最多 3 次。

**验收**：故意让 `verify_node` 返回"不充分"，观察它循环 3 次后停止（打印出 `retry_count`）。

## Day 3 · Checkpointer + 人工审批

**写什么**：

1. 加 `MemorySaver`，用 `thread_id` 跑两次，验证能记住上下文
2. 加 `interrupt_before=["tool"]`，在控制台模拟：

```python
# ① 跑到挂起
graph.invoke(inputs, config)

# ② 打印挂起状态
state = graph.get_state(config)
print("下一步:", state.next)
print("当前计划:", state.values["plan"])

# ③ 输入同意后继续
graph.invoke(None, config)      # 或 Command(resume=...)
```

**验收**：能在控制台看到"挂起 → 打印计划 → 输入继续 → 执行完"的完整流程。

## Day 4 · SubGraph 隔离

**写什么**：

1. 写一个只读子图（只有 `query_erp_batch` 一个工具，跑多轮查询，`raw_results` 越攒越多）
2. 作为节点塞进 Day 3 的主图
3. 打印父图 State，**确认看不到 `raw_results`**

**验收**：父图 State 里只有 `conclusion`，没有 `raw_results`。

**最后一步**：对照第五节的"四大痛点"表格，把这套代码串成 2 分钟的面试口述。

---

# 七、面试高频问题

## LangChain 相关

**1. LangChain 和 LangGraph 什么关系？**
> LangChain 是高层 API，LangGraph 是底层编排。`create_agent` 内部就是一张 LangGraph 图。需要精确控制流程时下到 LangGraph。

**2. `with_structured_output` 底层做了什么？**
> 把 Pydantic 模型转成 JSON Schema 塞进请求约束输出，拿到结果再用 Pydantic 校验。**Schema 只保证格式，业务合理性要二次校验。**

**3. 怎么解决工具乱调用？**
> 注册层 MCP 白名单 + 执行层 `bind_tools` 动态绑定。模型看不到的工具不可能调。

**4. `astream_events` 和 `astream` 有什么区别？**
> `astream` 只给 LLM 的 token 流；`astream_events` 给**所有组件的事件**（模型 token、工具开始/结束、链的中间步骤），能拿 `run_id` 做游标。

## LangGraph 相关

**5. 为什么 State 里的列表要用 `Annotated` 配合 Reducer？**
> 默认节点返回同名字段会**覆盖**原状态。用 Reducer 才能增量追加——消息历史和证据必须累积。但"当前计划""审批状态"这类字段反而该覆盖，所以不是所有字段都加。

**6. 条件边怎么工作？**
> 路由函数读 state 返回字符串，LangGraph 按字符串查映射表跳转。返回值必须在映射表 key 里。

**7. Checkpointer 是怎么工作的？**
> 图每执行完一个 Super-step，就把 State 快照序列化落库并绑定 `thread_id`。服务重启后传同一个 `thread_id` 就能恢复。

**8. 状态存哪里？**
> `MemorySaver` 测试用；生产用 `PostgresSaver`；我们的场景是自定义 `BaseCheckpointSaver` 存 MySQL。

**9. `interrupt` 和 `interrupt_before` 有什么区别？**
> `interrupt_before` 是编译时静态指定在某节点前暂停；`interrupt()` 是节点内动态调用，能传出上下文（比如计划内容）并接收返回值。需要人工看内容、改内容时用后者。

**10. 挂起时进程在等吗？**
> **不是。** 状态存库后释放资源，进程可以去干别的。这是跨天审批能实现的前提。

**11. SubGraph 怎么隔离数据？**
> 子图有独立 State，父图调用时只传同名字段，子图返回时也只写回父图有的字段。所以子图内部的 `raw_results` 不会污染父图。

**12. 怎么防死循环？**
> `recursion_limit` 硬限制 + 条件边重试计数 + 工具返回明确错误。超限捕获 `GraphRecursionError` 降级。

## 开放题

**13. 设计一个"调查计划确认"的 Agent，你怎么做？**
> ① State 里放 `plan` / `evidence` / `approved` / `retry_count`
> ② 图：`plan → approval → tool → verify`，`approval` 用 `interrupt()` 挂起
> ③ 工具用 `bind_tools` 按计划步骤动态绑定
> ④ 校验用 Pydantic + 业务层二次校验
> ⑤ `verify` 不通过打回 `plan`，`recursion_limit` 兜底
> ⑥ checkpointer 存 MySQL，支持断点续跑

---

# 八、明确不学的部分

| 不学 | 理由 |
|---|---|
| `LLMChain` / `SequentialChain` / `ConversationChain` | 已废弃 |
| `initialize_agent` / `AgentExecutor` | 官方不推荐，用 LangGraph |
| LangChain 的 `DocumentLoader` / `TextSplitter` | RAG 讲 Java 实现 |
| 老式 Memory 类 | 已废弃，用 checkpointer |
| Deep Agents 细节 | 太新，面试官未必了解 |
| LangServe / LangGraph Cloud | 部署相关，少问 |
| 多 Agent 框架（CrewAI / AutoGen） | 先把单 Agent 吃透 |
| 微调 | 90% 场景 prompt + RAG 就够 |

---

# 最后

**这份文档的核心不是"学完所有 API"，是"能讲清为什么这么设计"。**

简历里的四大痛点，在 LangGraph 里都有原生解法——**这比"我会用 LangChain"值钱得多**。

面试官不会因为你背出了 `add_conditional_edges` 的签名就录用你，但会因为你能说清"为什么把不可控的 ReAct 循环拆成受控流程图"而记住你。

**技术是门槛，判断力是差异。**
