# 模块 A 练习 —— 用 Agent 场景学会 Python 基础

> **配套文档**：`README.md` 模块 A（语言基础）
> **用法**：每题先自己写 → 卡住了翻菜鸟教程查语法 → 最后对照文末参考答案
> **目标**：不看资料能写出来。抄一遍不算学会，关掉示例能写出来才算。

---

## 贯穿所有练习的数据结构

这就是 Agent 里 `messages` 的真实形状，后面每一题都用它：

```python
messages = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良，帮我查原因"},
    {"role": "assistant", "content": "好的，我先查一下3号产线的工单记录"},
    {"role": "user", "content": "重点是昨天下午那批"},
    {"role": "assistant", "content": "已找到，下午2点到5点有3个批次异常"},
]
```

**先把这 5 行敲进 PyCharm，跑一遍 `print(messages)` 看清楚它的结构。**

---

## 练习 1 · list / dict 基础

打印出所有 `role` 为 `user` 的消息的 `content`。

> 考察：dict 取值、for 循环、if 判断

---

## 练习 2 · 切片

取出**最近 3 条**消息，赋值给变量 `recent`。

> 考察：负索引、切片

---

## 练习 3 · 推导式

用**一行**代码，取出所有 user 消息，组成新列表 `user_msgs`。

> 考察：列表推导式

---

## 练习 4 · 嵌套与统计

统计每种 `role` 各出现了多少次，输出成一个 dict，形如 `{"system": 1, "user": 2, "assistant": 2}`。

> 考察：dict 累加、`.get()` 给默认值

---

## 练习 5 · 函数 + 默认参数

写一个函数 `build_context(messages, max_count=3)`：

- 只取最后 `max_count` 条
- 返回拼接成的一段文本，每行格式为 `role: content`
- 用换行符 `\n` 分隔

调用 `build_context(messages)` 和 `build_context(messages, 2)`，看结果差异。

> 考察：函数定义、默认参数、切片、字符串 join

---

## 练习 6 · `**kwargs`（重点）

写一个函数 `call_llm(messages, **kwargs)`，把传入的额外参数打印出来。

然后这样调用：

```python
call_llm(messages, temperature=0.7, model="gpt-4", max_tokens=1024)
```

要求输出能看清每个参数名和值。

> 考察：`**kwargs` 的接收与遍历
> **为什么重要**：LangChain 的每个调用都是这个形状 —— `llm.invoke(messages, temperature=0.7, ...)`

---

## 练习 7 · 函数是一等公民（重点）

写一个函数 `apply_to_messages(func, messages)`，把 `func` 应用到每条消息上，返回新列表。

然后传一个 `lambda m: m["content"]` 进去，打印结果。

> 考察：函数作为参数传递
> **为什么重要**：`builder.add_node("agent", call_model)` 之所以成立，就是因为函数能当参数传

---

## 练习 8 · 解包

用**一行**代码，把 messages 拆成 `first`（第一条）和 `rest`（剩下所有）。

> 考察：解包赋值

---

## 练习 9 · 综合（最接近真实代码）

写一个函数：

```python
def summarize_messages(messages, max_count=3, include_system=False):
    ...
```

要求：

1. 当 `include_system=False` 时，过滤掉所有 `role == "system"` 的消息
2. 从过滤后的结果里取最后 `max_count` 条
3. 返回格式化字符串，每行 `role: content`

> 考察：函数、默认参数、条件判断、推导式、切片、join —— 模块 A 全部知识点的串联

---

## 过关标准

9 题全部**不看答案、不查资料**能写出来 → 模块 A 通过。

写不出来的题，回去翻菜鸟教程对应章节，然后再关掉教程重写一遍。

---

## 参考答案

> **先自己写完再看。** 直接看答案等于没做。

<br><br><br><br><br><br><br><br><br><br>

### 练习 1

```python
for msg in messages:
    if msg["role"] == "user":
        print(msg["content"])
```

### 练习 2

```python
recent = messages[-3:]
print(recent)
```

### 练习 3

```python
user_msgs = [m for m in messages if m["role"] == "user"]
print(user_msgs)
```

### 练习 4

```python
counts = {}
for msg in messages:
    role = msg["role"]
    counts[role] = counts.get(role, 0) + 1
print(counts)
```

> `.get(role, 0)` 是关键：角色第一次出现时返回 0，避免 KeyError。

### 练习 5

```python
def build_context(messages, max_count=3):
    recent = messages[-max_count:]
    lines = [f'{m["role"]}: {m["content"]}' for m in recent]
    return "\n".join(lines)


print(build_context(messages))
print("---")
print(build_context(messages, 2))
```

### 练习 6

```python
def call_llm(messages, **kwargs):
    print(f"消息条数: {len(messages)}")
    print("额外参数:")
    for key, value in kwargs.items():
        print(f"  {key} = {value}")


call_llm(messages, temperature=0.7, model="gpt-4", max_tokens=1024)
```

> `kwargs` 在函数内部是一个普通的 dict，所以能 `.items()` 遍历。
> 反过来，调用时用 `**some_dict` 就能把 dict 展开成关键字参数。

### 练习 7

```python
def apply_to_messages(func, messages):
    return [func(m) for m in messages]


contents = apply_to_messages(lambda m: m["content"], messages)
print(contents)
```

> `func` 是一个参数，但它可以接收函数 —— 这就是"函数是一等公民"。

### 练习 8

```python
first, *rest = messages
print(first)
print(rest)
```

> `*rest` 表示"剩下的都收进 rest 这个 list"。

### 练习 9

```python
def summarize_messages(messages, max_count=3, include_system=False):
    filtered = messages
    if not include_system:
        filtered = [m for m in messages if m["role"] != "system"]

    recent = filtered[-max_count:]
    lines = [f'{m["role"]}: {m["content"]}' for m in recent]
    return "\n".join(lines)


print(summarize_messages(messages))
print("---")
print(summarize_messages(messages, max_count=2, include_system=True))
```

> 这题已经非常接近 Agent 里的真实代码了。做完这题，你就理解了"上下文裁剪"是怎么实现的。
