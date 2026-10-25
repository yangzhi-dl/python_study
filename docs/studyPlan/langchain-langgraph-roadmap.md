# LangChain / LangGraph 学习路线（能力栈 ②③④）

> **前置**：Python 基础模块 A–G 已学完
> **这一阶段的标准和之前不同**：框架层不追求"会写"，追求「**看懂 + 能改 + 能设计**」
> **最终目标**：能独立做出「不良品根因追溯智能体」的可运行版本

---

## 文档地址速查（2026-10 已核对）

### 官方英文文档（唯一权威）

| 用途 | 地址 |
|---|---|
| 总入口 | `https://docs.langchain.com/` |
| **LangChain Python 概览** | `https://docs.langchain.com/oss/python/langchain/overview` |
| LangChain 安装 | `https://docs.langchain.com/oss/python/langchain/install` |
| **LangChain 快速开始** | `https://docs.langchain.com/oss/python/langchain/quickstart` |
| **LangGraph Python 概览** | `https://docs.langchain.com/oss/python/langgraph/overview` |
| Deep Agents（开箱即用） | `https://docs.langchain.com/oss/python/deepagents/overview` |
| LangSmith 可观测性 | `https://docs.langchain.com/langsmith/observability` |
| API 参考 | `https://reference.langchain.com/python/langgraph` |

### GitHub

- LangChain：`https://github.com/langchain-ai/langchain`
- LangGraph：`https://github.com/langchain-ai/langgraph`

### 中文资源（多为旧版翻译）

| 资源 | 说明 |
|---|---|
| `https://langchain.cadn.net.cn/` | 社区翻译，**可能停留在 0.x 版本** |
| `https://m.runoob.com/ai-agent/langgraph-quick-start.html` | 菜鸟教程的 LangGraph 入门 |

> ⚠️ **LangChain 在 2025 年底发布了 1.0，API 结构有较大变化。** 中文翻译普遍滞后，看中文教程容易学到已废弃的写法。**以英文官方文档为准，中文只作辅助理解概念。**

---

## 〇、先说清楚标准变了

| 阶段 | 对象 | 标准 |
|---|---|---|
| Python 基础（已完成） | 语言本身 | **会写**——不看资料能写出来 |
| 本阶段 ② | LangChain / LangGraph 的 API | **看懂 + 能改** |
| 本阶段 ③ | Agent 设计范式 | **必须理解**（这是思想，不是 API） |
| 本阶段 ④ | 工程化配套 | **认得 + 按需深入** |

**为什么框架层不要求"会写"？**

- 框架 API 更新快，背下来也会过时
- 你写 Agent 时的角色是**设计者 + 审阅者**，不是 API 默写员
- 真正的价值在「知道该用什么、判断用得对不对」

**但第 ③ 层是例外**——ReAct 循环、状态管理这些是**思想**，不是 API。思想不理解，你只是在拼装别人的代码。

---

## 一、路线总览

| 层 | 内容 | 时间 | 产出 |
|---|---|---|---|
| **②** | LangChain 基础 → LangGraph | 2–3 周 | 跑通最小 Agent 图 |
| **③** | Agent 范式（ReAct / 工具调用 / 状态） | 1–2 周 | 实现多轮工具调用 |
| **④** | 工程化（RAG / 审计 / API / 成本） | 边做边补 | 能演示的完整系统 |

**总计约 4–6 周**（每天 2 小时）。

---

# 第 ② 层 · LangChain / LangGraph

## 2.1 先跑通，再理解

**不要一上来读文档**。先跑通官方 quickstart，让代码跑起来，再回头理解每个组件。

顺序：
1. 装包，调通一次模型
2. 跑通 `create_agent`（10 行代码就能有一个 Agent）
3. 再跑通一个最小的 LangGraph 图
4. 最后回头拆解每个概念

### LangChain 1.0 的变化（重要）

