# 模块 C 练习 —— 用 Agent 场景学会面向对象

> **配套文档**：`README.md` 模块 C（面向对象）
> **用法**：每题先自己写 → 卡住了翻菜鸟教程查语法 → 最后对照文末参考答案
> **目标**：不看答案能写出来。抄一遍不算学会。

---

## 最终目标：造出这几个类

```
Message          一条消息（有 role 和 content）
└─ SystemMessage 系统消息（继承 Message，role 固定）
Tool             一个工具的定义（有 name、description、parameters）
```

这三个类，加上你模块 A、B 学的东西，就能拼出一个 Agent 的最小骨架。

**做完这 9 题，你会掌握 Agent 项目里 90% 的类设计。**

---

## 知识点对照表

| README 模块 C 知识点 | 对应练习 | 档位 |
|---|---|---|
| `class` / `__init__` / `self` | 练习 1 | 会写 |
| 属性、方法 | 练习 1、2 | 会写 |
| 魔术方法 `__repr__` | 练习 3 | 认得（但写一次就记住） |
| 继承、`super()` | 练习 4 | 会写 |
| 方法覆盖（override） | 练习 5 | 会写 |
| `@dataclass` | 练习 6、9 | 会写 |
| `@property` | 练习 7 | 能改 |
| `@classmethod` | 练习 8 | 能改 |
| 综合运用 | 练习 9 | 会写 |

---

## 练习 1 · 最基础的类

定义一个 `Message` 类，有 `role` 和 `content` 两个属性，通过构造传入。

要求能这样用：

```python
msg = Message("user", "3号产线有不良")
print(msg.role)      # user
print(msg.content)   # 3号产线有不良
```

> 考察：`class` 定义、`__init__`、`self`

<details>
<summary>Java 对照</summary>

```java
public class Message {
    private String role;
    private String content;

    public Message(String role, String content) {   // ← 对应 __init__
        this.role = role;                            // ← this 对应 self
        this.content = content;
    }
}
```

**两个差异**：
- Python 用 `__init__` 而不是类名当构造方法
- Python 的 `self` **必须显式写**（Java 的 `this` 是隐式的）
</details>

---

## 练习 2 · 加一个方法

给 `Message` 加一个方法 `to_text()`，返回 `"role: content"` 格式的字符串。

```python
msg = Message("user", "3号产线有不良")
print(msg.to_text())     # user: 3号产线有不良
```

> 考察：方法的定义与调用、`self` 在方法里怎么用

---

## 练习 3 · `__repr__`（让 print 变好看）

现在直接 `print(msg)` 会输出类似 `<__main__.Message object at 0x000001A2B3C4>` —— 完全看不懂。

给 `Message` 加 `__repr__` 方法，让它输出：

```python
print(msg)     # <Message user: 3号产线有不良>
```

> 考察：魔术方法（双下划线方法）
> **为什么需要**：调试时 `print(对象)` 能直接看到内容，不用一个个属性点出来

---

## 练习 4 · 继承 + `super()`

定义 `SystemMessage` 类，继承 `Message`，但 `role` 固定为 `"system"`，只需要传 `content`。

```python
sys_msg = SystemMessage("你是不良品根因分析助手")
print(sys_msg.role)      # system
print(sys_msg.content)   # 你是不良品根因分析助手
print(sys_msg.to_text()) # system: 你是不良品根因分析助手
```

> 考察：继承、`super().__init__()` 的调用

<details>
<summary>Java 对照</summary>

```java
public class SystemMessage extends Message {      // ← Python 写 (Message)
    public SystemMessage(String content) {
        super("system", content);                  // ← 一样是 super
    }
}
```
</details>

---

## 练习 5 · 方法覆盖

`SystemMessage` 的 `to_text()` 要改成 `"[系统] content"` 的格式（覆盖父类的实现）。

```python
sys_msg = SystemMessage("你是助手")
print(sys_msg.to_text())     # [系统] 你是助手

msg = Message("user", "你好")
print(msg.to_text())         # user: 你好   ← 父类不受影响
```

> 考察：方法覆盖（override）—— 子类定义同名方法，会盖住父类的

---

## 练习 6 · `@dataclass`（代码量砍一半）

用 `@dataclass` 重写 `Message` 类，看看能省多少代码。

要求功能一样：

```python
msg = Message("user", "你好")
print(msg.role)          # user
print(msg)               # Message(role='user', content='你好')
```

**对比一下**：不用 dataclass 时你写了多少行？用了之后呢？

> 考察：`@dataclass` 装饰器
> **它自动帮你生成**：`__init__`、`__repr__`、`__eq__`

<details>
<summary>Java 对照</summary>

```java
@Data                    // ← Lombok 注解，效果几乎一样
public class Message {
    private String role;
    private String content;
}
```

Python 的 `@dataclass` 就是内置版的 Lombok `@Data` —— 自动生成构造方法、`toString`、`equals`。
</details>

---

## 练习 7 · `@property`（能改即可）

定义一个 `Tool` 类，有 `name` 和 `description`。再加一个 `is_dangerous` 属性，判断这个工具是否危险。

```python
t1 = Tool("delete_file", "删除文件")
t2 = Tool("query_workorder", "查询工单")

print(t1.is_dangerous)   # True
print(t2.is_dangerous)   # False
```

**关键要求**：`is_dangerous` 调用时**不加括号**，像普通属性一样访问。

危险工具名单：`delete_file`、`execute_shell`、`drop_table`

> 考察：`@property` —— 把方法伪装成属性
> **为什么需要**：调用方不用关心它是算出来的还是存起来的

---

## 练习 8 · `@classmethod`（能改即可）

给 `Message` 加一个**类方法** `from_dict()`，从字典创建实例。

