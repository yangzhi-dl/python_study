# 模块 F 练习 —— 异步与流式

> **配套文档**：`README.md` 模块 F（异步与流式）
> **这一模块的特点**：概念最抽象，所以全部从**可运行的效果**切入
> **目标**：能读懂 `async def` / `await` / `yield` / `async for` 混在一起的代码

---

## 为什么这模块重要

LangChain 的流式输出长这样：

```python
async for chunk in llm.astream(messages):
    print(chunk.content, end="")
```

`astream` 返回的就是**异步生成器**，`async for` 是消费它的语法。

**这两个东西看不懂，流式输出就没法写。** 而流式输出是 Agent 产品的标配（打字机效果）。

---

# Part 1 · 先看效果：同步 vs 异步

## 1.1 同步版本（串行）

```python
import time


def fetch(name: str, seconds: float) -> str:
    print(f"  开始请求 {name}")
    time.sleep(seconds)          # 模拟网络等待
    print(f"  完成请求 {name}")
    return f"{name} 的结果"


def main_sync():
    start = time.perf_counter()

    results = []
    for name in ["工单", "质检", "BOM"]:
        results.append(fetch(name, 1))

    elapsed = time.perf_counter() - start
    print(f"结果: {results}")
    print(f"总耗时: {elapsed:.2f} 秒")


if __name__ == "__main__":
    main_sync()
```

**输出**：

```
  开始请求 工单
  完成请求 工单
  开始请求 质检
  完成请求 质检
  开始请求 BOM
  完成请求 BOM
结果: ['工单 的结果', '质检 的结果', 'BOM 的结果']
总耗时: 3.00 秒
```

**注意输出顺序**：一个一个来，前面没完成，后面不会开始。

## 1.2 异步版本（并发）

```python
import asyncio
import time


async def fetch_async(name: str, seconds: float) -> str:
    print(f"  开始请求 {name}")
    await asyncio.sleep(seconds)     # ← 注意：不是 time.sleep
    print(f"  完成请求 {name}")
    return f"{name} 的结果"


async def main_async():
    start = time.perf_counter()

    results = await asyncio.gather(
        fetch_async("工单", 1),
        fetch_async("质检", 1),
        fetch_async("BOM", 1),
    )

    elapsed = time.perf_counter() - start
    print(f"结果: {results}")
    print(f"总耗时: {elapsed:.2f} 秒")


if __name__ == "__main__":
    asyncio.run(main_async())
```

**输出**：

```
  开始请求 工单
  开始请求 质检
  开始请求 BOM
  完成请求 工单
  完成请求 质检
  完成请求 BOM
结果: ['工单 的结果', '质检 的结果', 'BOM 的结果']
总耗时: 1.00 秒
```

**两个关键差异**：

| | 同步 | 异步 |
|---|---|---|
| 输出顺序 | 开始→完成→开始→完成 | **三个都开始**，然后陆续完成 |
| 总耗时 | 3 秒 | **1 秒** |

**为什么能快 3 倍？**

因为 `time.sleep(1)` 是**真的在睡**——CPU 干等着；而 `await asyncio.sleep(1)` 是**让出控制权**——"我要等 1 秒，这期间你去干别的"。

**这就是异步的本质：等待的时候不闲着。**

## 1.3 一个关键澄清

异步**不是**让代码跑得更快，而是**让等待时间重叠**。

- 计算密集型任务（比如算 100 万次循环）→ **异步没用**，甚至更慢
- IO 密集型任务（网络请求、读写文件、查数据库）→ **异步收益巨大**

Agent 开发属于后者：**大量时间花在等 LLM 响应**。所以异步是刚需。

---

# Part 2 · 生成器 yield（异步的基础）

理解 `async for` 之前，必须先理解 `yield`。

## 2.1 普通函数 vs 生成器

```python
def make_list():
    return [1, 2, 3]        # 一次性生成全部，返回整个列表


def make_gen():
    yield 1                  # 给一个，暂停
    yield 2                  # 再给一个，暂停
    yield 3                  # 再给一个
```

**区别**：

| | 普通函数 | 生成器 |
|---|---|---|
| 返回 | 一次返回全部 | 一次给一个 |
| 内存 | 全部装进内存 | 用一个产一个 |
| 关键字 | `return` | `yield` |

