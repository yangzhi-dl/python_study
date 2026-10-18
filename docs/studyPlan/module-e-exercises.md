# 模块 E 练习 —— 错误处理与调试

> **配套文档**：`README.md` 模块 E（错误处理与调试）
> **这一模块的特点**：不讲抽象语法，全部基于**真实报错**。看完能直接用于排错。
> **目标**：看到任何报错，能三秒内说出「什么错、在哪错、怎么修」

---

## 为什么这模块最实用

写 Agent 时，**90% 的时间花在排错上**——模型返回的格式不对、工具参数缺字段、上下文超长、API 超时。

而这些问题的第一手信息，全部来自 **traceback**。

**会读 traceback 的人和不会的人，排错效率差 10 倍。**

---

# Part 1 · 看懂 traceback（核心技能）

## 1.1 traceback 长什么样

报错时控制台会打出一大坨东西，形如：

```
Traceback (most recent call last):
  File "main.py", line 15, in <module>
    print(build_context(MESSAGES))
  File "utils.py", line 6, in build_context
    lines.append(f'{m["role"]}: {m["content"]}')
KeyError: 'content'
```

很多人看到这一坨就慌了，直接复制去搜索。**其实它有固定的读法。**

## 1.2 读法：从下往上，三行搞定

```
KeyError: 'content'                                    ← ① 什么错
  File "utils.py", line 6, in build_context            ← ② 在哪错（最后一行 File）
    lines.append(f'{m["role"]}: {m["content"]}')       ← ③ 具体哪一句
  File "main.py", line 15, in <module>                 ← ④ 谁调用的（可略）
```

**读的顺序是反的**：

| 步骤 | 看哪里 | 得到什么 |
|---|---|---|
| ① | **最后一行** | 异常类型 + 消息：`KeyError: 'content'` |
| ② | **从下往上数，第一个 `File "你的代码"`** | 出错的文件和行号 |
| ③ | 那行下面的代码 | 具体出错的那句 |
| ④ | 继续往上 | 调用链（谁把它调起来的） |

**关键技巧**：如果 traceback 里有很多 `File "D:\Python3.10.10\lib\..."` 这样的行，**那是 Python 标准库内部，跳过不看**。找**最后一个属于你自己项目**的 `File` 行。

## 1.3 五种常见报错实战

### 实战 1 · KeyError

```python
# utils.py
def build_context(messages):
    lines = []
    for m in messages:
        lines.append(f'{m["role"]}: {m["content"]}')
    return "\n".join(lines)


# main.py
MESSAGES = [
    {"role": "system", "content": "你是助手"},
    {"role": "user"},                          # ← 少了 content
]
print(build_context(MESSAGES))
```

报错：

```
Traceback (most recent call last):
  File "main.py", line 8, in <module>
    print(build_context(MESSAGES))
  File "utils.py", line 5, in build_context
    lines.append(f'{m["role"]}: {m["content"]}')
KeyError: 'content'
```

**诊断**：`utils.py` 第 5 行，某个 dict 里没有 `'content'` 键。

**修复思路**：用 `.get()` 给默认值

```python
lines.append(f'{m["role"]}: {m.get("content", "")}')
```

---

### 实战 2 · TypeError

```python
def count_by_role(messages):
    ...

count_by_role(MESSAGES, 3)      # ← 多传了一个参数
```

```
Traceback (most recent call last):
  File "main.py", line 8, in <module>
    count_by_role(MESSAGES, 3)
TypeError: count_by_role() takes 1 positional argument but 2 were given
```

**诊断**：函数只接受 1 个位置参数，你传了 2 个。

**修复**：要么删掉多余参数，要么改函数签名。

---

### 实战 3 · ModuleNotFoundError

```
Traceback (most recent call last):
  File "main.py", line 2, in <module>
    from dotenv import load_dotenv
ModuleNotFoundError: No module named 'dotenv'
```

**诊断**：当前解释器没装 dotenv。

**排查顺序**（重要，你踩过这个坑）：

1. 先确认用的是哪个解释器
   ```bash
   python -c "import sys; print(sys.executable)"
   ```
2. 路径不对 → 问题在解释器选择，不在包
3. 路径对了但还是报错 → 真的没装，`pip install python-dotenv`

---

### 实战 4 · AttributeError

```python
msg = {"role": "user", "content": "你好"}
print(msg.content)          # ← 用点访问 dict
```

```
Traceback (most recent call last):
  File "main.py", line 3, in <module>
    print(msg.content)
AttributeError: 'dict' object has no attribute 'content'
```

