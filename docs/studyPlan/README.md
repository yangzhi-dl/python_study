# Python 基础清单 —— 面向 Agent 开发

> **两段式标准（关键）**
>
> | 层次 | 对象 | 标准 |
> |---|---|---|
> | 第一段 | **Python 语言本身** | **必须自己会写** |
> | 第二段 | **框架与库**（LangChain / LangGraph / FastAPI） | **看懂即可** |
>
> **本文档只管第一段。** 框架层是下一阶段的事，那时你写代码的角色从"作者"变成"审阅者"。

---

## 〇、为什么这样分

### Python 基础必须会写

- **框架层看不懂，可以查文档、可以让 AI 补。但 Python 基础看不懂，你连"AI 写错了"都发现不了。**
- 基础不牢时，LangChain 报的错你会误以为是框架问题，其实是语法问题——这是最浪费时间的坑。
- 写工具函数、定义数据结构、处理异常，这些是**每天都要动手的**，没有"看懂就行"的空间。

### 框架层看懂即可

- 框架 API 更新快，背下来也会过时，不值得投入。
- 用 AI 写框架代码时，你的价值在于**判断对错、发现问题**，不是默写 API。
- 真正要掌握的是：**数据怎么流动、状态怎么变、错误出在哪一层**。

---

## 一、路线总览

| 模块 | 内容 | 标准 | 净学习时长 |
|---|---|---|---|
| **A** | 语言基础 | 会写 | 6 h |
| **B** | 工程与运行环境 | 会写（要动手） | 2 h |
| **C** | 面向对象 | 会写 | 3 h |
| **D** | 类型系统与 Pydantic | 会写 | 4 h |
| **E** | 错误处理与调试 | 会写 | 2.5 h |
| **F** | 异步与流式 | 会写 | 3 h |
| **G** | 装饰器 | 会写 | 1.5 h |
| **H** | 工程化配套 | 能改 / 认得 | 2 h |
| | **合计** | | **约 24 小时** |

**档位说明**

| 档位 | 含义 |
|---|---|
| **【会写】** | 能自己写出来，不用查资料 |
| **【能改】** | 能看懂、能改参数、能照着抄 |
| **【认得】** | 认得出就行，遇到再查 |

---

## 模块 A · 语言基础（6 h）【全部会写】

地基。这一层没有"看懂即可"的余地。

| 知识点 | 档位 | 在 Agent 里用在哪 |
|---|---|---|
| str / int / float / bool / None | 会写 | |
| f-string 格式化 | 会写 | 拼 prompt 天天用 |
| list：增删改查、排序 | 会写 | 消息列表、工具列表 |
| dict：取值、`.get()`、遍历 | 会写 | 状态、工具参数、API 返回 |
| **嵌套结构 `list[dict]`、`dict[str, list]`** | 会写 | ★★ Agent 数据的标准形状 |
| 切片 `[1:]` `[:-1]` `[-3:]` | 会写 | 取最近 N 条历史消息 |
| 条件 if / elif / else、三元表达式 | 会写 | |
| 循环 for / while | 会写 | |
| `enumerate` / `zip` / `range` | 会写 | 高频 |
| **解包 `a, b = x`、`*args`、`**kwargs`、`**d`** | 会写 | ★★ LangChain 调用几乎全是 kwargs |
| **列表 / 字典推导式** | 会写 | 过滤消息、批量转换 |
| `any` / `all` / `sum` / `sorted(key=...)` | 会写 | |
| 字符串方法 split / join / strip / replace | 会写 | 解析模型输出 |
| 函数：定义、参数、默认值、返回值 | 会写 | |
| **关键字实参调用** `f(a=1, b=2)` | 会写 | ★★ LLM 调用全是这种写法 |
| **函数是一等公民**（可传参、可返回） | 会写 | ★★ `add_node("x", my_func)` 的本质 |
| `lambda` | 能改 | 排序、简单回调 |
| 作用域、闭包 | 能改 | |
| 可变对象陷阱（dict/list 传引用） | 认得 | 状态复用的坑 |

