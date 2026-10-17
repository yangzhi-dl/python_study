# 模块 D 练习 —— 类型注解与 Pydantic

> **配套文档**：`README.md` 模块 D（类型系统与 Pydantic）
> **用法**：每题先自己写 → 卡住了翻菜鸟教程查语法 → 最后对照文末参考答案
> **目标**：不看答案能写出来

---

## 为什么这模块是分水岭

之前说过：**这一层不会，LangGraph 代码就是天书**。原因很直接——LangGraph 的 `State` 就是用 `TypedDict` + `Annotated` 定义的：

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
```

这两行看不懂，整个 LangGraph 就没法读。而 Pydantic 则是**写工具时的必备技能**——每个工具的参数字段都要用它定义。

**好消息**：类型注解本身很简单，就是"给变量和函数贴标签"。真正要花时间的是 Pydantic 的用法。

---

## 准备：先装 pydantic

D2 部分需要 pydantic。在 PyCharm 里装：

```
Settings → Project: Python学习 → Python Interpreter
→ 点 "+" → 搜索 pydantic → Install Package
```

确认右上角解释器路径是 `.venv\Scripts\python.exe`。

或者用终端：

```bash
cd practice/module_b_environment/mini_project
source .venv/Scripts/activate
pip install pydantic
```

---

## 贯穿所有练习的数据结构

和模块 A、C 一样，还是这个：

```python
messages = [
    {"role": "system", "content": "你是不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良"},
    {"role": "assistant", "content": "我先查一下工单记录"},
]
```

**这次我们要给它加上"类型标签"。**

---

# Part 1 · 类型注解（D1）

## 练习 1 · 基础类型注解

给下面这个函数加上完整的类型注解：

```python
def build_context(messages, max_count=3):
    recent = messages[-max_count:]
    lines = []
    for m in recent:
        lines.append(f'{m["role"]}: {m["content"]}')
    return "\n".join(lines)
```

要求标注出：
- `messages` 是「字典组成的列表」
- `max_count` 是整数
- 返回值是字符串

> 考察：`list[dict]`、`int`、`-> str`

<details>
<summary>Java 对照</summary>

```java
public static String buildContext(List<Map<String, String>> messages, int maxCount) {
    ...
}
```

**几乎一样**。Python 的 `list[dict]` 对应 Java 的 `List<Map<...>>`，只是写法更简洁。

区别：**Java 的类型是强制的**（不写编译不过），**Python 的类型是可选的**（不写照样跑，写了也没人检查）。
</details>

---

## 练习 2 · Optional / None

写一个函数 `find_message(messages, role)`：在消息列表里找第一条指定 role 的消息，**找到就返回它，找不到返回 None**。

```python
msg = find_message(messages, "user")
if msg is not None:
    print(msg["content"])
```

请**用两种写法**各写一遍：
- `Optional[dict]`
- `dict | None`

> 考察：`Optional[X]` 和 `X | None`
> **两种写法完全等价**，`|` 是 Python 3.10+ 的新语法，更简洁

---

## 练习 3 · Literal（限定取值范围）

定义一个类型 `Role`，只能是 `"system"`、`"user"`、`"assistant"` 三个值之一。

然后用它写一个函数 `filter_by_role(messages, role)`，只返回指定 role 的消息。

```python
user_msgs = filter_by_role(messages, "user")    # ✅
bad = filter_by_role(messages, "boss")          # ⚠️ 类型检查器会警告
```

> 考察：`Literal` —— 把取值限定在几个常量里
> **为什么需要**：比 `str` 精确得多，能防止传错值

<details>
<summary>Java 对照</summary>

```java
public enum Role { SYSTEM, USER, ASSISTANT }
```

`Literal` 有点像"轻量版的枚举"——不用定义 enum，直接列字符串。
</details>

---

## 练习 4 · TypedDict（重点 ★）

**用 `TypedDict` 描述消息字典的结构**，然后改掉练习 1 里那个 `list[dict]` 的模糊标注。

```python
class MessageDict(TypedDict):
    role: str
    content: str
