# 不良品根因追溯 Agent —— 最小可运行版本

> 这是**阶段 1** 的骨架：单 Agent + 3 个工具 + 假数据。
> 目标不是"能用"，是"能跑通、能看懂、能改"。

---

## 怎么跑

### 1. 装依赖

```bash
cd practice/agent_demo
source ../../module_b_environment/mini_project/.venv/Scripts/activate
pip install langchain langchain-openai python-dotenv
```

> 如果你已经在别的 venv 里装过 langchain，直接用那个环境也行。

### 2. 配 Key

把 `.env.example` 复制成 `.env`，填上你的 Key：

```
API_KEY=sk-xxx
BASE_URL=            # 用中转接口的话填地址，官方留空
MODEL_NAME=gpt-4o
```

### 3. 跑

```bash
python main.py
```

---

## 你会看到什么

`main.py` 会打印**完整的消息链**，形如：

```
[0] HumanMessage: 3号线 2026-10-24 的不良原因是什么？
[1] AIMessage:
     → 调用工具: query_workorder, 参数: {'line': '3号线', 'date': '2026-10-24'}
[2] ToolMessage: 3号线 2026-10-24 共 5 个批次：...
[3] AIMessage:
     → 调用工具: query_quality, 参数: {'batch_id': 'B002'}
[4] ToolMessage: 批次 B002 不良项: 焊缝气孔...
...
[9] AIMessage: 根因是回流焊峰值温度偏低...
```

**这条链就是 ReAct 循环的实际样子**：
```
用户提问 → 模型想"要查工单" → 执行 → 模型看结果 → 想"要查质检" → 执行 → ... → 给结论
```

---

## 三个文件的分工

| 文件 | 职责 | 你要改的时候 |
|---|---|---|
| `tools.py` | 定义工具 + 假数据 | 换真实数据源、加新工具 |
| `main.py` | 配置模型、系统提示、入口 | 调行为、改问题、改输出格式 |
| `.env` | 密钥和模型配置 | 换 Key / 换模型 |

---

## 接下来改什么（按顺序）

### ① 换问题

`main.py` 里把 `question` 改成别的问题，看 Agent 怎么反应：

- "3号线 2026-10-23 的情况怎么样？"（这天没有异常批次）
- "B002 这个批次有什么问题？"（直接给批次号）
- "3号线昨天的不良是不是来料问题？"（需要它想到查 BOM）

**观察**：模型会不会选错工具、会不会多查一步、会不会乱猜。

### ② 改工具描述

把 `query_workorder` 的 docstring 改得含糊一点：

```python
"""查询"""
```

再跑一次，看模型还会不会正确调用。

**这一步能让你亲眼看到：docstring 对工具调用的影响有多大。**

### ③ 加一个新工具

比如 `query_equipment(equipment_id)` 查设备参数。

只需要：
1. 在 `tools.py` 里加一个 `@tool` 函数
2. 加到 `ALL_TOOLS` 列表里

**不用改 main.py** —— 这就是 `create_agent` 方便的地方。

### ④ 换真实数据

把 `WORKORDERS` / `QUALITY_RECORDS` 的字典查询换成数据库查询。

**只改 tools.py，其他不动。**

---

## 已知的局限（这就是阶段 2、3 要解决的）

| 局限 | 说明 | 怎么解决 |
|---|---|---|
| 假数据 | 字典写死 | 阶段 1 后期接真实数据源 |
| 单轮对话 | 每次 `invoke` 都是新会话 | 加 checkpointer（阶段 2） |
| 没有证据链 | 结论里没强制标注来源 | 改 prompt + 结构化输出（阶段 2） |
| 没有审计日志 | 谁问了什么、调了什么工具，没留痕 | 加 JSONL 日志（阶段 3） |
| 可能死循环 | 模型一直调工具 | 设 `recursion_limit`（阶段 2） |
| 无法人工确认 | 危险操作直接执行 | LangGraph 的 `interrupt`（阶段 2） |

**这些不是 bug，是阶段 1 的边界。** 一个一个加。