**过关检验**：不看资料，写一个函数接收 `list[dict]` 形式的消息，按 role 分组拼成字符串。

---

## 模块 B · 工程与运行环境（2 h）【会写】

> 这个模块**必须动手**，不建虚拟环境就装不了 langchain。

| 知识点 | 档位 | 在 Agent 里用在哪 |
|---|---|---|
| 虚拟环境 venv / uv | 会写 | 每个项目独立环境 |
| pip / uv 安装依赖 | 会写 | `pip install langchain langgraph` |
| requirements.txt / pyproject.toml | 会写 | 记录依赖，换机器能复现 |
| 模块与包：`import` / `from x import y` | 会写 | 拆文件后必然要用 |
| `if __name__ == "__main__":` | 会写 | 脚本入口 |
| 路径处理 `pathlib.Path` | 会写 | 加载 prompt 模板、知识库文件 |
| **环境变量** + `.env` + `python-dotenv` | 会写 | 存 API Key |
| 终端基本操作（cd、跑脚本） | 会写 | 日常 |

**过关检验**：从零建项目 → 建虚拟环境 → 装 langchain → 写两个 .py 互相 import → 从 .env 读 Key 并打印 → 跑通。

---

## 模块 C · 面向对象（3 h）【会写】

Agent 框架全是类。要能自己定义类、继承基类。

| 知识点 | 档位 | 在 Agent 里用在哪 |
|---|---|---|
| `class` / `__init__` / `self` | 会写 | ★ 框架里到处都是 |
| 属性、方法、实例化 | 会写 | `graph = StateGraph(State)` |
| 继承、`super()` | 会写 | 自定义 Tool / Callback 时继承基类 |
| `@dataclass` | 会写 | 定义轻量配置对象 |
| `@property` | 能改 | |
| `@staticmethod` / `@classmethod` | 能改 | |
| 魔术方法 `__repr__` / `__call__` | 认得 | 调试、可调用对象 |
| 多重继承、MRO | 认得 | |

**过关检验**：不看资料，定义一个类、继承它、在子类里调 `super().__init__()`。

---

## 模块 D · 类型系统与 Pydantic（4 h）【会写】

**分水岭。** 这一层不会，LangGraph 代码就是天书。

### D1 类型注解（Python 语法，必须会写）

| 知识点 | 档位 | 说明 |
|---|---|---|
| `def f(x: int) -> str:` | 会写 | 节点函数签名 |
| `list[str]` / `dict[str, int]` / `tuple[int, ...]` | 会写 | |
| `Optional[X]` 或 `X \| None` | 会写 | |
| `Union[X, Y]` 或 `X \| Y` | 会写 | |
| `Literal["a", "b"]` | 会写 | 路由函数的返回值约束 |
| `Any` | 会写 | |
| **`TypedDict`** | 会写 | ★★ LangGraph 的 State 就是它 |
| **`Annotated[X, meta]`** | 会写 | ★★ reducer：`Annotated[list, add_messages]` |
| `Callable[[int], str]` | 能改 | 工具 / 回调类型 |
| `TypeVar` / `Generic` | 认得 | |

### D2 Pydantic（第三方库，但写工具必须会）

> 虽然属于"库"，但**写工具时必须自己定义参数模型**，所以基础用法要会写。

| 知识点 | 档位 | 说明 |
|---|---|---|
| `BaseModel` 定义、字段类型标注 | 会写 | ★★ 工具的 args_schema |
| `Field(...)` 默认值与描述 | 会写 | 给 LLM 看的参数说明 |
| `model_dump()` / `model_validate()` / `model_json_schema()` | 会写 | ★ 结构化输出、JSON Schema |
| 嵌套模型、`list[Model]` | 会写 | |
| 配合 `with_structured_output()` | 能改 | 让 LLM 输出固定结构 |
| 校验器 `field_validator` | 认得 | |

**过关检验**：自己定义一个带嵌套的 Pydantic 模型，调 `model_json_schema()` 看到 JSON Schema 输出。

