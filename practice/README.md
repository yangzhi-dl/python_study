# 练习代码目录

按学习模块分目录，与 `docs/studyPlan/README.md` 的模块划分**一一对应**。

---

## 目录对照

| 目录 | 对应模块 | 放什么 |
|---|---|---|
| `module_a_language_basics/` | 模块 A · 语言基础 | 9 道练习 + 自己加的变体 |
| `module_b_environment/` | 模块 B · 工程与运行环境 | 子项目（验证 venv / import / .env） |
| `module_c_oop/` | 模块 C · 面向对象 | 类的定义、继承练习 |
| `module_d_typing_pydantic/` | 模块 D · 类型系统与 Pydantic | TypedDict、Pydantic 模型 |
| `module_e_errors/` | 模块 E · 错误处理与调试 | 故意写错的代码 + 报错分析 |
| `module_f_async/` | 模块 F · 异步与流式 | async/await、生成器 |
| `module_g_decorators/` | 模块 G · 装饰器 | 自己写的装饰器 |
| `module_h_engineering/` | 模块 H · 工程化配套 | 按需，可能一直空着 |

另有 `../playground/` —— 随手试验的地方，不归档、不整理。

---

## 命名约定

- 练习文件用 **`ex01_xxx.py`**、**`ex02_xxx.py`** 前缀，保证按顺序排列
- 每个模块目录可以放一个 **`notes.md`**，记录这个模块踩过的坑
- 变量名、函数名用英文，不要拼音

---

## 三条规矩

1. **每个练习脚本必须能独立运行**（`python ex01_xxx.py`），不要互相 import。
   原因：练习是碎片的，一旦互相依赖，改一个就会连环崩。

2. **一个知识点一个文件**。
   不要在 `ex01.py` 里塞 8 个练习 —— 出错了你不知道是哪段的问题。

3. **写不出就空着，别抄答案**。
   卡住的题在文件名后面加 `_todo`（如 `ex06_kwargs_todo.py`），学完模块 A 再回头补。

---

## 关于模块 B 的特殊说明

模块 B（工程与运行环境）需要**跨文件 import**，所以它下面要单独建一个子项目：

```
module_b_environment/
└── mini_project/
    ├── .env              # 存假 API Key（不要提交真实 Key）
    ├── .venv/            # 这个子项目自己的虚拟环境
    ├── config.py         # 读 .env
    ├── utils.py          # 一个工具函数
    └── main.py           # import config 和 utils，跑通
```

这样你才能真正体验"虚拟环境 + 模块导入 + 环境变量"三件事怎么配合。

---

## 以后会加什么

学完模块 A–G 后，会建一个 `agent/` 目录放最终的 Agent 项目：

```
agent/
├── llm/        # 模型封装（换模型只改这里）
├── graph/      # LangGraph 图，追溯逻辑
├── tools/      # 领域工具集（查工单、查质检、查 BOM…）
└── app/        # API / CLI / UI
```

**现在不建** —— 避免过早复杂化。练习代码和最终项目严格分开，这是刻意的。
