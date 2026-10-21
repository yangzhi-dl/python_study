# 模块 G 练习 —— 装饰器

> **配套文档**：`README.md` 模块 G（装饰器）
> **这一模块的特点**：装饰器是 Python 里最"魔法"的东西，所以从零拆解，不跳步
> **目标**：理解 `@deco` 的机制，能写简单装饰器，看懂 `@tool` 在干什么

---

## 为什么这模块重要

LangChain 的工具长这样：

```python
from langchain_core.tools import tool

@tool
def query_workorder(line: str) -> str:
    """查询产线工单记录"""
    return "..."
```

**这一行 `@tool` 背后到底发生了什么？** 搞懂装饰器，你就能自己回答。

而且——**模块 C 的 `Tool` 类 + 模块 D 的 Pydantic + 模块 G 的装饰器**，这三块拼起来，就是 LangChain 工具的完整原理。这模块是收尾。

---

# Part 1 · 前提：函数是一等公民

装饰器能存在，全靠一个前提：**Python 里函数和普通变量没区别**。

```python
def say_hello():
    print("hello")


# ① 函数可以赋值给变量
greet = say_hello
greet()                    # hello

# ② 函数可以当参数传
def call_twice(func):
    func()
    func()

call_twice(say_hello)      # hello hello

# ③ 函数可以当返回值
def get_greeter():
    return say_hello

g = get_greeter()
g()                        # hello
```

**Java 对照**：Java 8 之前做不到（只能传接口实现），Java 8+ 有 Lambda 和方法引用才能类似。

Python 从第一天就这样——**函数就是对象**。

---

# Part 2 · 手动实现一个"装饰"

**先不用 `@` 语法**，手写一遍，你就懂了。

## 2.1 目标

写一个计时器，测量函数执行耗时。

**最笨的写法**（在每个函数里重复写）：

```python
import time


def work():
    start = time.perf_counter()
    time.sleep(0.5)
    print("干完活了")
    print(f"耗时 {time.perf_counter() - start:.4f} 秒")


def another_work():
    start = time.perf_counter()
    time.sleep(0.3)
    print("另一个活干完了")
    print(f"耗时 {time.perf_counter() - start:.4f} 秒")
```

**问题**：每加一个函数就要复制一遍计时逻辑。**重复代码，违反 DRY。**

## 2.2 用"函数套函数"解决

```python
import time


def timer(func):
    """接收一个函数，返回一个"加了计时功能"的新函数"""

    def wrapper():
        start = time.perf_counter()
        func()                              # 调用原来的函数
        elapsed = time.perf_counter() - start
        print(f"耗时 {elapsed:.4f} 秒")

    return wrapper


def work():
    time.sleep(0.5)
    print("干完活了")


# 关键这一行：
work = timer(work)
work()
```

**输出**：

```
干完活了
耗时 0.5003 秒
```

## 2.3 拆解这一行

```python
work = timer(work)
#      └──┬──┘ └─┬─┘
#        ①      ②
```

| 步骤 | 发生了什么 |
|---|---|
| ② | 把原来的 `work` 函数**作为参数**传给 `timer` |
| ① | `timer` 返回 `wrapper` 函数，**赋回给 `work`** |

**执行完后**，`work` 这个名字指向的已经不是原来的函数了，而是 `wrapper`。

**这就是"装饰"**：给函数套了一层壳，功能增强了，名字没变。

## 2.4 完整执行流程

```python
def timer(func):
    print(f"[timer] 收到函数: {func.__name__}")
    def wrapper():
        print("[wrapper] 开始计时")
        func()
        print("[wrapper] 计时结束")
    print("[timer] 返回 wrapper")
    return wrapper


def work():
    print("[work] 我在干活")


print("--- 装饰前 ---")
work = timer(work)

print("--- 调用 work() ---")
work()
```

**输出**：

```
--- 装饰前 ---
[timer] 收到函数: work
[timer] 返回 wrapper
--- 调用 work() ---
[wrapper] 开始计时
[work] 我在干活
[wrapper] 计时结束
```

**注意**：`timer(work)` 执行时，`wrapper` **只是被定义，没有被调用**——所以看不到 `[wrapper] 开始计时`。

直到 `work()` 才真正执行 `wrapper` 内部。

---

# Part 3 · `@` 只是语法糖

```python
# 写法 A
def work():
    ...
work = timer(work)


# 写法 B（完全等价）
@timer
def work():
    ...
```