## 2.2 观察执行过程（重点）

```python
def count_up(n: int):
    print(">>> 生成器开始执行")
    for i in range(n):
        print(f"    [产出前] i={i}")
        yield i
        print(f"    [恢复后] i={i}")
    print(">>> 生成器结束")


gen = count_up(3)
print("① 拿到生成器对象（此时函数体还没执行）")

print("② 开始消费：")
for value in gen:
    print(f"    [消费到] {value}")

print("③ 结束")
```

**输出**：

```
① 拿到生成器对象（此时函数体还没执行）
② 开始消费：
>>> 生成器开始执行
    [产出前] i=0
    [消费到] 0
    [恢复后] i=0
    [产出前] i=1
    [消费到] 1
    [恢复后] i=1
    [产出前] i=2
    [消费到] 2
    [恢复后] i=2
>>> 生成器结束
③ 结束
```

**这张输出是理解 `yield` 的钥匙**，注意看：

- `①` 时函数体**一行都没执行**——只是创建了对象
- `②` 开始后，`产出` 和 `消费` **交替进行**
- 每次 `yield` 把值交出去后**暂停**，等下一次 `for` 要值时**从暂停处继续**

**一句话**：`yield` = "交出一个值 + 记住当前位置 + 暂停"。

## 2.3 手动消费（`next()`）

```python
gen = count_up(3)

print(next(gen))     # 0
print(next(gen))     # 1
print(next(gen))     # 2
print(next(gen))     # 抛 StopIteration
```

`for` 循环内部就是不停调 `next()`，直到捕获 `StopIteration` 才停。

## 2.4 生成器的实际用途

**为什么不用列表？**

```python
# 列表版：一次性生成 100 万条，占满内存
def read_all_lines(path):
    return [line for line in open(path)]      # 文件大就爆内存

# 生成器版：读一行给一行
def read_lines(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line
```

**核心价值**：**按需生产，不占内存**。

这也是为什么 LLM 流式输出用生成器——**模型生成一个字，就立刻推给你一个字**，不用等全部生成完。

---

# Part 3 · async / await

## 3.1 三个关键字

```python
async def get_data():            # ① async def 定义"协程函数"
    result = await something()    # ② await 等待一个异步操作
    return result


asyncio.run(get_data())          # ③ 入口，启动事件循环
```

| 关键字 | 作用 |
|---|---|
| `async def` | 定义一个**协程函数** |
| `await` | 等待异步操作完成，**等待期间让出控制权** |
| `asyncio.run()` | 启动事件循环，运行协程（程序入口） |

## 3.2 一个容易懵的点：调用 async 函数不会立即执行

```python
async def hello():
    print("hello 被执行了")
    return "结果"


coro = hello()               # 不打印任何东西！
print(type(coro))            # <class 'coroutine'>
print(coro)                  # <coroutine object hello at 0x...>

result = asyncio.run(coro)   # 这时才真正执行
print(result)                # 结果
```

**关键理解**：`async def` 定义的函数，调用它只返回一个**协程对象**（相当于"待执行的任务单"），必须交给事件循环才会真正跑。

## 3.3 `await` 到底在等什么

```python
import asyncio


async def step1():
    print("step1 开始")
    await asyncio.sleep(1)
    print("step1 结束")
    return "A"


async def step2():
    print("step2 开始")
    await asyncio.sleep(1)
    print("step2 结束")
    return "B"


async def main():
    print("=== 顺序 await（总共 2 秒）===")
    a = await step1()
    b = await step2()
    print(f"结果: {a}, {b}")


asyncio.run(main())
```

输出：

```
=== 顺序 await（总共 2 秒）===
step1 开始
step1 结束
step2 开始
step2 结束
结果: A, B
```

**`await` 是"顺序等待"** —— 一个完成才轮到下一个。要并发，得用 `asyncio.gather`（Part 4）。

---

# Part 4 · asyncio.gather 并发

## 4.1 基本用法

```python
import asyncio


async def main():
    print("=== gather 并发（总共 1 秒）===")
    results = await asyncio.gather(
        step1(),
        step2(),
    )
    print(f"结果: {results}")


asyncio.run(main())
```