2025 年底 LangChain 发布了 1.0，**入口从"各种 Chain"变成了 `create_agent`**：

```python
from langchain.agents import create_agent


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


agent = create_agent(
    model="openai:gpt-4o",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "天气如何？"}]
})
print(result["messages"][-1].content)
```

**注意**：`tools` 直接接收**普通函数**（靠 docstring 和类型注解生成 schema），不需要手动 `@tool`。

**官方给的选型建议**：

| 需求 | 用什么 |
|---|---|
| 开箱即用（自动压缩上下文、虚拟文件系统、子 Agent） | **Deep Agents** |
| 高度定制 | **LangChain `create_agent`** |
| 底层编排（确定性流程 + Agent 混合） | **LangGraph** |
| 追踪调试 | **LangSmith** |

**这对你的路线意味着什么**：

第 ② 层的顺序应该是 ——
1. 先跑通 `create_agent`（10 行就有一个 Agent，建立信心）
2. 再学 LangGraph（理解底层循环）
3. **不要一上来就啃 LangGraph 的 API**

**那为什么还要学 LangGraph？**

因为你要做的是**流程可控的追溯 Agent**——需要明确的节点、条件路由、状态持久化、人工确认。`create_agent` 是个黑盒循环，控制力不够。

> 简单说：**`create_agent` 让你快速看到效果，LangGraph 让你掌控流程。** 两个都要，但顺序不能反。

## 2.2 LangChain 必须搞清的 6 个概念

### ① Model（模型）

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0)
response = llm.invoke("你好")
print(response.content)
```

**三种调用方式**（模块 F 学过）：

| 方法 | 用途 |
|---|---|
| `invoke(...)` | 同步，一次性拿结果 |
| `stream(...)` | 同步流式 |
| `ainvoke(...)` / `astream(...)` | 异步版 |

> 换成通义/DeepSeek/本地模型，只需要换这一层——**这就是 Pi Agent 三层架构里 `pi-ai` 那一层的作用**。

### ② Message（消息）

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

messages = [
    SystemMessage(content="你是不良品根因分析助手"),
    HumanMessage(content="3号产线昨天有5个批次不良"),
]
```

**四种消息类型**：

| 类型 | 谁产生的 | 用途 |
|---|---|---|
| `SystemMessage` | 你 | 设定角色和行为规则 |
| `HumanMessage` | 用户 | 用户输入 |
| `AIMessage` | 模型 | 模型回复（**可能带 `tool_calls`**） |
| `ToolMessage` | 你 | 工具执行结果（回填给模型） |

> 你模块 A 里练的 `{"role": "user", "content": "..."}` 字典，就是这些消息对象的简化版。

### ③ Prompt（提示词模板）

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{domain}领域的分析助手"),
    ("human", "{question}"),
])

result = prompt.invoke({"domain": "制造业质量", "question": "为什么有不良？"})
```

**为什么用模板不用字符串拼接？**
- 变量自动校验（少传变量会报错）
- 可以复用
- 支持 `MessagesPlaceholder` 插入历史消息

### ④ OutputParser（结构化输出）

**最常用的方式**（模块 D 学过 Pydantic）：

```python
from pydantic import BaseModel, Field


class RootCause(BaseModel):
    """根因分析结果"""
    cause: str = Field(description="最可能的原因")
    evidence: list[str] = Field(description="支撑证据")
    confidence: float = Field(description="置信度 0-1")


structured_llm = llm.with_structured_output(RootCause)
result = structured_llm.invoke("3号产线温度偏低导致焊接不良")
print(result.cause)
```

**这就是模块 D 练习 10 的实战版**——`model_json_schema()` 生成的 Schema 被自动塞给模型。

### ⑤ Tool（工具）

模块 G 学过 `@tool`。这里补上**完整用法**：

```python
from langchain_core.tools import tool