**`@timer` 就是 `work = timer(work)` 的简写。**

Python 在定义完 `work` 之后，**立刻**把它传给 `timer`，再把返回值赋回 `work`。

## 3.1 语法糖的意义

```python
@timer
@logger
@retry
def work():
    ...
```

**等价于**：

```python
work = timer(logger(retry(work)))
```

**装饰器从下往上应用**（离函数最近的先执行）。

这个顺序在排查问题时很重要。

---

# Part 4 · `*args` / `**kwargs`（关键细节）

Part 2 的 `wrapper()` **没有参数**。如果被装饰的函数有参数，就废了：

```python
@timer
def add(a, b):
    return a + b

add(1, 2)     # ❌ TypeError: wrapper() takes 0 positional arguments but 2 were given
```

**因为调用 `add(1, 2)` 实际调用的是 `wrapper(1, 2)`，而 `wrapper` 不接受参数。**

## 4.1 正确写法

```python
import functools
import time


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)        # ← 原样转发所有参数
        elapsed = time.perf_counter() - start
        print(f"[timer] {func.__name__} 耗时 {elapsed:.4f} 秒")
        return result                          # ← 原样返回结果
    return wrapper


@timer
def add(a, b):
    return a + b


print(add(1, 2))       # [timer] add 耗时 0.0000 秒  →  3
```

## 4.2 三个必须做的动作

| 动作 | 代码 | 忘了会怎样 |
|---|---|---|
| 接收任意参数 | `def wrapper(*args, **kwargs)` | 有参函数直接报错 |
| 原样转发 | `func(*args, **kwargs)` | 参数丢失 |
| 原样返回 | `return result` | 被装饰函数返回 `None` |

**第三点最容易忘**——如果 `wrapper` 不 `return`，调用 `add(1, 2)` 会得到 `None`，而不是 `3`。

> 这就是模块 A 学的 `*args` / `**kwargs` 的实战用途。

---

# Part 5 · `functools.wraps`（元信息保护）

## 5.1 问题

```python
@timer
def work():
    """这是 work 函数的说明"""
    time.sleep(0.1)


print(work.__name__)      # wrapper      ← 不是 work！
print(work.__doc__)       # None         ← 文档丢了！
```

**原因**：装饰后 `work` 指向的是 `wrapper`，所以 `__name__` 和 `__doc__` 都是 `wrapper` 的。

## 5.2 影响

- **调试时看不出来是哪个函数**（所有装饰过的函数都叫 `wrapper`）
- **文档生成工具抓不到说明**
- **LangChain 的 `@tool` 会读取函数名和 docstring 当工具名和描述**——如果被覆盖，工具就没有名字和描述了！

## 5.3 修复

```python
import functools


def timer(func):
    @functools.wraps(func)          # ← 这一行
    def wrapper(*args, **kwargs):
        ...
    return wrapper
```

`functools.wraps(func)` 会把原函数的 `__name__`、`__doc__`、`__module__` 等元信息**复制到 wrapper 上**。

验证：

```python
@timer
def work():
    """这是 work 函数的说明"""
    ...

print(work.__name__)     # work    ✅
print(work.__doc__)      # 这是 work 函数的说明    ✅
```

**规则：写装饰器一律加 `@functools.wraps(func)`**，别问为什么，养成习惯。

---

# Part 6 · 带参数的装饰器（能改即可）

## 6.1 需求

```python
@retry(max_attempts=5)      # ← 装饰器本身带参数
def unstable():
    ...
```

## 6.2 结构：三层嵌套

```python
import functools
import time


def retry(max_attempts: int = 3, delay: float = 1.0):
    # 第一层：接收装饰器参数，返回真正的装饰器
    def decorator(func):
        # 第二层：接收被装饰的函数
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 第三层：真正执行的地方
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        print(f"[retry] 第 {attempt + 1} 次失败: {e}，{delay} 秒后重试")
                        time.sleep(delay)
            raise last_error
        return wrapper
    return decorator
```

## 6.3 为什么是三层

```python
@retry(max_attempts=5)
def unstable(): ...
```

**展开过程**：

```python
# 第一步：先执行 retry(max_attempts=5)，返回 decorator
decorator = retry(max_attempts=5)

# 第二步：再执行 decorator(unstable)，返回 wrapper
unstable = decorator(unstable)
```