输出：

```
=== gather 并发（总共 1 秒）===
step1 开始
step2 开始
step1 结束
step2 结束
结果: ['A', 'B']
```

**注意**：两个 `开始` 都在前面 —— 说明是同时启动的。

## 4.2 gather vs 逐个 await

| 写法 | 耗时 | 什么时候用 |
|---|---|---|
| `await a(); await b()` | 2 秒 | 有先后依赖（b 需要 a 的结果） |
| `await asyncio.gather(a(), b())` | 1 秒 | 互不依赖，可以并行 |

**Agent 场景**：同时查工单、查质检、查 BOM —— 三个查询互不依赖，用 gather 能省 2/3 时间。

## 4.3 一个坑：gather 里传的是"协程对象"

```python
# ✅ 正确
await asyncio.gather(fetch("a"), fetch("b"))

# ❌ 错误：传了结果而不是协程
await asyncio.gather(fetch("a"), fetch("b"))   # 如果 fetch 不是 async 函数，这里会报错
```

---

# Part 5 · 异步生成器 async for（流式输出的核心）

## 5.1 什么是异步生成器

**同步生成器**：`def` + `yield`
**异步生成器**：`async def` + `yield`

```python
async def async_gen():
    yield 1
    yield 2
    yield 3
```

**消费方式不同**：

```python
# 同步生成器
for x in sync_gen():
    ...

# 异步生成器
async for x in async_gen():
    ...
```

## 5.2 完整例子：模拟 LLM 流式输出（重点）

这个例子是**你以后写打字机效果的模板**：

```python
import asyncio


async def fake_llm_stream(prompt: str):
    """模拟 LLM 逐字返回（真实场景里是 llm.astream）"""
    response = "3号产线的不良根因是：回流焊温度偏低 5 度。"

    for char in response:
        await asyncio.sleep(0.05)     # 模拟网络延迟
        yield char                     # 一个字一个字往外吐


async def main():
    print("用户: 3号产线为什么不良？")
    print("助手: ", end="", flush=True)

    async for chunk in fake_llm_stream("3号产线为什么不良？"):
        print(chunk, end="", flush=True)

    print()     # 换行


asyncio.run(main())
```

**运行效果**：文字一个一个字蹦出来（打字机效果）。

**关键点**：
- `flush=True` —— 强制立即输出，不然会被缓冲住，看不到逐字效果
- `end=""` —— 不换行，让字连起来

## 5.3 对比 LangChain 的真实写法

```python
# 你现在写的（模拟版）
async for chunk in fake_llm_stream(prompt):
    print(chunk, end="", flush=True)

# 真实 LangChain（几乎一模一样）
async for chunk in llm.astream(messages):
    print(chunk.content, end="", flush=True)
```

**结构完全一样**，只是 `chunk` 从字符串变成了 `AIMessageChunk` 对象，要取 `.content`。

**这就是为什么模块 F 值得花时间。**

## 5.4 同步 vs 异步生成器对照

| | 同步生成器 | 异步生成器 |
|---|---|---|
| 定义 | `def f(): yield` | `async def f(): yield` |
| 消费 | `for x in f()` | `async for x in f()` |
| 里面能 await | ❌ | ✅ |
| 典型用途 | 读大文件 | **LLM 流式输出** |

---

# Part 6 · 三个必踩的坑

## 坑 1 · 忘了 await

```python
async def get_data():
    return "数据"


async def main():
    result = get_data()          # ❌ 忘了 await
    print(result)                # <coroutine object get_data at 0x7f...>
    print(type(result))          # <class 'coroutine'>


asyncio.run(main())
```

**症状**：打印出来是 `<coroutine object ...>`，不是你要的数据。

**原因**：没 `await`，拿到的是"任务单"而不是"任务结果"。

**修复**：`result = await get_data()`

> 这个坑 PyCharm 通常会警告：`Coroutine 'get_data' was never awaited`

## 坑 2 · 在 async 函数里用 time.sleep

```python
import asyncio
import time


async def bad():
    time.sleep(1)            # ❌ 整个事件循环被卡死 1 秒
    return "ok"


async def good():
    await asyncio.sleep(1)   # ✅ 让出控制权
    return "ok"
```