@tool
def query_workorder(line: str, date: str) -> str:
    """查询指定产线在某天的工单记录

    Args:
        line: 产线编号，例如 3号线
        date: 日期，格式 YYYY-MM-DD
    """
    # 真实场景里查数据库
    return f"{line} 在 {date} 有 5 个批次"


# 绑定到模型
llm_with_tools = llm.bind_tools([query_workorder])
```

**关键**：`bind_tools` 之后，模型就能"决定要不要调这个工具"，但它**不负责执行**——执行是你的事。

### ⑥ Runnable / LCEL（管道）

```python
chain = prompt | llm | parser
result = chain.invoke({"question": "..."})
```

**`|` 是重载的运算符**，把组件串成管道。左边输出 → 右边输入。

**LCEL 的价值**：
- 统一接口（所有组件都有 `invoke` / `stream` / `batch`）
- 自动支持流式
- 自动支持异步

> 注意：LCEL 不是必须的。很多场景直接写函数更清晰。**看懂即可，不必强行用**。

## 2.3 LangGraph 必须搞清的 7 个概念

### 最小可运行例子（建议先跑通这个）

```python
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, add_messages
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END


llm = ChatOpenAI(model="gpt-4o")


# ① State：整个图的共享状态
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ② Node：一个函数，接收 state，返回要更新的字段
def chatbot(state: State) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


# ③ 建图
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)       # 加节点
builder.add_edge(START, "chatbot")          # 起点 → 节点
builder.add_edge("chatbot", END)            # 节点 → 终点

# ④ 编译
graph = builder.compile()

# ⑤ 运行
result = graph.invoke({"messages": [HumanMessage(content="你好")]})
print(result["messages"][-1].content)
```

**这段代码里的每一个符号你都学过**：

| 符号 | 出自 |
|---|---|
| `TypedDict` | 模块 D 练习 4 |
| `Annotated[list, add_messages]` | 模块 D 练习 5 |
| 函数作为参数 `add_node("x", func)` | 模块 A（函数是一等公民） |
| `builder.compile()` | 模块 C（类的方法调用） |

### 七个概念逐个说

| 概念 | 是什么 | 类比 |
|---|---|---|
| **State** | 图的共享状态（`TypedDict`） | 全局变量，但受控 |
| **Node** | 一个函数，改 state | 流程里的一个步骤 |
| **Edge** | 固定跳转 A→B | 直线箭头 |
| **Conditional Edge** | 根据 state 决定去哪 | if/else 分支 |
| **compile()** | 把图变成可执行对象 | 编译 |
| **Checkpointer** | 保存每一步的状态 | 存档 |
| **interrupt()** | 暂停等人确认 | 断点 |

### 条件路由（Agent 的核心）

```python
def should_continue(state: State) -> str:
    """判断下一步去哪"""
    last_message = state["messages"][-1]

    # 如果模型要调工具，就去 tools 节点
    if last_message.tool_calls:
        return "tools"
    # 否则结束
    return END


builder.add_conditional_edges(
    "chatbot",
    should_continue,
    {"tools": "tools", END: END},
)
```

**这就是 ReAct 循环的骨架**——判断"还要不要继续"。

### Checkpointer（状态持久化）

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "user-123"}}

# 第一次
graph.invoke({"messages": [HumanMessage(content="你好")]}, config)

# 第二次：能记住上一次的对话
graph.invoke({"messages": [HumanMessage(content="刚才说到哪了")]}, config)
```

**`thread_id` 就是会话 ID**。同一个 `thread_id` 共享历史。

> 这就是 Pi Agent 里 `AgentSession` + JSONL 会话存储的对应物。

## 2.4 学习资源与顺序

| 顺序 | 资源 | 做什么 |
|---|---|---|
| 1 | LangChain 官方 Quickstart | 跑通，调通一次模型 |
| 2 | LangGraph 官方 Quickstart | 跑通上面那个最小图 |
| 3 | LangGraph 的 "Build a basic chatbot" 教程 | 加工具、加条件路由 |
| 4 | LangGraph 的 "Human-in-the-loop" 教程 | 加 interrupt |
| 5 | LangGraph 的 "Persistence" 教程 | 加 checkpointer |