所以：
- **第一层** `retry(...)` —— 接收配置
- **第二层** `decorator(func)` —— 接收函数
- **第三层** `wrapper(...)` —— 实际执行

## 6.4 对比：不带参数的装饰器只有两层

```python
def timer(func):              # 第一层：接收函数
    def wrapper(*args):       # 第二层：执行
        ...
    return wrapper
```

**记住这个规律**：
- 不带参数 → **两层**
- 带参数 → **三层**

---

# Part 7 · `@tool` 到底做了什么（重点收尾）

## 7.1 你写的样子

```python
from langchain_core.tools import tool


@tool
def query_workorder(line: str, date: str) -> str:
    """查询产线工单记录

    Args:
        line: 产线编号，例如 3号线
        date: 日期，格式 YYYY-MM-DD
    """
    return f"{line} 在 {date} 的工单..."
```

## 7.2 它做了什么

`@tool` 会读取三样东西：

| 读什么 | 变成什么 |
|---|---|
| 函数名 `query_workorder` | 工具名 `name` |
| docstring | 工具描述 `description`（**给 LLM 看的**） |
| 类型注解 `line: str, date: str` | 参数 JSON Schema（**内部用 Pydantic 生成**） |

然后它**返回一个 `StructuredTool` 对象**，替换掉原来的函数。

## 7.3 等价于手写什么

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class QueryWorkOrderArgs(BaseModel):
    line: str = Field(description="产线编号，例如 3号线")
    date: str = Field(description="日期，格式 YYYY-MM-DD")


def query_workorder_impl(line: str, date: str) -> str:
    return f"{line} 在 {date} 的工单..."


query_workorder = StructuredTool.from_function(
    func=query_workorder_impl,
    name="query_workorder",
    description="查询产线工单记录",
    args_schema=QueryWorkOrderArgs,
)
```

**看出联系了吗？**

| 模块 | 学到的东西 | 在这里的作用 |
|---|---|---|
| 模块 C | `Tool` 类、`to_schema()` | 工具的数据结构 |
| 模块 D | `BaseModel` / `Field` / `model_json_schema()` | 参数 Schema 的生成 |
| 模块 G | 装饰器 | 把上面两件事自动串起来 |

**`@tool` 就是"用装饰器把这三步自动化"的产物。**

## 7.4 为什么必须有 `@functools.wraps` 或等价机制

因为 `@tool` 要读**函数名和 docstring**。如果装饰器把 `__name__` 覆盖成 `wrapper`，工具名就全变成 `wrapper` 了——LLM 根本分不清调哪个。

这就是 Part 5 说的"元信息保护"为什么重要。

---

# 练习

## 练习 1 · 写一个 `@timer`

要求：
- 打印函数名和执行耗时
- 支持任意参数的函数
- 保留原函数的 `__name__` 和 `__doc__`

```python
@timer
def slow_add(a: int, b: int) -> int:
    """慢速加法"""
    time.sleep(0.1)
    return a + b


print(slow_add(1, 2))       # 3
print(slow_add.__name__)    # slow_add
```

## 练习 2 · 写一个 `@logger`

打印函数名、参数、返回值：

```python
@logger
def greet(name: str) -> str:
    return f"你好, {name}"


greet("Ember")
```

期望输出：

```
[logger] 调用 greet(name='Ember')
[logger] greet 返回: 你好, Ember
```

> 提示：用 `inspect.signature` 或手动拼 `args` / `kwargs`

## 练习 3 · 写一个 `@retry`（带参数）

要求：失败重试 N 次，间隔 0.5 秒。

```python
attempt = 0


@retry(max_attempts=3, delay=0.5)
def unstable():
    global attempt
    attempt += 1
    if attempt < 3:
        raise ValueError(f"第 {attempt} 次失败")
    return "成功"


print(unstable())     # 成功
```

## 练习 4 · 找出 bug

```python
import time


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        func(*args, **kwargs)
        print(f"耗时 {time.perf_counter() - start:.4f} 秒")
    return wrapper


@timer
def add(a, b):
    return a + b


