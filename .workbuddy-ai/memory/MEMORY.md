# PythonStudy — 项目记忆

> 精简版（2026-11-01 整理）。详细协作规则见项目根目录 `CODEBUDDY.md`，本文件只记"事实与状态"。

## 一、项目基本信息

| 项 | 内容 |
|---|---|
| 路径 | `C:\Users\Yandel\Desktop\PythonStudy`（2026-10-25 由 `Python学习` 改名，旧路径已清空） |
| 类型 | PyCharm 项目 |
| 用途 | Ember 学 Python + Agent 实操的主目录 |
| 主线 | Python 基础 → LangChain → LangGraph → 不良品根因追溯智能体 |

## 二、学习标准的正确划分（重要，曾被误解）

- **Python 语言本身 → 必须自己会写**（容器、函数、类、类型注解、异常、async、装饰器）
- **框架与库（LangChain / LangGraph / FastAPI）→ 看懂 + 能改 + 能说清原理即可**
- 不要把整个清单降级成"看懂"。Python 基础必须能独立写。

## 三、学习进度

文档在 `docs/studyPlan/`（`README.md` 已定稿，**不要擅自修改**，新增材料另建文件）。

| 模块 | 状态 |
|---|---|
| A 语言基础 | 已完成（2026-10-14），自建 13 个专项训练 + 9 道综合题 |
| B 工程环境 | 基本完成（2026-10-15） |
| C 面向对象 | 已完成（2026-10-16），9 题 |
| D 类型系统与 Pydantic | 已完成（2026-10-17），10 题 |
| E 错误处理 / F 异步 / G 装饰器 / H 工程化 | 练习已出，按需做 |

**下一步**：已进入 LangChain/LangGraph 实操阶段（Ember 处于求职准备期）。

### 学习路线文档

- `langchain-langgraph-roadmap.md` —— 完整项目路线（4–6 周，含工程化）
- `langchain-langgraph-core-steps.md` —— **求职向精简版（2 周，优先用这份）**，7 阶段 + 面试高频 20 问
- 核心是阶段 3（手写工具调用循环）和阶段 5（手写 ReAct 图）；「什么时候不该用 Agent」比「怎么用」更重要；最大风险是过度设计

## 四、LangChain 实操代码环境

**目录**：`studyLangChain_LangGraph/mini-project/LangChainLangGraph_workbuddy/`
（`studyLangChain` 已改名为 `studyLangChain_LangGraph`）

- 命名 `ch章节_小节_内容.py`，每个文件可独立运行，支持 `--offline` 和数字参数
- 文件顶部写「跑这个能看到什么」+「怎么跑」
- 环境：Python 3.13 / venv 在 `mini-project/.venv` / langchain 1.4.6 / langchain-core 1.6.12 / langchain-openai 1.7.2 / langgraph / pydantic 2.14.1
- 模型：`deepseek-v4-flash-0731`（百炼专属实例，配置在 `mini-project/.env`）

## 五、技术红线（实测踩过的坑）

**LangChain**
1. `with_structured_output` 必须显式 `method="function_calling"`；`json_schema` 必然失败，`json_mode` 返回垃圾
2. 裸 `@tool` 参数无 description，docstring 的 `Args:` 不生效 → 要加描述/约束必须 `args_schema=BaseModel`；无 docstring 创建即 `ValueError`
3. `bind_tools` 是替换不是累加，要多个就一次给全
4. 消息对象：`.text` 是 property；`.type` 是 `system/human/ai/tool`；`.id` 是 `lc_run--xxx`
5. Prompt 模板：`input_variables` 排序后；`MessagesPlaceholder` 不加 `optional=True` 就是必填（缺了报裸 `KeyError`）；字面花括号双写 `{{}}`
6. 流式：`usage_metadata` 在**第一个 chunk** 就有；`astream` 的 chunk 要判空（思考模式前 13 个 `.text` 为空）
7. 模型走思考模式，`output_token_details` 里有 `reasoning`，也计费（一次结构化输出约 600–700 token，其中约 160 推理）
8. 多个 async Demo 不能各自 `asyncio.run`（`Event loop is closed`），共用一个循环
9. 工具异常先发 `on_tool_error` 再抛；执行器仍要 `try/except` 转 ToolMessage 回填