**诊断**：`msg` 是 `dict`，字典只能用 `["key"]` 访问，不能用 `.key`。

**什么时候能用点？** 对象（比如 Pydantic 模型、dataclass 实例）才能用点。

---

### 实战 5 · 多层调用 + 库内部帧

```python
# utils.py
def load_messages(path):
    return json.loads(path.read_text())     # ← 文件是空的
```

```
Traceback (most recent call last):
  File "main.py", line 20, in <module>
    main()
  File "main.py", line 14, in main
    context = build_context(load_messages(path))
  File "utils.py", line 22, in load_messages
    return json.loads(path.read_text())
  File "D:\Python3.10.10\lib\json\__init__.py", line 346, in loads
    return _default_decoder.decode(s)
  File "D:\Python3.10.10\lib\json\decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
  File "D:\Python3.10.10\lib\json\decoder.py", line 355, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**这坨看起来吓人，其实很简单**：

- 最后一行：`JSONDecodeError: Expecting value: line 1 column 1 (char 0)` —— JSON 解析失败，第 1 行第 1 列就没东西
- **从下往上找第一个你的文件** → `utils.py, line 22`
- 那行是 `json.loads(path.read_text())` —— 说明传进去的字符串不是合法 JSON

**最常见原因**：文件是空的，或者内容是纯文本不是 JSON。

**中间那三行 `D:\Python3.10.10\lib\json\...` 全部跳过** —— 那是标准库内部，不是你的问题。

---

## 练习 1 · 诊断五个真实报错

下面是五个 traceback，请对每一个说出：**① 什么错 ② 在你的哪个文件哪一行 ③ 大概怎么修**。

**报错 A**

```
Traceback (most recent call last):
  File "main.py", line 9, in <module>
    print(messages[10]["content"])
IndexError: list index out of range
```

**报错 B**

```
Traceback (most recent call last):
  File "config.py", line 8, in <module>
    load_dotenv(ENV_PATH)
  File "D:\...\dotenv\main.py", line 322, in load_dotenv
    dotenv_path = find_dotenv()
  File "D:\...\dotenv\main.py", line 380, in find_dotenv
    raise IOError("Starting path not found")
OSError: Starting path not found
```

**报错 C**

```
Traceback (most recent call last):
  File "main.py", line 12, in <module>
    total = sum(counts.values())
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

**报错 D**

```
Traceback (most recent call last):
  File "main.py", line 5, in <module>
    from tools import query_workorder
ModuleNotFoundError: No module named 'tools'
```

**报错 E**

```
Traceback (most recent call last):
  File "main.py", line 18, in main
    result = tool.to_schema()
AttributeError: 'Tool' object has no attribute 'to_schema'
```

---

# Part 2 · 常见异常类型

## 2.1 八种必须认识的异常

| 异常 | 触发条件 | 典型例子 |
|---|---|---|
| `KeyError` | 字典里没有这个键 | `{"a": 1}["b"]` |
| `IndexError` | 列表越界 | `[1, 2, 3][10]` |
| `TypeError` | 类型不对 / 参数个数不对 | `len(123)` |
| `ValueError` | 类型对但值不对 | `int("abc")` |
| `AttributeError` | 对象没有这个属性/方法 | `"abc".foo()` |
| `FileNotFoundError` | 文件不存在 | `open("不存在.txt")` |
| `ModuleNotFoundError` | 模块没安装 | `import 没装的包` |
| `ZeroDivisionError` | 除以零 | `1 / 0` |

**注意 `TypeError` 和 `ValueError` 的区别**（最容易混）：

```python
int("abc")      # ValueError：类型对（是字符串），但内容不能转数字
int([1, 2])     # TypeError：类型就不对（列表根本不能转）
```

## 练习 2 · 判断会抛什么异常

对下面每一行，说出会抛什么异常（如果不会抛就写"正常"）：

```python
1.  {"role": "user"}["content"]
2.  [1, 2, 3][3]
3.  int("123")
4.  int("12.5")
5.  "abc" + 123
6.  len({"a": 1, "b": 2})
7.  {"a": 1}.get("b", 0)
8.  open("不存在的文件.txt").read()
9.  None.foo()
10. [1, 2, 3].append(4)
```

---

# Part 3 · try / except 的完整用法

## 3.1 基本结构

```python
try:
    risky()             # 可能出错的代码
except ValueError:
    handle_error()      # 出错时怎么办
```