print(add(1, 2))
```

**问题**：输出是什么？为什么？

> 提示：想想 Part 4 的"三个必须做的动作"。

## 练习 5 · 理解题

不看资料，用自己的话回答：

1. `@timer` 加在函数上，等价于哪一行代码？
2. 不带参数的装饰器有几层嵌套？带参数的几层？
3. 为什么装饰器一定要写 `@functools.wraps(func)`？
4. `@tool` 从你写的函数里读走了哪三样东西？

---

## 过关标准

| 内容 | 标准 |
|---|---|
| Part 2、3 | 能说清"装饰 = 把函数传进去，拿新函数回来" |
| Part 4 | **能写出带 `*args, **kwargs` 的 wrapper** |
| Part 5 | 知道为什么必须加 `@functools.wraps` |
| Part 6 | 能看懂三层结构（不要求默写） |
| Part 7 | **能说出 `@tool` 读走了什么** |
| 练习 1 | 不看资料能写出来 |

---

## 参考答案

> **先自己写完再看。**

<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

### 练习 1

```python
import functools
import time


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[timer] {func.__name__} 耗时 {elapsed:.4f} 秒")
        return result
    return wrapper


@timer
def slow_add(a: int, b: int) -> int:
    """慢速加法"""
    time.sleep(0.1)
    return a + b


print(slow_add(1, 2))
print(slow_add.__name__)
print(slow_add.__doc__)
```

> 四个要素齐全：`@functools.wraps`、`*args/**kwargs`、原样转发、原样返回。

### 练习 2

```python
import functools


def logger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 把参数拼成 name='Ember' 这种形式
        parts = []
        for a in args:
            parts.append(repr(a))
        for k, v in kwargs.items():
            parts.append(f"{k}={v!r}")

        print(f"[logger] 调用 {func.__name__}({', '.join(parts)})")
        result = func(*args, **kwargs)
        print(f"[logger] {func.__name__} 返回: {result}")
        return result
    return wrapper


@logger
def greet(name: str) -> str:
    return f"你好, {name}"


greet("Ember")
```

> `{v!r}` 用 repr 格式，字符串会带引号，方便看出是字符串还是数字。

### 练习 3

```python
import functools
import time


def retry(max_attempts: int = 3, delay: float = 0.5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        print(f"[retry] 第 {attempt + 1} 次失败: {e}，{delay} 秒后重试")
                        time.sleep(delay)
            raise last_error
        return wrapper
    return decorator


attempt = 0


@retry(max_attempts=3, delay=0.5)
def unstable():
    global attempt
    attempt += 1
    if attempt < 3:
        raise ValueError(f"第 {attempt} 次失败")
    return "成功"


print(unstable())
```

输出：

```
[retry] 第 1 次失败: 第 1 次失败，0.5 秒后重试
[retry] 第 2 次失败: 第 2 次失败，0.5 秒后重试
成功
```

> 三层结构：`retry(...)` → `decorator(func)` → `wrapper(...)`。

### 练习 4

**输出**：

```
耗时 0.0000 秒
None
```

**两个问题**：

1. **`wrapper` 没有 `return`** —— 所以 `add(1, 2)` 返回 `None`，`print` 出来就是 `None`
2. **没加 `@functools.wraps`** —— 虽然这题不影响输出，但是隐患

**修复**：

```python
def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)      # ← 接住结果
        print(f"耗时 {time.perf_counter() - start:.4f} 秒")
        return result                        # ← 返回结果
    return wrapper
```

> **这是写装饰器最容易犯的错**——忘了 `return`，被装饰的函数就"静默失效"了，返回值全变 `None`。

### 练习 5 · 理解题

**1.** `@timer` 等价于 `work = timer(work)`

**2.** 不带参数 **两层**（`timer` → `wrapper`），带参数 **三层**（`retry` → `decorator` → `wrapper`）

**3.** 因为装饰后 `函数名` 指向的是 `wrapper`，如果不加 `wraps`，原函数的 `__name__`、`__doc__` 会被覆盖。后果：
- 调试时所有函数都叫 `wrapper`
- 文档生成抓不到说明
- **LangChain 的 `@tool` 读不到工具名和描述**

**4.** `@tool` 读走三样：
- **函数名** → 工具名
- **docstring** → 工具描述（给 LLM 看的）
- **类型注解** → 参数 JSON Schema

---

## 做完之后的自我检查

如果这五个问题都能答上来，基础部分就齐了：

1. `@deco` 等价于哪一行？
2. `wrapper` 为什么必须用 `*args, **kwargs`？
3. 为什么必须 `return result`？
4. 为什么必须 `@functools.wraps(func)`？
5. `@tool` 读走了哪三样东西？

**答得出来，模块 G 就过了——可以进 LangChain 了。**