```

改完后，`build_context(messages: list[MessageDict], ...)`。

**关键体验**：在 PyCharm 里敲 `messages[0]["` 的时候，会不会自动提示 `role` 和 `content`？

> 考察：`TypedDict`
> **为什么重要**：`dict` 是"什么键都行"，`TypedDict` 是"只有这几个键"——PyCharm 能据此做补全和检查

---

## 练习 5 · Annotated（重点 ★★）

这题不是"写"，是"读懂 + 复现"。

先看这段代码（LangGraph 里的真实写法）：

```python
from typing import Annotated, TypedDict


def add_messages(left: list, right: list) -> list:
    """把新消息追加到旧消息后面"""
    return left + right


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
```

**要求你回答三个问题**：

1. `Annotated[list, add_messages]` 里，`list` 和 `add_messages` 各是什么角色？
2. 如果写成 `messages: list`（去掉 Annotated），LangGraph 处理时会有什么不同？
3. 自己写一个 `Annotated[int, "必须大于0"]` 的变量，并打印它的类型注解，看看输出什么。

> 考察：`Annotated[X, meta]` —— "类型 X + 附加元信息 meta"
> **为什么重要**：LangGraph 靠读取这个元信息来决定"这个字段怎么合并"

<details>
<summary>提示：怎么打印类型注解</summary>

```python
from typing import Annotated, get_type_hints

count: Annotated[int, "必须大于0"] = 5
print(get_type_hints(__name__))
```
</details>

---

# Part 2 · Pydantic（D2）

## 练习 6 · 第一个 BaseModel

用 Pydantic 定义 `Message` 模型，然后创建实例。

```python
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


msg = Message(role="user", content="你好")
print(msg.role)      # user
print(msg)           # role='user' content='你好'
```

**额外试一下**：故意传错类型，看 Pydantic 报什么错。

```python
bad = Message(role=123, content="你好")
```

> 考察：`BaseModel` 定义
> **和 dataclass 的关键区别**：Pydantic 会**在运行时校验类型**，dataclass 不会

---

## 练习 7 · Field（给字段加说明和默认值）

给 `Tool` 模型加字段描述和默认值。

```python
from pydantic import BaseModel, Field


class Tool(BaseModel):
    name: str = Field(description="工具名称")
    description: str = Field(description="工具用途说明，给 LLM 看的")
    dangerous: bool = Field(default=False, description="是否为危险操作")
```

要求：

```python
tool = Tool(name="query_workorder", description="查询产线工单记录")
print(tool.dangerous)     # False（用了默认值）
```

> 考察：`Field(...)`
> **为什么重要**：`description` 不是给人看的，是**给 LLM 看的**——它会被写进 JSON Schema，帮助模型理解参数含义

---

## 练习 8 · 嵌套模型

定义两个模型：`ToolParameter` 和 `Tool`，`Tool` 里包含一个参数列表。

```python
class ToolParameter(BaseModel):
    name: str = Field(description="参数名")
    type: str = Field(default="string", description="参数类型")
    description: str = Field(default="", description="参数说明")


class Tool(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter] = []
```

要求能这样用：

```python
tool = Tool(
    name="query_workorder",
    description="查询产线工单记录",
    parameters=[
        ToolParameter(name="line", description="产线编号"),
        ToolParameter(name="date", description="日期"),
    ],
)

print(tool.parameters[0].name)       # line
print(len(tool.parameters))          # 2
```

> 考察：嵌套模型、`list[Model]`
> **小知识**：Pydantic 里 `= []` 是**安全的**（它会为每个实例深拷贝），但 `@dataclass` 里必须用 `field(default_factory=list)`——这个区别模块 C 提过

---

## 练习 9 · 三个核心方法

用练习 8 的 `tool` 对象，完成三件事：

1. **转成字典**：`tool.model_dump()`
2. **从字典还原**：`Tool.model_validate(data)`，并验证还原出来的和原来相等
3. **生成 JSON Schema**：`tool.model_json_schema()`，用 `json.dumps(..., indent=2, ensure_ascii=False)` 打印出来看

```python
import json

data = tool.model_dump()
tool2 = Tool.model_validate(data)
print(tool2 == tool)          # True

schema = tool.model_json_schema()
print(json.dumps(schema, indent=2, ensure_ascii=False))
```

> 考察：`model_dump()` / `model_validate()` / `model_json_schema()`
> **第三个方法最重要** —— 它生成的就是要发给 LLM 的 JSON Schema

---

## 练习 10 · 综合（最接近真实代码）

为一个真实工具定义参数模型，并生成给 LLM 看的 Schema。

工具：**查询产线工单**

参数：
- `line`：产线编号，必填
- `date`：日期，格式 `YYYY-MM-DD`，必填
- `limit`：最多返回多少条，默认 10

```python
from pydantic import BaseModel, Field
import json


class QueryWorkOrderArgs(BaseModel):
    """查询产线工单记录"""
    line: str = Field(description="产线编号，例如 3号线")
    date: str = Field(description="日期，格式 YYYY-MM-DD")
    limit: int = Field(default=10, description="最多返回多少条记录")


print(json.dumps(QueryWorkOrderArgs.model_json_schema(), indent=2, ensure_ascii=False))
```

**观察输出**：你会看到 `required` 数组里有 `line` 和 `date`，但没有 `limit`——因为 `limit` 有默认值。

> 考察：模块 D 全部知识点的串联
> **这题做通，你就理解了 LangChain 里工具参数是怎么定义并交给 LLM 的**

---

## 过关标准

| 部分 | 题目 | 标准 |
|---|---|---|
| D1 | 练习 1、2、3、4 | 不看答案能写出来 |
| D1 | 练习 5（Annotated） | **能用自己的话解释** `Annotated` 是什么 |
| D2 | 练习 6、7、8、9 | 不看答案能写出来 |
| D2 | 练习 10 | 能独立完成并看懂输出的 Schema |

**练习 5 是重点中的重点**——它是 LangGraph 的入口。

---

## 参考答案

> **先自己写完再看。**

<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

### 练习 1

```python
def build_context(messages: list[dict], max_count: int = 3) -> str:
    recent = messages[-max_count:]
    lines = []
    for m in recent:
        lines.append(f'{m["role"]}: {m["content"]}')
    return "\n".join(lines)
```

> 语法：`参数名: 类型`，返回值用 `-> 类型`。
> 注意 `list[dict]` 里的 `dict` 没带参数——因为字典的键值类型还没标注，练习 4 会改进。

### 练习 2

**写法 A（传统）：**

```python
from typing import Optional


def find_message(messages: list[dict], role: str) -> Optional[dict]:
    for m in messages:
        if m["role"] == role:
            return m
    return None
```

**写法 B（Python 3.10+，更简洁）：**

```python
def find_message(messages: list[dict], role: str) -> dict | None:
    for m in messages:
        if m["role"] == role:
            return m
    return None
```

> **两种完全等价**。现在推荐用 `|`，因为它更短，而且能组合：`int | str | None`。

### 练习 3

```python
from typing import Literal

Role = Literal["system", "user", "assistant"]


def filter_by_role(messages: list[dict], role: Role) -> list[dict]:
    return [m for m in messages if m["role"] == role]
```

> `Literal` 限定取值范围。类型检查器看到 `filter_by_role(messages, "boss")` 会提示错误。
> 注意：**运行时不会报错**，它只对静态检查工具有效。

### 练习 4

```python
from typing import TypedDict


class MessageDict(TypedDict):
    role: str
    content: str


def build_context(messages: list[MessageDict], max_count: int = 3) -> str:
    recent = messages[-max_count:]
    lines = []
    for m in recent:
        lines.append(f'{m["role"]}: {m["content"]}')
    return "\n".join(lines)
```

> 改完之后，在 PyCharm 里敲 `messages[0]["` 应该会弹出 `role` / `content` 的补全提示。
> **这是 TypedDict 最大的实用价值**——让 IDE 知道 dict 里有什么键。

### 练习 5

**问题 1**：`Annotated[list, add_messages]` 里
- `list` 是**真正的类型**（类型检查器看到的）
- `add_messages` 是**附加元信息**（类型检查器忽略，但 LangGraph 会读取）

**问题 2**：如果只写 `messages: list`，LangGraph 就不知道该怎么合并这个字段，默认行为是**直接覆盖**——新消息会顶掉旧消息，历史全丢。

**问题 3**：

```python
from typing import Annotated, get_type_hints

count: Annotated[int, "必须大于0"] = 5
print(get_type_hints(__name__))
# {'count': <class 'int'>}
```

> **核心理解**：`Annotated` = "类型 + 标签"。类型给检查器用，标签给框架用。
>
> **在 LangGraph 里**：`add_messages` 这个标签告诉它"这个字段要用 add_messages 函数来合并"。没有它，多轮对话的历史会被覆盖掉。

### 练习 6

```python
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


msg = Message(role="user", content="你好")
print(msg.role)
print(msg)
```

传错类型时：

```python
bad = Message(role=123, content="你好")
```

Pydantic 会尝试转换（`123` → `"123"`），如果转不了才报 `ValidationError`。

> **这就是 Pydantic 和 dataclass 的根本区别**：Pydantic **在运行时校验并转换类型**，dataclass 完全不管。

### 练习 7

```python
from pydantic import BaseModel, Field


class Tool(BaseModel):
    name: str = Field(description="工具名称")
    description: str = Field(description="工具用途说明，给 LLM 看的")
    dangerous: bool = Field(default=False, description="是否为危险操作")


tool = Tool(name="query_workorder", description="查询产线工单记录")
print(tool.dangerous)
```

> `Field(...)` 的两个常用参数：`description`（说明）、`default`（默认值）。
> 有 `default` 的字段可以不传，没有的必须传。

### 练习 8

```python
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    name: str = Field(description="参数名")
    type: str = Field(default="string", description="参数类型")
    description: str = Field(default="", description="参数说明")


class Tool(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter] = []


tool = Tool(
    name="query_workorder",
    description="查询产线工单记录",
    parameters=[
        ToolParameter(name="line", description="产线编号"),
        ToolParameter(name="date", description="日期"),
    ],
)

print(tool.parameters[0].name)
print(len(tool.parameters))
```

> 注意 `parameters[0].name` —— Pydantic 会自动把字典转成 `ToolParameter` 对象，可以直接用点访问。

### 练习 9

```python
import json

data = tool.model_dump()
print(data)
# {'name': 'query_workorder', 'description': '查询产线工单记录', 'parameters': [...]}

tool2 = Tool.model_validate(data)
print(tool2 == tool)      # True

schema = tool.model_json_schema()
print(json.dumps(schema, indent=2, ensure_ascii=False))
```

> 三个方法的用途：
> - `model_dump()` —— 模型 → 字典（存数据库、发 HTTP 请求）
> - `model_validate()` —— 字典 → 模型（接收外部数据时用）
> - `model_json_schema()` —— 生成 JSON Schema（**给 LLM 看**）

### 练习 10

```python
from pydantic import BaseModel, Field
import json


class QueryWorkOrderArgs(BaseModel):
    """查询产线工单记录"""
    line: str = Field(description="产线编号，例如 3号线")
    date: str = Field(description="日期，格式 YYYY-MM-DD")
    limit: int = Field(default=10, description="最多返回多少条记录")


print(json.dumps(QueryWorkOrderArgs.model_json_schema(), indent=2, ensure_ascii=False))
```

输出的 Schema 大致长这样：

```json
{
  "properties": {
    "line": {
      "description": "产线编号，例如 3号线",
      "title": "Line",
      "type": "string"
    },
    "date": {
      "description": "日期，格式 YYYY-MM-DD",
      "title": "Date",
      "type": "string"
    },
    "limit": {
      "default": 10,
      "description": "最多返回多少条记录",
      "title": "Limit",
      "type": "integer"
    }
  },
  "required": ["line", "date"],
  "title": "QueryWorkOrderArgs",
  "type": "object"
}
```

> **`required` 里只有 `line` 和 `date`** —— 因为 `limit` 有默认值。
>
> 这个 JSON 就是发给 LLM 的东西。LLM 读到它就知道：这个工具有三个参数，`line` 和 `date` 必填，`limit` 可选。
>
> **你在 LangChain 里写的每一个工具，背后都在生成这个。**

---

## 做完之后的自我检查

能不能回答这三个问题？

1. `list[dict]` 和 `list[MessageDict]` 有什么区别？为什么后者更好？
2. `Annotated[list, add_messages]` 里的 `add_messages` 是干什么的？
3. `model_json_schema()` 生成的东西最终给谁看？

**答得出来，模块 D 就过了。**