**执行逻辑**：`try` 里的代码正常跑完 → 跳过 `except`；中途抛异常 → 立刻跳到匹配的 `except`。

## 3.2 四种变体

### 变体 1 · 捕获多个异常

```python
try:
    value = int(user_input)
    result = 100 / value
except (ValueError, ZeroDivisionError) as e:
    print(f"输入有问题: {e}")
```

> 用**元组**列出多个异常类型。`as e` 把异常对象接住，`e` 里就有错误消息。

### 变体 2 · 分别处理

```python
try:
    value = int(user_input)
    result = 100 / value
except ValueError:
    print("不是合法数字")
except ZeroDivisionError:
    print("不能除以零")
```

> 不同类型的错误，给不同的提示。

### 变体 3 · else（成功时才执行）

```python
try:
    content = path.read_text(encoding="utf-8")
except FileNotFoundError:
    print("文件不存在")
else:
    print(f"读取成功，共 {len(content)} 字符")
```

> `else` 里的代码**只有 try 没出错时才执行**。
> 为什么不直接写在 try 里？因为 try 里的代码如果出错会被 except 捕获，写在 else 里就不会被误捕。

### 变体 4 · finally（无论如何都执行）

```python
try:
    result = call_api()
except TimeoutError:
    print("请求超时")
finally:
    print("请求结束")        # 不管成功失败都会打印
    close_connection()
```

> `finally` 常用于**清理资源**（关文件、关连接）。

## 3.3 完整例子：加载配置文件

这个例子把四种变体全用上了，**建议照着敲一遍**：

```python
import json
from pathlib import Path


def load_config(path: Path) -> dict:
    """加载 JSON 配置文件，任何情况下都不让程序崩溃"""
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"[警告] 配置文件不存在: {path}，使用空配置")
        return {}
    except PermissionError:
        print(f"[警告] 没有权限读取: {path}")
        return {}
    except UnicodeDecodeError:
        print(f"[警告] 文件编码不是 UTF-8: {path}")
        return {}
    else:
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[警告] JSON 格式错误: {e}")
            return {}
    finally:
        print(f"[info] load_config 执行完毕: {path.name}")


config = load_config(Path(__file__).parent / "settings.json")
print(f"最终配置: {config}")
```

**这个函数的价值**：无论文件不存在、没权限、编码错、JSON 格式错，**它都不崩，只是返回空字典 + 打印警告**。

这就是"健壮代码"的写法。

## 练习 3 · 给函数加保护

下面这个函数，如果 `messages` 为空会抛 `ZeroDivisionError`，如果某条消息缺 `content` 会抛 `KeyError`。

请改写它，让它在两种情况下都**返回空字符串**而不是崩溃。

```python
def build_context(messages, max_count=3):
    recent = messages[-max_count:]
    lines = []
    for m in recent:
        lines.append(f'{m["role"]}: {m["content"]}')
    return "\n".join(lines)
```

---

# Part 4 · raise 与自定义异常

## 4.1 raise：主动抛异常

```python
def set_temperature(value):
    if not 0 <= value <= 2:
        raise ValueError(f"temperature 必须在 0-2 之间，收到 {value}")
    return value


set_temperature(5)
```

```
ValueError: temperature 必须在 0-2 之间，收到 5
```

**什么时候主动 raise？**

- 参数校验不通过
- 前置条件不满足（比如"必须先登录"）
- 内部状态异常，继续跑下去会更糟

**原则**：**早失败 > 带病运行**。参数不对就立刻抛，别让它跑到深处才炸。

## 4.2 自定义异常

```python
class ToolExecutionError(Exception):
    """工具执行失败"""
    pass


def execute_tool(name: str, args: dict):
    if not name:
        raise ToolExecutionError("工具名不能为空")
    ...
```

**为什么要自定义？**

| 好处 | 说明 |
|---|---|
| 语义清晰 | `ToolExecutionError` 比 `Exception` 一眼看出是什么问题 |
| 能精准捕获 | `except ToolExecutionError:` 只抓工具错误，不误伤其他 |

**最小写法**：继承 `Exception`，函数体写 `pass` 就行。

## 练习 4 · 参数校验

写一个函数 `create_message(role, content)`，要求：

- `role` 必须是 `"system"` / `"user"` / `"assistant"` 之一，否则 `raise ValueError`
- `content` 不能是空字符串，否则 `raise ValueError`

---

# Part 5 · Agent 里的四个真实场景（重点）

前面都是基础，这部分是**你写 Agent 时天天遇到的**。