---

## 模块 E · 错误处理与调试（2.5 h）【会写】

| 知识点 | 档位 | 在 Agent 里用在哪 |
|---|---|---|
| `try / except / else / finally` | 会写 | 工具报错、网络重试 |
| `raise` 抛出异常 | 会写 | |
| 常见异常类型（ValueError / KeyError / TypeError） | 会写 | |
| **看懂 traceback（从下往上读）** | 会写 | ★ 排错第一步 |
| `logging` 基础 | 能改 | 追踪 Agent 每一步 |
| `with` 上下文管理器 | 能改 | 文件读写 |
| 自定义异常类 | 能改 | |

**过关检验**：故意写一段会报错的代码，能自己从 traceback 定位到出错的行和原因。

---

## 模块 F · 异步与流式（3 h）【会写】

> 只做非流式的同步调用 → 可以后置；
> 要做**流式输出**（打字机效果）→ 必须会写。

| 知识点 | 档位 | 说明 |
|---|---|---|
| 同步 vs 异步的概念差异 | 会写 | 理解为什么有 `invoke` 和 `ainvoke` |
| `async def` / `await` | 会写 | |
| `asyncio.run()` | 会写 | 异步入口 |
| **生成器 `yield`** | 会写 | ★ 流式输出的底层 |
| **异步生成器 `async for`** | 会写 | ★ `astream()` 返回的就是它 |
| `asyncio.gather()` 并发 | 能改 | 并行调多个工具 |
| 迭代器协议 `__iter__` / `__next__` | 认得 | |
| `contextvars` | 认得 | LangGraph 内部传上下文用 |
| 事件循环原理、GIL | 认得 | 知道就行，别深挖 |

**过关检验**：不看资料，写一个异步函数，用 `async for` 逐块打印内容。

---

## 模块 G · 装饰器（1.5 h）【会写】

| 知识点 | 档位 | 说明 |
|---|---|---|
| 理解 `@deco` 等价于 `f = deco(f)` | 会写 | 看懂 `@tool`、`@traceable` |
| 自己写一个简单装饰器 | 会写 | |
| 带参数的装饰器 | 能改 | |
| `functools.wraps` | 认得 | |

**过关检验**：不看资料，写一个能打印函数执行时间的装饰器。

---

## 模块 H · 工程化配套（2 h）【按需】

| 知识点 | 档位 | 什么时候需要 |
|---|---|---|
| 配置分层（.env / 配置类） | 能改 | 有 dev / prod 之分时 |
| `pytest` 基础 | 能改 | 要测工具函数时 |
| **FastAPI** 基础 | 认得 | 要把 Agent 暴露成 HTTP API 时 |
| 代码格式化 ruff / black | 认得 | |
| 类型检查 pyright / mypy | 认得 | |

> 如果最终只是本地跑脚本，这个模块可以整体跳过。

---

## 二、明确不用深挖的

- 元类、描述符协议、MRO 解析顺序
- 多进程 `multiprocessing`、GIL 原理
- C 扩展、Cython
- 复杂正则表达式
- socket / 网络编程底层
- 设计模式大全、领域驱动设计
- 装饰器嵌套地狱、闭包奇技淫巧
- 内存管理与手动 GC

理由：以上都不会在 Agent 编排代码里出现。遇到再说。

---

## 三、知识点 → 真实 Agent 代码对照

下面这段代码覆盖了模块 A–G 的核心。**每行右边的注释就是它的知识点来源。**

