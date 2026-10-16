# Python 学习项目 — 项目约定

## 一、项目基本信息

| 项 | 内容 |
|---|---|
| 路径 | `C:\Users\Yandel\Desktop\Python学习` |
| 类型 | PyCharm 项目（已有 `.idea/` 配置） |
| Python SDK | **Python 3.10** |
| 用途 | Ember 学习 Python 的**主目录**，所有学习相关的代码、练习、笔记都放这里 |
| 接入时间 | 2026-10-13 |

## 二、学习标准的正确划分（重要）

**分两段，不要混为一谈：**

| 层次 | 对象 | 标准 |
|---|---|---|
| 第一段 | **Python 语言本身** | **必须自己会写** |
| 第二段 | **框架与库**（LangChain / LangGraph / FastAPI） | **看懂即可** |

- Python 基础（容器、函数、类、类型注解、异常、async、装饰器）→ 要能**不看资料写出来**
- 框架 API 用法 → 能看懂、能判断 AI 写得对不对即可，不必默写

> 曾经误解过一次：把整个清单都降级为"看懂即可"。**Python 基础必须能独立写。**

## 三、协作方式

- **代码由 Nova（AI）写**，但 Python 基础练习 Ember 要自己动手
- 解释代码时讲清「这行在干什么、为什么这么写」
- 涉及「要学什么」的清单，按【会写 / 能改 / 认得】分档
- Ember 偏好务实路线：**先让代码跑起来，遇到不懂再回查**，不主张线性啃完再动手

## 四、长期目标

用 **Python + LangChain + LangGraph** 实现一个「**不良品根因追溯智能体**」（对标 AgentScope-java 版本）。

参考来源：
- Pi Agent（TypeScript）的架构设计 —— 笔记在旧工作区 `WorkBuddyWorkSpace\Python相关学习\pi-agent-architecture-notes.md`
- 项目分层建议：`llm/`（模型封装）/ `agent/`（LangGraph 图）/ `app/`（API / CLI / UI）
- 原则：**循环要极简，工具要丰富**

## 五、当前阶段

**正在补 Python 基础**，尚未进入 LangChain / LangGraph。

学习清单：`docs/studyPlan/README.md`，配套练习：`docs/studyPlan/module-*-exercises.md`

- 8 个模块：A 语言基础 / B 工程环境 / C 面向对象 / D 类型系统与 Pydantic / E 错误处理与调试 / F 异步与流式 / G 装饰器 / H 工程化配套
- 三档：【会写】【能改】【认得】；模块 A–G 的标准是**会写**
- 净学习约 24 小时，推荐每天 2 小时 × 约 12 天
- 最短路径约 13 小时（模块 A + B + C + D1）

### 进度

| 模块 | 状态 | 说明 |
|---|---|---|
| A 语言基础 | **已完成**（2026-10-14） | 自建 13 个基础训练 + 完成 9 道综合题 |
| B 工程环境 | **基本完成**（2026-10-15） | 已实操 venv / dotenv / config.py / 跨文件 import |
| C 面向对象 | 已出练习（2026-10-15），进行中 | `docs/studyPlan/module-c-exercises.md` |
| D–H | 未开始 | |

**下一步**：Ember 做完模块 B 后出模块 C（面向对象）。学完 A–D 后进入 LangChain 核心概念，再到 LangGraph（那阶段标准为「看懂即可」）。

### 已知习惯

- Ember 自己的练习目录/文件用**中文命名**（如 `基础训练`、`模块联系题`），这是他的学习目录，不必纠正
- 他练得比要求更全（模块 A 自主加了 13 个知识点专项训练）

## 六、目录结构

```
Python学习/
├── .idea/                  # PyCharm 项目配置
├── .workbuddy-ai/
│   └── memory/             # 项目记忆
│       └── MEMORY.md       # 本文件
├── docs/
│   └── studyPlan/          # 学习文档
│       ├── README.md                  # Python 基础清单（定稿）
│       ├── module-a-exercises.md      # 模块 A 练习
│       ├── module-b-exercises.md      # 模块 B 练习
│       └── module-c-exercises.md      # 模块 C 练习
├── practice/               # 练习代码，按模块分
│   ├── README.md
│   ├── module_a_language_basics/      # Ember 已建 基础训练/ + 模块联系题/
│   ├── module_b_environment/
│   ├── module_c_oop/
│   ├── module_d_typing_pydantic/
│   ├── module_e_errors/
│   ├── module_f_async/
│   ├── module_g_decorators/
│   └── module_h_engineering/
├── playground/             # 随手试验，不归档
└── main.py                 # PyCharm 默认模板，待替换
```

未来会加 `agent/`：`llm/`（模型封装）、`graph/`（LangGraph 图）、`tools/`（领域工具）、`app/`（API/CLI/UI）。**现在不建**，避免过早复杂化。

## 七、约定

- **命名规范**：文件夹与文件一律用**事件英文名**，不要用日期（如 `phone-usb-mtp-fix`）
- **`docs/studyPlan/README.md` 已定稿，不要擅自修改**（Ember 明确要求）。新增学习材料另建文件。
- 涉及破坏性操作（删除、批量移动）前必须先确认
- 沙箱限制：无法调用 `wsl.exe` / `docker.exe` / `whoami.exe` 等原生 exe；`pip install` 需装在隔离环境里
- 沙箱限制：**无法完成需要交互认证的操作**（如 `git push` 到 GitHub），这类操作需 Ember 手动执行

---

## 八、Git 仓库

| 项 | 内容 |
|---|---|
| 远程地址 | `https://github.com/yangzhi-dl/python_study.git` |
| 分支 | `main` |
| 首次提交 | `e67becd chore: 初始化 Python 学习项目`（39 文件，3096 行） |
| 推送状态 | **已提交到本地，尚未推送到 GitHub** |

**未推送原因**：沙箱无法交互输入 GitHub 凭证（`fatal: could not read Username`）。

**Ember 需执行**：

```bash
cd C:\Users\Yandel\Desktop\Python学习
git push -u origin main
```

或直接在 PyCharm 里点推送（会走 Git Credential Manager 弹登录窗口）。
GitHub 已不支持密码认证，需用 **PAT（Personal Access Token）**，用户名填 `yangzhi-dl`，密码填 token。

### .gitignore 要点

- **忽略**：`.venv/`、`venv/`、`.env`（含 `.env.*`，但保留 `.env.example`）、`__pycache__/`、`.idea/`、`*.log`、数据与模型文件（`*.db` `*.pkl` `*.pt` `data/` `models/`）
- **会提交**：`.workbuddy-ai/`（含学习进度记录）、`docs/`、`practice/`、`main.py`
- `.gitattributes` 统一换行符为 LF
- 空目录用 `.gitkeep` 保留

### 已配置的全局 git 便利项

- `core.quotepath false` —— 中文文件名正常显示（不再显示八进制转义）
- `init.defaultBranch main` —— 新建仓库默认 main 分支
- `push.autoSetupRemote true` —— 首次推送不用加 `-u`
- `pull.rebase false` —— 消除 pull 警告