> **官方文档的版本要和装的包版本一致**。LangChain 迭代快，看旧博客容易踩坑。

---

# 第 ③ 层 · Agent 范式（必须理解）

这一层不是学 API，是**理解思想**。

## 3.1 ReAct 循环

**ReAct = Reasoning + Acting**。核心是让模型"边想边做"：

```
Thought: 用户问3号产线的不良原因，我需要先查工单
Action: query_workorder(line="3号线", date="2026-10-16")
Observation: 返回 5 个批次，其中 3 个异常
Thought: 需要再查这 3 个批次的质检记录
Action: query_quality(batch_ids=[...])
Observation: 温度参数偏低
Thought: 有了足够证据，可以给结论了
Final Answer: 根因是回流焊温度偏低...
```

**这就是 Pi Agent 里那个 `while` 循环的理论版**：

```
while 模型还在调工具:
    执行工具
    把结果塞回消息列表
    再调模型
```

**要理解的三件事**：

| 问题 | 答案 |
|---|---|
| 模型怎么决定"要不要调工具" | 它在训练时学过：需要外部信息就输出 `tool_calls` |
| 工具结果怎么回去 | 包成 `ToolMessage` 追加到 `messages` |
| 什么时候停 | 模型不再输出 `tool_calls`，直接给文本 |

## 3.2 工具调用（Tool Calling）的完整链路

```python
# ① 模型返回的 AIMessage 里带 tool_calls
response = llm_with_tools.invoke(messages)
# response.tool_calls = [{"name": "query_workorder", "args": {...}, "id": "call_abc"}]

# ② 你执行工具
from langchain_core.messages import ToolMessage

messages.append(response)                    # 先把模型的"意图"加进去

for tool_call in response.tool_calls:
    result = execute_tool(tool_call["name"], tool_call["args"])
    messages.append(
        ToolMessage(content=result, tool_call_id=tool_call["id"])
    )

# ③ 再调模型，这次它能看到工具结果了
response2 = llm_with_tools.invoke(messages)
```

**关键理解**：**模型从来没有真正"执行"任何东西**。它只是输出一段结构化的"我想调这个工具"，执行永远发生在你的代码里。

> 这就是 Pi Agent 说的"**副作用边界**"——模型只能提议，执行在本地，可拦截。

## 3.3 工具描述决定成败

**同一段逻辑，两种描述**：

```python
# ❌ 差
@tool
def q(line: str, date: str) -> str:
    """查询"""
    ...

# ✅ 好
@tool
def query_workorder(line: str, date: str) -> str:
    """查询指定产线在某天的工单记录。

    适用于：用户询问某个产线在某天的生产情况、批次数量、异常批次。

    Args:
        line: 产线编号，例如 "3号线"、"装配二线"
        date: 日期，格式 YYYY-MM-DD，例如 "2026-10-16"
    """
    ...
```

**模型选不选这个工具、参数填得对不对，几乎全看这段描述。**

这是 Agent 开发里**最容易被低估的调优点**——比调 temperature 有用得多。

## 3.4 状态管理：短期 vs 长期

| | 短期记忆 | 长期记忆 |
|---|---|---|
| 是什么 | 当前对话的 `messages` | 跨会话持久化的数据 |
| 存哪 | 内存 / State | Checkpointer + 数据库 |
| 会满吗 | **会**（上下文窗口） | 不会 |
| 怎么处理 | 裁剪 / 摘要 | 按需检索 |

**上下文超了怎么办**（三个策略）：