```python
from typing import Annotated, TypedDict              # D1 类型注解 + TypedDict + Annotated
from langchain_core.messages import BaseMessage, add_messages
from langgraph.graph import StateGraph, START, END


class AgentState(TypedDict):                          # C 类 / D1 TypedDict
    messages: Annotated[list[BaseMessage], add_messages]   # 泛型 + Annotated reducer


def call_model(state: AgentState) -> dict:            # A 函数定义 + D1 类型注解
    response = llm.invoke(state["messages"])          # A dict 取值 + 关键字实参
    return {"messages": [response]}                   # A dict 字面量


async def stream_answer(state: AgentState):           # F async def
    async for chunk in llm.astream(state["messages"]):     # F 异步生成器
        yield chunk.content                           # F yield


builder = StateGraph(AgentState)                      # C 类实例化
builder.add_node("agent", call_model)                 # A ★ 函数作为参数传递
builder.add_edge(START, "agent")                      # B 模块级常量
graph = builder.compile()                             # C 方法调用

result = graph.invoke({"messages": [("user", "你好")]})   # A 嵌套结构
print(result["messages"][-1].content)                 # A 索引 + 属性访问
```

**能自己写出这段的等价版本 = 模块 A–D 通关。**

---

## 四、时间安排

净学习时间约 **24 小时**（含动手写代码的时间）。

| 每天投入 | 完成天数 |
|---|---|
| 1 小时 | 约 3.5 周 |
| **2 小时** | **约 12 天（推荐）** |
| 3 小时 | 约 8 天 |
| 4 小时 | 约 6 天 |

**推荐节奏**：每天 2 小时 × 约 12 天。

**不建议**：攒到周末一次学 8 小时。语法需要**间隔重复 + 反复动手**才能进肌肉记忆。

### 最短路径（约 13 小时）

只学：**模块 A（6h）+ B（2h）+ C（3h）+ D1 类型注解（2h）**

学完就能自己写出 LangGraph 的骨架代码。**模块 F/G/H 在真正用到时补，比提前学效率高得多。**

---

## 五、怎么练（针对"必须会写"）

**核心原则：每个知识点手写一遍最小示例，不查资料能写出来才算过。**

1. **先照着抄，再关掉示例重写**。抄一遍不算学会，关掉能写出来才算。
2. **改需求**。写完一个函数后，主动改改需求（比如"再加一个过滤条件"），看自己能不能调整。
3. **故意写错，看报错**。积累报错经验比记住语法更有用。
4. **每学完一个模块，让 AI 出 3 道小题**。做不出来就是没学会，别自欺欺人。
5. **遇到卡住的语法，回查本文档**。清单从"要背的知识点"变成"手边的字典"。

### 进度判断标准

**不要用"我学完几个模块"衡量，用"不看资料能写出多少"衡量。**

- 能不看示例写出带 `**kwargs` 的函数 → 模块 A 过了
- 能不看示例定义类并继承 → 模块 C 过了
- 能不看示例写 `TypedDict` + Pydantic 模型 → 模块 D 过了
- 能不看示例写异步生成器 → 模块 F 过了

---

## 六、通关自检清单

**模块 A**

- [ ] 不看资料，能操作嵌套 dict / list
- [ ] 不看资料，能写出带 `**kwargs` 的函数
- [ ] 不看资料，能把函数当参数传给另一个函数
- [ ] 不看资料，能写推导式处理列表
- [ ] 不看资料，能用切片取最近 N 条

**模块 B**
- [ ] 能独立建项目、建虚拟环境、装依赖
- [ ] 能拆多个 .py 文件并互相 import
- [ ] 能从 .env 读配置

**模块 C**
- [ ] 不看资料，能定义类、继承、调 `super()`
- [ ] 能看懂框架源码里的类结构

**模块 D**
- [ ] 不看资料，能写 `TypedDict` 和 `Annotated`
- [ ] 不看资料，能定义 Pydantic 模型并调 `model_dump()` / `model_json_schema()`
- [ ] 能看懂 `list[dict[str, Any]]` 这类嵌套类型标注

**模块 E**
- [ ] 能看懂 traceback 并定位出错行
- [ ] 能写 try/except 处理错误

**模块 F**
- [ ] 不看资料，能写 `async def` + `await`
- [ ] 不看资料，能用 `yield` 写生成器
- [ ] 不看资料，能用 `async for` 消费异步流

**模块 G**
- [ ] 不看资料，能写一个简单装饰器

**以上全部打勾，再进入 LangChain / LangGraph 的正式学习（那一阶段标准放宽为「看懂即可」）。**
