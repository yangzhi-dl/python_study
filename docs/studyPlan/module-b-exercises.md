# 模块 B 练习 —— 从零搭一个迷你项目

> **配套文档**：`README.md` 模块 B（工程与运行环境）
> **和模块 A 的区别**：A 是知识点（一道题一个语法），B 是**流程**（一件事串起多个工具）。
> 所以这里不是 9 道题，是 **7 个任务**，按顺序做，每个任务都有验证方法。

---

## 目标

在 `practice/module_b_environment/mini_project/` 下，从零搭一个小项目，跑通这条链：

```
建虚拟环境 → 装依赖 → 读环境变量 → 跨文件 import → 读本地文件 → 跑通
```

这条链就是**每个 Python 项目启动时的全部准备工作**。学完这个，你以后看任何项目的目录结构都能秒懂。

---

## 最终目录结构

```
mini_project/
├── .venv/                  # 虚拟环境（自动生成，不用管）
├── .env                    # 环境变量（真实值，不提交）
├── .env.example            # 环境变量模板（提交给别人看）
├── .gitignore              # Git 忽略清单
├── requirements.txt        # 依赖清单
├── config.py               # 读 .env
├── utils.py                # 工具函数
├── main.py                 # 入口
└── prompts/
    └── system.txt          # 提示词文件
```

> 目录名用英文 —— 真实项目一律英文，现在养成习惯。

---

## 任务 1 · 建虚拟环境

**为什么要建**：每个项目一个独立环境，A 项目装的包不会污染 B 项目。你在 PyCharm 里看到自动建的那个 `venv` 就是这东西，只是之前不用你操心。

```bash
cd practice/module_b_environment/mini_project
python -m venv .venv
```

**激活**（看你的终端类型，选一个）：

```bash
# Git Bash
source .venv/Scripts/activate

# PowerShell
.venv\Scripts\Activate.ps1

# CMD
.venv\Scripts\activate.bat
```

> PowerShell 如果报"禁止运行脚本"，用 CMD 或 Git Bash 就行。

**验证**：命令行前面出现 `(.venv)`，然后跑：

```bash
python -V          # 应该是 Python 3.10.x
pip list           # 只有 pip / setuptools，很干净
```

**记住这一步**：以后每建一个新项目，第一件事都是它。

---

## 任务 2 · 装依赖 + 记录

```bash
pip install python-dotenv
pip freeze > requirements.txt
```

**验证**：`requirements.txt` 里有 `python-dotenv==x.x.x`

**理解 `requirements.txt`**：它是"这个项目需要哪些包"的清单。换台机器，`pip install -r requirements.txt` 就能一键复现环境。

> 学习阶段用 `pip freeze` 就够（它会把所有包都写进去）。真实项目更规范的做法是手动维护，只写直接依赖。

---

## 任务 3 · 环境变量

**为什么要用**：API Key 这类敏感信息绝不能写死在代码里。写死了，代码一分享 Key 就泄露。

### 3.1 建 `.env`

```
API_KEY=sk-test-1234567890
MODEL_NAME=gpt-4
BASE_URL=https://api.example.com
```

### 3.2 建 `.env.example`

内容一样，但**值留空**：

```
API_KEY=
MODEL_NAME=
BASE_URL=
```

`.env.example` 是给别人的模板 —— 告诉他需要配哪些变量，但不泄露真实值。真实项目里 `.env` 不提交，`.env.example` 提交。

### 3.3 写 `config.py`

```python
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env（路径基于当前文件位置，避免换目录就失效）
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

API_KEY: str = os.getenv("API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4")
BASE_URL: str = os.getenv("BASE_URL", "")


if __name__ == "__main__":
    print(f"API_KEY = {API_KEY}")
    print(f"MODEL_NAME = {MODEL_NAME}")
    print(f"BASE_URL = {BASE_URL}")
```

**验证**：`python config.py` 能打印出 `.env` 里的值

**这 3 行代码里有 3 个知识点**：
- `os.getenv("X", 默认值)` —— 读环境变量，读不到就用默认值（所以 .env 丢了程序也不会崩）
- `Path(__file__).parent` —— 拿到当前文件所在目录（任务 6 详解）
- `load_dotenv()` —— 把 `.env` 的内容加载进环境变量

---

## 任务 4 · 跨文件 import

### 4.1 写 `utils.py`

```python
def build_context(messages: list[dict], max_count: int = 3) -> str:
    """把最近几条消息拼成一段文本。"""
    recent = messages[-max_count:]
    lines = []
    for m in recent:
        lines.append(f'{m["role"]}: {m["content"]}')
    return "\n".join(lines)


def count_by_role(messages: list[dict]) -> dict:
    """统计每种 role 出现多少次。"""
    counts: dict = {}
    for m in messages:
        role = m["role"]
        counts[role] = counts.get(role, 0) + 1
    return counts
```

### 4.2 写 `main.py`

```python
from config import MODEL_NAME
from utils import build_context, count_by_role

MESSAGES = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良"},
    {"role": "assistant", "content": "我先查一下工单记录"},
]

print(f"使用模型: {MODEL_NAME}")
print(count_by_role(MESSAGES))
print(build_context(MESSAGES))
```

**验证**：`python main.py` 跑通，打印出模型名、统计结果、拼接文本

**理解 import**：
- `from utils import build_context` —— 从 utils.py 里取一个函数
- **关键**：import 的时候，被导入的文件会**整个执行一遍**。这是任务 5 的核心。