| 策略 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| 滑动窗口 | 只留最近 N 条 | 简单 | 丢早期信息 |
| 摘要压缩 | 把旧对话总结成一段 | 保留要点 | 有信息损失 |
| RAG 检索 | 存起来，用时检索 | 不丢信息 | 复杂 |

> Pi Agent 用的是"**摘要压缩 + 原始记录全留**"——喂给模型的是摘要，但完整历史在 JSONL 里可回溯。这是最实用的方案。

## 3.5 三种 Agent 架构

| 架构 | 结构 | 什么时候用 |
|---|---|---|
| **单 Agent + 工具** | 一个循环，多个工具 | **大多数场景**，优先选这个 |
| **多 Agent 协作** | 多个 Agent 分工 | 流程长、角色差异大 |
| **Plan-and-Execute** | 先出计划，再逐步执行 | 任务复杂、步骤多 |

**建议**：从单 Agent 开始。**90% 的场景不需要多 Agent**，多 Agent 会带来调试复杂度指数级上升。

## 3.6 什么时候"不该"用 Agent（重要）

**这是最容易被跳过的一节，但最重要。**

Agent 的代价：
- 不确定（同样的输入，输出可能不同）
- 慢（多轮调用）
- 贵（token 消耗大）
- 难调试

**所以：能用固定流程解决的，别用 Agent。**

| 场景 | 该用什么 |
|---|---|
| 步骤固定、判断规则明确 | **普通函数 / 工作流** |
| 需要理解自然语言、灵活决策 | Agent |
| 输入格式固定、输出格式固定 | 普通函数 + Pydantic |

**判断方法**：问自己"如果换成人工，这个人需要思考吗？"
- 需要思考、需要判断 → Agent
- 照着 SOP 执行就行 → 普通代码

> 你的"不良品根因追溯"属于前者——因为"哪个参数异常会导致这个缺陷"需要经验和推理。

---

# 第 ④ 层 · 工程化与上线

这一层**边做边补**，不用提前学完。

## 4.1 RAG（检索增强生成）

**为什么需要**：模型不知道你的私有数据（历史不良报告、工艺文件、专家经验）。

**完整流程**：

```
文档（PDF/Word/Excel）
    ↓ ① 加载
纯文本
    ↓ ② 切块（chunk）
文本块（每块几百字）
    ↓ ③ 向量化（Embedding）
向量
    ↓ ④ 存入向量库
    ↓ ⑤ 用户提问时，检索最相似的几块
    ↓ ⑥ 拼进 prompt
LLM 基于这些材料回答
```

**最小实现**（LangChain 提供现成组件）：

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


# ① 加载
docs = TextLoader("历史不良报告.txt", encoding="utf-8").load()

# ② 切块
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# ③④ 向量化 + 存储
vectorstore = FAISS.from_documents(chunks, OpenAIEmbeddings())

# ⑤ 检索
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
relevant = retriever.invoke("回流焊温度偏低会导致什么缺陷")

# ⑥ 塞进 prompt
context = "\n\n".join(d.page_content for d in relevant)
```

**三个必踩的坑**：

| 坑 | 表现 | 对策 |
|---|---|---|
| 切块太大/太小 | 检索不准 | 按语义切（段落/章节），不要按固定字数硬切 |
| 召回质量差 | 找到的资料不相关 | 调 `k` 值、加 rerank、改 embedding 模型 |
| 模型不看资料硬编 | 幻觉 | prompt 里明确要求"只能基于以下材料回答" |

## 4.2 可观测性

**问题**：Agent 跑一次可能调 10 次模型、5 次工具，出错了你不知道哪一步坏的。

**方案**：

| 方案 | 说明 |
|---|---|
| LangSmith | 官方平台，自动追踪每次调用（推荐入门） |
| 自己埋点 | 用 `logging` 记录每步输入输出 |
| `stream_mode="debug"` | LangGraph 内置，能看到每个节点的状态变化 |

**最小做法**（不接 LangSmith）：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def traced_node(state):
    logging.info(f"[节点] 输入: {state}")
    result = do_something(state)
    logging.info(f"[节点] 输出: {result}")
    return result
```