## 场景 1 · 工具执行失败，不能让整个 Agent 崩

**问题**：LLM 决定调用某个工具，但工具执行时抛异常了。如果直接往外抛，整个 Agent 就挂了。

**正确做法**：**把错误信息返回给 LLM，让它自己决定怎么办**。

```python
def safe_execute_tool(tool_func, args: dict) -> str:
    """执行工具，失败时把错误信息变成字符串返回"""
    try:
        result = tool_func(**args)
        return str(result)
    except TypeError as e:
        return f"[工具参数错误] {e}"
    except Exception as e:
        return f"[工具执行失败] {type(e).__name__}: {e}"
```

**关键理解**：在 Agent 里，**错误不是终点，是给模型的一条信息**。模型看到"参数错误"可能会改参数重试。

## 场景 2 · LLM 返回的 JSON 解析失败

**问题**：你让 LLM 输出 JSON，它有时候会包在 ` ```json ` 代码块里，有时候会多说一句话。

```python
import json
import re


def parse_json_safely(text: str) -> dict:
    """尽最大努力从 LLM 输出里解析出 JSON"""
    # 先直接试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 再试着从 ```json ... ``` 代码块里提取
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 都不行，抛出带原文的错误，方便排查
    raise ValueError(f"无法从以下内容解析出 JSON:\n{text}")
```

**这个模式在 Agent 开发里极其常见**，建议直接收藏。

## 场景 3 · API 调用重试

**问题**：网络抖动、限流，第一次调用失败很正常。

```python
import time