---

## 任务 5 · `if __name__ == "__main__":`（重点）

这是模块 B 最需要真正理解的一个语法 —— 它看着莫名其妙，但每个项目都有。

### 5.1 在 `utils.py` 末尾加上

```python
if __name__ == "__main__":
    print(">>> utils.py 正在被直接运行")
    demo = [{"role": "user", "content": "测试"}]
    print(build_context(demo))
```

### 5.2 做对比实验

```bash
python utils.py      # 观察：">>> utils.py 正在被直接运行" 会不会打印？
python main.py       # 观察：同一行会不会打印？
```

### 5.3 再把 if 判断去掉，做第三次实验

```python
# 注释掉 if，让它无条件执行
print(">>> utils.py 正在被直接运行")
```

再跑 `python main.py` —— 看看这次发生了什么。

### 你应该观察到

| 运行方式 | 加了 if | 去掉 if |
|---|---|---|
| `python utils.py` | 打印 | 打印 |
| `python main.py` | **不打印** | **打印** |

### 结论

`__name__` 这个变量：
- 文件被**直接运行**时 → 等于 `"__main__"`
- 文件被 **import** 时 → 等于模块名（这里是 `"utils"`）

所以 `if __name__ == "__main__":` 的作用是：**这段代码只在直接运行本文件时执行，被别人 import 时不执行。**

**这就是为什么测试代码都放在这个 if 里面** —— 否则你 import 它的时候，测试代码会莫名其妙跟着跑一遍。

---

## 任务 6 · 路径处理

**为什么要学**：硬编码绝对路径 `C:\Users\Yandel\...` 换台机器就废，而且项目一移动就崩。

### 6.1 建 `prompts/system.txt`

```
你是一个不良品根因分析助手。
你的任务是：根据用户提供的产线、批次、时间范围，查询相关工单与质检记录，定位不良根因。
回答时要给出：可能的原因、支撑证据、建议的排查方向。
```

### 6.2 在 `utils.py` 顶部加 import，末尾加函数

```python
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """读取 prompts 目录下的提示词文件。"""
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"提示词文件不存在: {path}")
    return path.read_text(encoding="utf-8")
```

### 6.3 在 `main.py` 里调用

```python
from utils import load_prompt

print(load_prompt("system"))
```

### 验证（两步都要做）

1. **在项目目录下运行**：`python main.py` → 能读出文件内容
2. **换个目录运行**：

```bash
cd C:/Users/Yandel/Desktop
python "C:/Users/Yandel/Desktop/Python学习/practice/module_b_environment/mini_project/main.py"
```

**两次都要成功。** 如果你用了硬编码路径，第二次就会失败。

### 理解 `Path(__file__).parent`

| 部分 | 含义 |
|---|---|
| `__file__` | 当前这个文件自己的路径 |
| `.parent` | 取它所在的目录 |
| `Path(__file__).parent / "prompts"` | 拼出"和我同级的 prompts 目录" |

这样不管从哪个目录启动，都能定位到**文件旁边**的东西。

> 注意 `encoding="utf-8"` —— Windows 默认编码是 GBK，读中文文件不加这个会乱码。这个坑你一定会遇到。

---

## 任务 7 · 综合验收

把 `main.py` 换成完整版，把所有东西串起来：

```python
from config import API_KEY, MODEL_NAME
from utils import build_context, count_by_role, load_prompt

MESSAGES = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良"},
    {"role": "assistant", "content": "我先查一下工单记录"},
    {"role": "user", "content": "重点是昨天下午那批"},
]


def main() -> None:
    print("=" * 40)
    print(f"模型: {MODEL_NAME}")
    print(f"API Key 是否配置: {'是' if API_KEY else '否'}")
    print("=" * 40)

    print("\n[系统提示词]")
    print(load_prompt("system"))

    print("\n[消息统计]")
    print(count_by_role(MESSAGES))

    print("\n[上下文]")
    print(build_context(MESSAGES))


if __name__ == "__main__":
    main()
```

### 验收标准

- [ ] `python main.py` 一次跑通，无报错
- [ ] 从**任意目录**运行都能读到 `prompts/system.txt`
- [ ] 命令行前面有 `(.venv)`
- [ ] `requirements.txt` 存在且内容正确
- [ ] 删掉 `.env` 后重跑，程序**不崩溃**（因为 `os.getenv` 给了默认值）

---

## 最后一个动作 · 写 `.gitignore`

以后用 Git 的话，这些东西**绝对不能提交**：

```
.venv/
.env
__pycache__/
*.pyc
```

`.env` 里有真实 Key，`.venv` 有几百 MB。现在建好，以后省事。

---

## 过关标准

7 个任务全做完，并且能**用自己的话**回答这三个问题：

1. **为什么要建虚拟环境？** —— 不建会怎样？
2. **`if __name__ == "__main__":` 是干什么的？** —— 用你自己的话说
3. **为什么读文件要用 `Path(__file__).parent`，不直接写路径？**

答得出来 → 模块 B 通过，进模块 C（面向对象）。

---

## 附：这些命令你以后天天用

```bash
python -m venv .venv              # 建虚拟环境
source .venv/Scripts/activate     # 激活（Git Bash）
pip install 包名                   # 装包
pip freeze > requirements.txt     # 导出依赖
pip install -r requirements.txt   # 按清单装依赖
python 脚本.py                     # 跑脚本
deactivate                        # 退出虚拟环境
```