## 4.3 审计日志（制造业必需）

**记什么**：

| 字段 | 说明 |
|---|---|
| 时间戳 | 精确到毫秒 |
| 会话 ID / 用户 | 谁在用 |
| 输入 | 用户问了什么 |
| 调用的工具 | 工具名 + 参数 |
| 工具返回 | 原始结果 |
| 模型输出 | 最终结论 |
| 耗时 / token 数 | 成本核算 |

**为什么制造业必须有**：

真实案例——某药企在 GMP 合规检查时被要求提供过去 90 天所有 AI 审核操作的完整日志，**拿不出来，直接成了合规事故**。

**你的场景**：如果 Agent 建议"这批货可以放行"，出了质量问题，你得能说清"当时基于什么数据得出的结论"。

**实现**：JSONL 追加写入，和 Pi Agent 的做法一样。

```python
import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def audit_log(event: dict) -> None:
    event["timestamp"] = datetime.now().isoformat()
    log_file = LOG_DIR / f"{datetime.now():%Y-%m-%d}.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
```

## 4.4 成本控制

| 手段 | 效果 |
|---|---|
| 缓存相同请求 | 省重复调用 |
| 模型分级（简单任务用小模型） | 省 50%+ |
| 限制 `max_tokens` | 防跑飞 |
| 裁剪上下文 | 省 token |
| 批量处理 | 省调用次数 |

**最小实现**：

```python
from functools import lru_cache
import hashlib


@lru_cache(maxsize=1000)
def cached_query(question_hash: str) -> str:
    ...
```

## 4.5 部署

模块 H 学过 FastAPI。这里补上**关键点**：

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


@app.post("/chat")
async def chat(req: ChatRequest) -> dict:
    config = {"configurable": {"thread_id": req.thread_id}}

    # 关键：必须用 ainvoke，不能用 invoke
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=req.message)]},
        config,
    )
    return {"reply": result["messages"][-1].content}
```

**`ainvoke` 而不是 `invoke`** —— 否则阻塞事件循环，所有请求排队（模块 F 的坑 2）。

## 4.6 安全

| 风险 | 对策 |
|---|---|
| 危险工具被误调 | 加 `interrupt()` 人工确认 |
| Prompt 注入 | 用户输入和系统提示隔离，不让用户输入覆盖指令 |
| 敏感数据泄露 | 日志脱敏、只传必要字段 |
| 无限循环 | 设置最大轮数 `recursion_limit` |

**危险工具确认**（human-in-the-loop）：

```python
from langgraph.types import interrupt

def dangerous_action(state):
    decision = interrupt({
        "question": "即将执行删除操作，是否确认？",
        "action": state["pending_action"],
    })
    if decision != "yes":
        return {"messages": [AIMessage(content="操作已取消")]}
    ...
```

---

# 五、贯穿项目：不良品根因追溯智能体

**三层不是分开学的，是同一个项目逐步加功能。**

## 阶段 1 · 对应第 ② 层（2–3 周）

**目标**：能跑通的单轮 Agent

```
输入：批次号 / 产线 / 时间范围
  ↓
工具：query_workorder（查工单）
      query_quality（查质检记录）
      query_bom（查 BOM 和物料）
  ↓