```python
data = {"role": "user", "content": "你好"}
msg = Message.from_dict(data)
print(msg.role)      # user
```

**关键区别**：
- 普通方法第一个参数是 `self`（实例）
- 类方法第一个参数是 `cls`（类本身）

> 考察：`@classmethod`
> **为什么需要**：这是"工厂方法"模式，Agent 项目里从 JSON 还原对象时天天用

<details>
<summary>Java 对照</summary>

```java
public static Message fromDict(Map<String, String> data) {   // ← static 工厂方法
    return new Message(data.get("role"), data.get("content"));
}
```

Python 的 `@classmethod` 类似 Java 的静态工厂方法，区别是它**能感知子类**（`cls` 会变成子类而不是父类）。
</details>

---

## 练习 9 · 综合（最接近真实代码）

用 `@dataclass` 定义 `Tool` 类，包含：

- `name: str`
- `description: str`
- `parameters: dict`

再加一个方法 `to_schema()`，返回 OpenAI 工具调用格式的字典：

```python
tool = Tool(
    name="query_workorder",
    description="查询产线工单记录",
    parameters={"type": "object", "properties": {"line": {"type": "string"}}},
)

print(tool.to_schema())
```

期望输出：

```python
{
    "type": "function",
    "function": {
        "name": "query_workorder",
        "description": "查询产线工单记录",
        "parameters": {"type": "object", "properties": {"line": {"type": "string"}}},
    },
}
```

> 考察：`@dataclass` + 方法 + 嵌套字典构造 —— 模块 C 全部知识点的串联
> **这题做通，你就理解了 LangChain 里 `@tool` 装饰器背后在干什么**

---

## 过关标准

- **练习 1、2、4、5、9**：不看答案能写出来（这五题是【会写】档）
- **练习 3、6**：写出来最好，写不出能看懂也行
- **练习 7、8**：能照着改就行，不强求默写

---

## 参考答案

> **先自己写完再看。** 直接看答案等于没做。

<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

### 练习 1

```python
class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content


msg = Message("user", "3号产线有不良")
print(msg.role)
print(msg.content)
```

> `self` 就是"这个实例自己"。`self.role = role` 的意思是：把参数 `role` 存到实例身上。

### 练习 2

```python
class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def to_text(self):
        return f"{self.role}: {self.content}"


msg = Message("user", "3号产线有不良")
print(msg.to_text())
```

> 注意：`to_text` 的第一个参数必须是 `self`，虽然调用时不用传。

### 练习 3

```python
    def __repr__(self):
        return f"<Message {self.role}: {self.content}>"
```

> `__repr__` 是"对象的字符串表示"。定义了它，`print(对象)` 和调试器里都会用它。

### 练习 4

```python
class SystemMessage(Message):
    def __init__(self, content):
        super().__init__("system", content)


sys_msg = SystemMessage("你是不良品根因分析助手")
print(sys_msg.role)
print(sys_msg.content)
print(sys_msg.to_text())
```

> `super().__init__("system", content)` = 调用父类的构造方法，把 role 写死成 "system"。
> `to_text()` 不用重写，因为继承下来了。

### 练习 5

```python
class SystemMessage(Message):
    def __init__(self, content):
        super().__init__("system", content)

    def to_text(self):
        return f"[系统] {self.content}"
```

> 子类定义了同名方法，就盖住了父类的 —— 这叫**方法覆盖**。父类 `Message` 不受影响。

### 练习 6

```python
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


msg = Message("user", "你好")
print(msg.role)
print(msg)
```

> 对比：不用 dataclass 要写 `__init__`（3 行）+ `__repr__`（2 行）；用了之后只写两个字段。
> 注意字段必须**带类型注解**（`: str`），这是 dataclass 的语法要求 —— 类型注解在模块 D 会正式学。

### 练习 7

```python
class Tool:
    DANGEROUS_NAMES = {"delete_file", "execute_shell", "drop_table"}

    def __init__(self, name, description):
        self.name = name
        self.description = description

    @property
    def is_dangerous(self):
        return self.name in self.DANGEROUS_NAMES


t1 = Tool("delete_file", "删除文件")
t2 = Tool("query_workorder", "查询工单")

print(t1.is_dangerous)
print(t2.is_dangerous)
```

> `@property` 加在方法上，调用时就**不用写括号**了。
> 危险名单放在类里当**类属性**（所有实例共享），不用每次调用都重建一个 set。

### 练习 8

```python
class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content

    @classmethod
    def from_dict(cls, data):
        return cls(data["role"], data["content"])


data = {"role": "user", "content": "你好"}
msg = Message.from_dict(data)
print(msg.role)
```

> `cls` 是类本身，`cls(...)` 相当于 `Message(...)`。
> 好处：如果子类调用 `SystemMessage.from_dict(...)`，`cls` 会自动变成 `SystemMessage`。

### 练习 9

```python
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict

    def to_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


tool = Tool(
    name="query_workorder",
    description="查询产线工单记录",
    parameters={"type": "object", "properties": {"line": {"type": "string"}}},
)

print(tool.to_schema())
```

> 这就是 LangChain 里 `@tool` 装饰器帮你自动生成的东西 —— 把 Python 函数转成 LLM 能看懂的 JSON Schema。

---

## 进阶提示（选做）

如果 `parameters` 想给个默认空字典，**不能这么写**：

```python
@dataclass
class Tool:
    parameters: dict = {}          # ❌ 错误！可变默认值陷阱
```

必须用 `field`：

```python
from dataclasses import dataclass, field

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict = field(default_factory=dict)     # ✅
```

**原因**：`{}` 在类定义时就创建了，所有实例会共享同一个字典——改一个全变。模块 A 的"可变对象陷阱"说的就是这个。

> 这是 Python 里出了名的坑，面试也爱问。知道有这回事就行，遇到再查。