**区别**：

- `time.sleep(1)` —— **真的在睡**，CPU 干等，其他所有任务全部停摆
- `await asyncio.sleep(1)` —— **让出控制权**，事件循环去跑别的任务

**症状**：你写了 `async`，但并发完全没生效，总耗时还是串行的。

**规则**：**async 函数里只能调异步版本的 IO 操作**。遇到 `time.sleep` / `requests.get` / 同步文件读写，要么换成异步版，要么用 `asyncio.to_thread()` 包一层。

```python
# 把阻塞操作丢到线程池里跑
result = await asyncio.to_thread(blocking_function, arg1, arg2)
```

## 坑 3 · 在已有事件循环里再调 asyncio.run

```python
# ❌ 在 Jupyter Notebook / 已运行的事件循环里会报错
asyncio.run(main())
```

**报错**：`RuntimeError: asyncio.run() cannot be called from a running event loop`

**原因**：`asyncio.run()` 会创建新的事件循环，但一个线程只能有一个。

**修复**：
- Jupyter 里直接用 `await main()`（Jupyter 本身就跑在事件循环里）
- 或者在普通脚本里用 `asyncio.run()`（这是正常场景）

---

# Part 7 · 三个"认得即可"的概念

## 7.1 迭代器协议 `__iter__` / `__next__`

生成器背后就是这个协议。你不需要手写，但看到要认识：

```python
class Counter:
    def __init__(self, n):
        self.n = n
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.i >= self.n:
            raise StopIteration
        self.i += 1
        return self.i
```

**用 `yield` 写同样的功能，代码少一半** —— 所以实际开发几乎不手写这个协议。

## 7.2 contextvars

异步代码里，"全局变量"不可靠——因为多个协程会互相干扰。

`contextvars` 提供"协程级别的全局变量"：

```python
import contextvars

request_id = contextvars.ContextVar("request_id", default="unknown")

request_id.set("req-123")
print(request_id.get())      # req-123
```

**你不需要主动用它**，但 LangGraph / FastAPI 内部会用来传上下文（比如 trace_id）。

## 7.3 事件循环（一句话理解）

**事件循环就是一个 `while` 循环**，不断检查：

```
while 有任务:
    找出所有"可以继续跑"的任务
    跑它们，直到遇到 await
    遇到 await 就挂起，回去找别的
```

**所以异步是"并发"不是"并行"** —— 同一时刻只有一个任务在跑，只是等待时切换。

---

# 练习

## 练习 1 · 同步改异步

把下面这段同步代码改成异步版，让总耗时从 3 秒降到 1 秒：

```python
import time


def query(source: str) -> str:
    print(f"查询 {source}")
    time.sleep(1)
    return f"{source} 的数据"


def main():
    results = []
    for s in ["工单", "质检", "BOM"]:
        results.append(query(s))
    print(results)


main()
```

> 考察：`async def`、`await`、`asyncio.gather`、`asyncio.run`

## 练习 2 · 写一个生成器

写一个生成器 `chunks(text, size)`，把长文本按固定长度切块返回。

```python
for c in chunks("abcdefghij", 3):
    print(c)
```

期望输出：

```
abc
def
ghi
j
```

> 考察：`yield`、切片

## 练习 3 · 手动消费生成器

用 `next()` 手动从 `chunks("abcdefghij", 3)` 里取前两块，然后打印剩下没取的。

> 考察：生成器是"一次性的"——取过就没了

## 练习 4 · 写一个异步生成器

写一个 `countdown(n)`，从 n 倒数到 1，每个数字间隔 0.5 秒产出。用 `async for` 消费。

```python
async for num in countdown(3):
    print(num)
```

期望：每隔 0.5 秒打印一个数字。

> 考察：`async def` + `yield` + `async for`

## 练习 5 · 找 bug

下面代码有 **2 个 bug**，找出来并修复：

```python
import asyncio
import time


async def fetch(name):
    print(f"开始 {name}")
    time.sleep(1)
    return f"{name} 完成"


async def main():
    a = fetch("A")
    b = fetch("B")
    results = await asyncio.gather(a, b)
    print(results)


asyncio.run(main())
```