输出：可能的原因 + 支撑数据
```

**技术点**：
- `@tool` 定义三个工具
- `bind_tools` 绑定
- LangGraph 单节点图 + 条件路由（要不要继续调工具）

**验收**：能对一个真实批次给出有数据支撑的初步结论。

## 阶段 2 · 对应第 ③ 层（1–2 周）

**目标**：多轮追溯 + 证据链

**加什么**：

| 加什么 | 为什么 |
|---|---|
| 多轮工具调用 | 一次查不够，要顺着线索追 |
| 状态管理（checkpointer） | 支持多轮追问 |
| 证据链 | **每条结论标注来源**（哪条工单、哪条质检记录） |
| 最大轮数限制 | 防死循环 |

**验收**：能对一个复杂批次做 3–5 轮追溯，每步有记录。

## 阶段 3 · 对应第 ④ 层（持续）

**目标**：能演示、能说清、能兜底

| 加什么 | 为什么 |
|---|---|
| RAG（历史案例库） | 能参考"上次类似问题怎么解决的" |
| 审计日志 | 合规 + 排错 |
| FastAPI 接口 | 给前端/其他系统调 |
| 人工确认 | 涉及"放行/报废"这类决策时必须有人把关 |
| 成本监控 | 知道每次追溯花多少钱 |

**验收**：能完整演示一遍，包括"AI 建议 → 人确认 → 留痕"的闭环。

---

# 六、时间安排

| 周次 | 内容 | 每天 2 小时的分配 |
|---|---|---|
| 第 1 周 | LangChain 基础（Model / Message / Prompt / Tool / LCEL） | 跑通 quickstart，理解 6 个概念 |
| 第 2 周 | LangGraph 基础（State / Node / Edge / 条件路由） | 跑通最小图 + 加工具 |
| 第 3 周 | LangGraph 进阶（checkpointer / interrupt）+ 开始阶段 1 项目 | 边学边写 |
| 第 4 周 | Agent 范式（ReAct / 工具调用链路 / 状态管理） | 理解 + 重构阶段 1 |
| 第 5 周 | RAG + 审计日志 | 给项目加记忆和留痕 |
| 第 6 周 | 部署 + 安全 + 打磨演示 | 完整跑通 |

**灵活调整**：第 ④ 层的内容可以边做边补，不用等前五周学完。

---

# 七、不用深挖的

| 别碰 | 原因 |
|---|---|
| LangChain 的各种 Chain 类型（LLMChain / SequentialChain…） | 大部分已被 LCEL 取代，旧教程的坑 |
| LangServe / LangGraph Cloud | 除非真要部署到云 |
| 各种 Vector DB 的底层原理 | 会用 FAISS / Chroma 就够 |
| 自己实现 Agent 循环 | 用框架，别重复造轮子 |
| 微调模型 | 90% 的场景用 prompt + RAG 就够 |
| 多 Agent 框架（CrewAI / AutoGen） | 先把单 Agent 做透 |

---

# 八、每阶段自检

## 第 ② 层过关

- [ ] 能跑通 LangGraph 的最小图，并解释每个部分
- [ ] 能说清 `Annotated[list, add_messages]` 在干什么
- [ ] 能写一个带条件路由的图
- [ ] 能解释 `invoke` / `stream` / `ainvoke` 的区别
- [ ] 知道 `@tool` 的 docstring 为什么重要

## 第 ③ 层过关

- [ ] **能画出 ReAct 循环的完整流程**
- [ ] 能说清"模型怎么决定调工具、工具结果怎么回去、什么时候停"
- [ ] 能说出**三种以上"不该用 Agent"的场景**
- [ ] 知道上下文超限的三种处理策略
- [ ] 能解释为什么"危险操作要人工确认"

## 第 ④ 层过关

- [ ] 能画出 RAG 的完整流程（六步）
- [ ] 知道审计日志要记哪 7 个字段
- [ ] 能把 Agent 包成 FastAPI 接口，且用 `ainvoke`
- [ ] 知道怎么防止 Agent 死循环

---

## 最后一句

**这一阶段最大的坑不是技术，是"过度设计"。**

很多人一上来就想做多 Agent、做全自动、做通用平台——结果卡在第一个 demo 上。

**正确的顺序**：单 Agent → 三个工具 → 跑通一个真实批次 → 再加记忆、加 RAG、加接口。

**先把一条链路跑通，再谈扩展。**