**LangGraph**
10. `recursion_limit` 默认值不构成保护（实测 1000 次循环能跑完），必须显式设
11. `interrupt()` 恢复时整个节点从头重跑 → 之前不能放副作用
12. SubGraph 父子只交换【同名字段】，独有字段天然隔离
13. `add_sequence` 参数是 `[(名字, 函数)]` 且不自动连 START/END
14. `stream_mode` 五种：values/updates/messages/custom/debug；`messages` 的 metadata 有 `langgraph_node`；`custom` 用 `get_stream_writer()` 不进 State
15. `msg.tool_calls` 只有 AIMessage 有 → `getattr(msg, "tool_calls", None)`
16. `compile()` 只校验有无入口，图结构问题用 `get_graph().draw_mermaid()` 人工过
17. **思考模式下 `tool_choice` 只能是 `auto` / `none`**（2026-11-02 实测）：当前实例 `qwen3.8-2.4t-a95b` 强制开启思考模式，`enable_thinking` 锁死为 `True`（传 `False` 直接 400）。`tool_choice="required"` 或指定函数对象会报 `The tool_choice parameter does not support being set to required or object in thinking mode`。`ch01_06` 的 Demo 6 已改为 try/except 降级打印

## 六、协作与风格（详细见 CODEBUDDY.md）

- 代码由 AI 写，Ember 看懂 + 核对；**交付前必须实际运行验证**，不能只做语法检查
- 可读性优先于 Pythonic：类型注解写全、一步一行、中文注释、少用推导式/lambda/链式
- **print 只打数据，不打讲解**（2026-11-01 Ember 明确："print 太多看得头痛"，教学文字留在对话里）
- 解释代码按 5 点讲（2026-11-01 新版 CODEBUDDY.md）：请求从哪进 / 数据怎么流转 / 模型和工具在哪调 / 数据库在哪读写 / 报错查哪里。**不要逐行翻译语法**
- **解释要短**：一次只讲透一个点（如"`@tool` 干了什么"），不要一次性铺开全部
- 不要主动追加"风险提示 / 建议你要不要…"这类没被问到的意见
- 练习目录/文件 Ember 用中文命名（`基础训练` 等），不必纠正

## 七、约定与限制

- 命名：文件夹与文件用**事件英文名**，不要用日期
- 破坏性操作（删除、批量移动）前必须确认
- 沙箱限制：无法调用 `wsl.exe` / `docker.exe` / `whoami.exe` 等原生 exe；需要交互认证的操作（如 `git push`）需 Ember 手动执行
- 不要删除 `.workbuddy-ai/`；不要在项目里写 API Key（放 `.env`）

## 八、Git

- 远程 `https://github.com/yangzhi-dl/python_study.git`，分支 `main`
- 首次提交 `e67becd`，**尚未推送到 GitHub**（沙箱无法交互输入凭证，需 Ember 手动 `git push`，用 PAT）
- `.gitignore` 忽略 `.venv/`、`.env`、`__pycache__/`、`.idea/`、数据与模型文件；`.workbuddy-ai/` 会提交

## 九、环境排查经验

- **编辑器标红但能运行** = PyCharm 索引/缓存问题 → `File → Invalidate Caches...`（运行时 python.exe 按 `pyvenv.cfg` 找包，不看 IDE 配置）
- `ModuleNotFoundError` 第一步先查 `python -c "import sys; print(sys.executable)"`，不是重装包
- 切换 venv 三种方式：项目解释器 / 运行配置 / 终端激活

## 十、规则文件机制（实测）

| 文件 | 作用 |
|---|---|
| `CODEBUDDY.md` | 主推，纯 Markdown，全文注入 |
| `AGENTS.md` | 兼容，CODEBUDDY.md 不存在时加载 |
| `CODEBUDDY.local.md` | 本地覆盖，已加 .gitignore |
| `.codebuddy/rules/` | 结构化规则，带 frontmatter（always / agent-requested / manual） |
| `.workbuddy-ai/memory/MEMORY.md` | 本文件，始终注入 system prompt |

注意：`CODEBUDDY.md` 会进 git，不能放密钥和个人绝对路径。