> 提示：想想"事件循环被阻塞"和"协程对象没被 await"。

---

## 过关标准

| 内容 | 标准 |
|---|---|
| Part 1 | 能解释"为什么异步能快 3 倍" |
| Part 2 · `yield` | **能说清"暂停 + 恢复"的过程** |
| Part 3 · `async/await` | 不看资料能写出 `async def` + `await` + `asyncio.run` |
| Part 4 · `gather` | 知道什么时候用 gather、什么时候顺序 await |
| Part 5 · `async for` | **能独立写出流式输出的例子** |
| Part 6 · 三个坑 | 能识别"忘了 await"和"用了 time.sleep" |
| Part 7 | 认得即可 |

---

## 参考答案

> **先自己写完再看。**

<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

### 练习 1

```python
import asyncio


async def query(source: str) -> str:
    print(f"查询 {source}")
    await asyncio.sleep(1)
    return f"{source} 的数据"


async def main():
    results = await asyncio.gather(
        query("工单"),
        query("质检"),
        query("BOM"),
    )
    print(results)


asyncio.run(main())
```

> 三处改动：`def` → `async def`、`time.sleep` → `await asyncio.sleep`、`for` 循环 → `asyncio.gather`。

### 练习 2

```python
def chunks(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i:i + size]


for c in chunks("abcdefghij", 3):
    print(c)
```

> `range(0, 10, 3)` 产生 `0, 3, 6, 9`，配合切片 `text[i:i+3]` 就能切块。
> 最后一块 `text[9:12]` 会自动截断到 `j`，不会报错。

### 练习 3

```python
gen = chunks("abcdefghij", 3)

print(next(gen))     # abc
print(next(gen))     # def

print("剩下的:", list(gen))    # ['ghi', 'j']
```

> **关键**：生成器是**一次性的**——`next()` 取走的部分不会再出现，`list(gen)` 只能拿到剩下的。

### 练习 4

```python
import asyncio


async def countdown(n: int):
    for i in range(n, 0, -1):
        await asyncio.sleep(0.5)
        yield i


async def main():
    async for num in countdown(3):
        print(num)


asyncio.run(main())
```

输出：

```
3
2
1
```

> 注意：`async def` 里可以有 `yield`，这就是异步生成器。
> 里面可以 `await`，这是它和同步生成器最大的区别。

### 练习 5 · 找 bug

**Bug 1**：`time.sleep(1)` 会阻塞整个事件循环

```python
time.sleep(1)              # ❌
await asyncio.sleep(1)     # ✅
```

**Bug 2**：`a = fetch("A")` 没有 await，拿到的是协程对象

```python
a = fetch("A")             # ❌ 这是协程对象
```

**说明**：`asyncio.gather(a, b)` 传协程对象是合法的（gather 会帮你 await），但直接传调用结果更清晰，也能避免"创建了协程却忘了 await"的隐患。

**修复后**：

```python
import asyncio


async def fetch(name):
    print(f"开始 {name}")
    await asyncio.sleep(1)          # ✅ 修复 1
    return f"{name} 完成"


async def main():
    a = fetch("A")                  # 创建协程对象（还没执行）
    b = fetch("B")
    results = await asyncio.gather(a, b)    # gather 会 await 它们
    print(results)


asyncio.run(main())
```

**补充说明**：`gather` 接受协程对象是合法的，它会内部 await。所以这题真正的 bug 是 **`time.sleep` 阻塞事件循环**。

> 更严谨的写法是直接传调用结果：
> ```python
> results = await asyncio.gather(fetch("A"), fetch("B"))
> ```
> 这样更清晰，也不会有"创建了协程但没 await"的风险。

---

## 做完之后的自我检查

1. `time.sleep(1)` 和 `await asyncio.sleep(1)` 的区别是什么？
2. `yield` 执行时，函数是"结束"了还是"暂停"了？
3. `async for` 和普通 `for` 有什么区别？
4. 为什么异步能提升 IO 密集型任务的性能，但对计算密集型没用？
5. 在 Agent 里，`astream()` 返回的是什么？

**答得出来，模块 F 就过了。**