def call_with_retry(func, max_retries: int = 3):
    """失败后重试，每次等待时间翻倍"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise                       # 最后一次还失败，往外抛
            wait = 2 ** attempt              # 1s, 2s, 4s
            print(f"第 {attempt + 1} 次失败: {e}，{wait} 秒后重试")
            time.sleep(wait)
```

**关键点**：`2 ** attempt` 叫**指数退避**（1、2、4 秒），避免短时间内反复冲击服务端。

## 场景 4 · 上下文超长

**问题**：消息越攒越多，超过模型的上下文窗口，API 直接报错。

```python
def trim_messages(messages: list, max_count: int = 20) -> list:
    """裁剪消息，但保留 system 消息"""
    if len(messages) <= max_count:
        return messages

    system_msgs = [m for m in messages if m.get("role") == "system"]
    other_msgs = [m for m in messages if m.get("role") != "system"]

    # system 保留，其余只留最近的
    return system_msgs + other_msgs[-(max_count - len(system_msgs)):]
```

**这就是 Pi Agent 里"上下文压缩"的最简版本** —— 保留 system 提示，砍掉旧对话。

## 练习 5 · 综合

把场景 1 和场景 3 结合起来：写一个 `call_tool_with_retry`，执行工具，失败重试 3 次，3 次都失败返回错误字符串（不抛异常）。

```python
def call_tool_with_retry(tool_func, args: dict, max_retries: int = 3) -> str:
    ...
```

---

# Part 6 · logging（能改即可）

`print` 调试的问题是：**上线后关不掉**。

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

logging.debug("这条不会显示（级别不够）")
logging.info("开始处理消息")
logging.warning("上下文接近上限")
logging.error("工具执行失败")
```

输出：

```
21:15:03 [INFO] 开始处理消息
21:15:03 [WARNING] 上下文接近上限
21:15:03 [ERROR] 工具执行失败
```

**五个级别**：`DEBUG < INFO < WARNING < ERROR < CRITICAL`

`level=logging.INFO` 表示只显示 INFO 及以上。改成 `DEBUG` 就能看到调试信息。

---

# Part 7 · with（能改即可）

```python
# 不用 with
f = open("file.txt", encoding="utf-8")
content = f.read()
f.close()                # ← 如果 read() 抛异常，这行永远执行不到，文件句柄泄漏

# 用 with
with open("file.txt", encoding="utf-8") as f:
    content = f.read()
# 离开 with 块自动 close，即使中间抛异常
```

**`with` 的本质**：保证"退出时一定执行清理"，等价于 try/finally 但更简洁。

---

## 过关标准

| 内容 | 标准 |
|---|---|
| Part 1 · 读 traceback | **五个报错能独立诊断**（这是本模块的核心） |
| Part 2 · 异常类型 | 八种能对上号 |
| Part 3 · try/except | 四种变体不看资料能写出来 |
| Part 4 · raise | 能写参数校验 |
| Part 5 · Agent 场景 | **能讲清楚"为什么工具错误要返回给 LLM 而不是抛出"** |
| Part 6、7 | 能看懂、能改 |

---

## 参考答案

> **先自己写完再看。**

<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

### 练习 1 · 诊断

**报错 A**
- 什么错：`IndexError` —— 列表索引越界
- 在哪：`main.py` 第 9 行
- 怎么修：`messages` 只有不到 11 条，改成 `messages[-1]` 或先判断 `len(messages)`

**报错 B**
- 什么错：`OSError: Starting path not found` —— `load_dotenv()` 没找到起点路径
- 在哪：`config.py` 第 8 行（后面两行 `D:\...\dotenv\...` 是库内部，跳过）
- 怎么修：给 `load_dotenv` 传明确的路径，或确认 `ENV_PATH` 指向的文件真的存在

**报错 C**
- 什么错：`TypeError` —— 不能把 `int` 和 `str` 相加
- 在哪：`main.py` 第 12 行
- 怎么修：`counts` 的 values 里混了字符串，检查数据来源，或用 `sum(int(v) for v in counts.values())`

**报错 D**
- 什么错：`ModuleNotFoundError` —— 找不到 `tools` 模块
- 在哪：`main.py` 第 5 行
- 怎么修：确认 `tools.py` 和 `main.py` 在同一目录；或检查是否在错误的工作目录运行

**报错 E**
- 什么错：`AttributeError` —— `Tool` 对象没有 `to_schema` 方法
- 在哪：`main.py` 第 18 行
- 怎么修：检查 `Tool` 类里是否定义了 `to_schema`；方法名是否拼错；是否缩进到了类外面

---

### 练习 2 · 异常类型判断

```python
1.  {"role": "user"}["content"]      → KeyError
2.  [1, 2, 3][3]                     → IndexError
3.  int("123")                       → 正常，结果是 123
4.  int("12.5")                      → ValueError（不能直接转小数）
5.  "abc" + 123                      → TypeError
6.  len({"a": 1, "b": 2})            → 正常，结果是 2
7.  {"a": 1}.get("b", 0)             → 正常，结果是 0（get 有默认值）
8.  open("不存在的文件.txt").read()   → FileNotFoundError
9.  None.foo()                       → AttributeError
10. [1, 2, 3].append(4)              → 正常，列表变成 [1,2,3,4]
```

---

### 练习 3 · 给函数加保护

```python
def build_context(messages: list, max_count: int = 3) -> str:
    if not messages:
        return ""

    try:
        recent = messages[-max_count:]
    except TypeError:
        return ""

    lines = []
    for m in recent:
        try:
            role = m["role"]
            content = m["content"]
        except (KeyError, TypeError):
            continue                    # 跳过结构不对的消息
        lines.append(f"{role}: {content}")

    return "\n".join(lines)
```

> 两种策略：**要么用 try 兜底，要么用 `.get()` 提前防御**。
> 这里两者结合：外层挡空列表，内层挡缺字段。

---

### 练习 4 · 参数校验

```python
VALID_ROLES = {"system", "user", "assistant"}


def create_message(role: str, content: str) -> dict:
    if role not in VALID_ROLES:
        raise ValueError(f"role 必须是 {VALID_ROLES} 之一，收到: {role!r}")
    if not content:
        raise ValueError("content 不能为空")
    return {"role": role, "content": content}
```

> `{role!r}` 里的 `!r` 是"用 repr 格式输出"，字符串会带引号，方便看出是空串还是空格。

---

### 练习 5 · 综合

```python
import time


def call_tool_with_retry(tool_func, args: dict, max_retries: int = 3) -> str:
    """执行工具，失败重试，全部失败返回错误字符串"""
    last_error = None

    for attempt in range(max_retries):
        try:
            return str(tool_func(**args))
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"第 {attempt + 1} 次失败: {e}，{wait} 秒后重试")
                time.sleep(wait)

    return f"[工具执行失败] 重试 {max_retries} 次仍失败: {type(last_error).__name__}: {last_error}"
```

> **注意最后的返回**：不是 `raise`，而是返回字符串。
> 因为这是给 Agent 用的——**错误要变成模型能读懂的信息**，而不是让程序崩掉。

---

## 做完之后的自我检查

1. 拿到一个 traceback，你的第一步看哪里？
2. `TypeError` 和 `ValueError` 怎么区分？
3. 在 Agent 里，工具执行失败为什么**不应该直接 raise**？
4. `finally` 和 `else` 分别在什么时候执行？

**答得出来，模块 E 就过了。**
