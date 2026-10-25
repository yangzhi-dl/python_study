# 模块 H 练习 —— 工程化配套

> **配套文档**：`README.md` 模块 H（工程化配套）
> **重要说明**：**这模块是"按需"**。模块 A–G 学完就能进 LangChain 了，这里的内容是"要测试 / 要上线"时才需要。
> **目标**：能看懂、能改、能跑起来，不要求默写

---

## 什么时候需要这模块

| 场景 | 需要学哪部分 |
|---|---|
| 只在本机跑脚本 | **整个模块可以跳过** |
| 想给函数写测试 | Part 2（pytest） |
| 想把 Agent 暴露成 HTTP 接口给前端调 | Part 3（FastAPI） |
| 代码要给别人看 / 长期维护 | Part 1（配置分层）+ Part 4（工具链） |

---

# Part 1 · 配置分层（能改）

## 1.1 问题

开发时用测试 Key、调试模式；上线时用生产 Key、关掉调试。**同一份代码，两套配置。**

**笨办法**：每次手动改 `.env`。容易忘，也容易把生产 Key 提交上去。

## 1.2 正确做法：按环境分文件

```
mini_project/
├── .env.dev          # 开发环境
├── .env.prod         # 生产环境
├── .env.example      # 模板（提交到 git）
└── config.py
```

`.env.dev`：

```
API_KEY=sk-test-1234567890
MODEL_NAME=gpt-4
DEBUG=true
```

`.env.prod`：

```
API_KEY=sk-prod-xxxxxxxxxx
MODEL_NAME=gpt-4o
DEBUG=false
```

## 1.3 config.py 怎么读

```python
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent

# 从环境变量读当前环境，默认 dev
ENV = os.getenv("APP_ENV", "dev")

# 优先加载 .env.{ENV}，没有就退回 .env
env_file = BASE_DIR / f".env.{ENV}"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv(BASE_DIR / ".env")

API_KEY: str = os.getenv("API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


if __name__ == "__main__":
    print(f"环境: {ENV}")
    print(f"模型: {MODEL_NAME}")
    print(f"调试模式: {DEBUG}")
```

## 1.4 怎么切换环境

```bash
# Git Bash / Linux
APP_ENV=prod python main.py

# PowerShell
$env:APP_ENV="prod"; python main.py

# CMD
set APP_ENV=prod && python main.py
```

## 1.5 `.gitignore` 要覆盖到

```gitignore
.env
.env.*
!.env.example
```

> `.env.*` 会匹配 `.env.dev` / `.env.prod`，但 `!.env.example` 把模板放出来——**模板要提交，真实值不能提交**。

## 1.6 一个坑：`DEBUG` 为什么这么判断

```python
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

**不能这么写**：

```python
DEBUG = bool(os.getenv("DEBUG", "false"))     # ❌ 永远是 True
```

因为 `bool("false")` 是 `True`——**非空字符串都是 True**。

必须显式比较字符串。这是环境变量的通用坑。

---

# Part 2 · pytest（能改）

## 2.1 为什么不用 `if __name__ == "__main__"` 自测

`if` 里写 `print` 自测，有三个问题：

1. **要人眼看**——`print` 出来一堆，得自己判断对不对
2. **不自动**——每改一次代码，要手动跑一遍
3. **不能批量**——10 个函数要跑 10 次

pytest 解决这三个问题：**自动断言、一次跑全部、失败自动报错**。

## 2.2 装

```bash
pip install pytest
```

## 2.3 目录约定

```
mini_project/
├── utils.py
└── tests/
    └── test_utils.py       # 文件名必须 test_ 开头
```

**两条命名规则**（pytest 靠这个找测试）：
- 文件：`test_*.py` 或 `*_test.py`
- 函数：`test_` 开头

## 2.4 第一个测试

`utils.py`：

```python
def build_context(messages: list[dict], max_count: int = 3) -> str:
    recent = messages[-max_count:]
    lines = []
    for m in recent:
        lines.append(f'{m["role"]}: {m["content"]}')
    return "\n".join(lines)
```

`tests/test_utils.py`：

```python
from utils import build_context


def test_basic():
    messages = [{"role": "user", "content": "你好"}]
    assert build_context(messages) == "user: 你好"


def test_max_count():
    messages = [
        {"role": "user", "content": "第一条"},
        {"role": "assistant", "content": "第二条"},
        {"role": "user", "content": "第三条"},
    ]
    result = build_context(messages, max_count=2)
    assert "第一条" not in result
    assert "第三条" in result


def test_empty():
    assert build_context([]) == ""
```

## 2.5 跑

```bash
pytest                    # 跑所有测试
pytest -v                 # 显示每个测试的名字
pytest tests/test_utils.py::test_basic    # 只跑一个
```

**输出示例**：

```
============================= test session starts =============================
collected 3 items

tests/test_utils.py::test_basic PASSED                                   [ 33%]
tests/test_utils.py::test_max_count PASSED                               [ 66%]
tests/test_utils.py::test_empty PASSED                                   [100%]

============================== 3 passed in 0.02s ==============================
```

**失败时**会明确告诉你是哪个断言、期望什么、实际什么：

```
E       assert '第一条' not in 'user: 第一条\n...'
```

## 2.6 `assert` 是什么

```python
assert 条件, "失败时的提示"
```

- 条件为真 → 什么也不发生，继续
- 条件为假 → 抛 `AssertionError`，pytest 标记为失败

**和 Java 对照**：

```java
assertEquals("user: 你好", buildContext(messages));   // JUnit
```

```python
assert build_context(messages) == "user: 你好"        # pytest
```

**pytest 更简洁**——直接写 `assert`，不需要记一堆 `assertEquals` / `assertTrue` / `assertNotNull`。

## 2.7 fixture（简单提一句）

多个测试都要用的准备数据，用 `@pytest.fixture`：

```python
import pytest


@pytest.fixture
def sample_messages():
    return [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
    ]


def test_something(sample_messages):      # ← 参数名就是 fixture 名
    assert len(sample_messages) == 2
```

**类似 JUnit 的 `@BeforeEach`**，但更灵活（按需注入）。

---

# Part 3 · FastAPI（认得）

## 3.1 什么时候需要

你的 Agent 现在只能在本机跑（`python main.py`）。

如果**前端要调用**、**其他系统要集成**，就需要一个 HTTP 接口。FastAPI 是 Python 里最流行的选择。

## 3.2 装

```bash
pip install fastapi uvicorn
```

- `fastapi` —— 框架本体
- `uvicorn` —— 跑服务的服务器

## 3.3 最小完整例子

`api.py`：

```python
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="不良品根因追溯 API")


# ① 定义请求体（用模块 D 学的 Pydantic）
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


# ② 定义响应体
class ChatResponse(BaseModel):
    reply: str
    session_id: str


# ③ 健康检查（部署时运维会调这个）
@app.get("/health")
async def health():
    return {"status": "ok"}


# ④ 主接口
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # 真实场景里，这里调用你的 Agent
    reply = f"[模拟] 收到问题: {req.message}"
    return ChatResponse(reply=reply, session_id=req.session_id)
```

## 3.4 跑起来

```bash
uvicorn api:app --reload
```

- `api` —— 文件名（`api.py`，不带 `.py`）
- `app` —— 文件里那个 `FastAPI()` 实例的名字
- `--reload` —— 改代码自动重启（开发时用，生产别加）

**访问**：`http://127.0.0.1:8000`

## 3.5 两个免费的好东西

**① 自动生成的接口文档**

打开 `http://127.0.0.1:8000/docs`，会看到一个可以**直接在网页上点按钮测试**的界面。

这是 FastAPI 最大的优势——**你不需要写文档，它根据类型注解自动生成**。

**② 自动参数校验**

因为用了 Pydantic，如果请求体少字段、类型不对，FastAPI 会**自动返回 422 错误并说明哪里错了**，不用你写校验代码。

```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 3.6 和 Agent 结合的关键点

```python
@app.post("/chat")
async def chat(req: ChatRequest):
    # 关键：Agent 的调用也要用 await（因为它是 IO 密集型）
    result = await agent.ainvoke({"messages": [("user", req.message)]})
    return ChatResponse(reply=result["messages"][-1].content)
```

**为什么必须用 `ainvoke` 而不是 `invoke`？**

因为 FastAPI 的路由是 `async def`，**在里面调同步的 `invoke` 会阻塞整个事件循环**——所有请求都会排队等待。

这就是模块 F 说的坑 2：**async 函数里不能有阻塞调用**。

---

# Part 4 · 工具链（认得）

## 4.1 ruff —— 格式化 + 检查（推荐）

```bash
pip install ruff

ruff check .            # 检查问题（不修改）
ruff check . --fix      # 自动修能修的
ruff format .           # 格式化代码
```

**它同时干了 flake8 + isort + black 的活**，而且极快（Rust 写的）。**新项目首选。**

## 4.2 black —— 纯格式化

```bash
pip install black
black .
```

**特点：完全不给你配置选项**——"代码长什么样由我决定，你别争"。团队协作时能消除格式争论。

## 4.3 mypy / pyright —— 类型检查

```bash
pip install mypy
mypy main.py
```

**它做什么**：检查你写的类型注解有没有矛盾。

```python
def add(a: int, b: int) -> int:
    return a + b


add("1", "2")       # mypy 会报错：Argument 1 has incompatible type "str"
```

**注意**：Python 运行时**不会**检查类型注解（模块 D 说过），**只有 mypy / pyright 这类工具才会**。

- `mypy` —— 老牌，配置多
- `pyright` —— 微软出品，更快，VS Code 内置
- PyCharm 自带的检查也做类似的事

## 4.4 建议

学习阶段**不用管这些**。等你开始写正式项目、要给别人看代码时，装个 ruff 就够了。

---

# 练习

## 练习 1 · 配置分层

给 `mini_project` 加上环境切换：

1. 建 `.env.dev` 和 `.env.prod`
2. 改 `config.py` 支持 `APP_ENV` 切换
3. 验证：`APP_ENV=prod python config.py` 能读到生产配置

> 考察：`os.getenv`、`Path`、条件加载

## 练习 2 · 写测试

给 `build_context` 写 3 个测试：

1. 正常情况：能正确拼接
2. `max_count` 生效：只取最后 N 条
3. 空列表：返回空字符串

跑 `pytest -v`，确保 3 个都 PASSED。

> 考察：pytest 命名约定、`assert`

## 练习 3 · 包成 API

写一个 `api.py`，提供两个接口：

- `GET /health` → 返回 `{"status": "ok"}`
- `POST /chat` → 接收 `{"message": "..."}`，返回 `{"reply": "..."}`

跑起来，用浏览器打开 `/docs` 测试。

> 考察：FastAPI 基本用法、Pydantic 请求体

## 练习 4 · 跑工具链

```bash
ruff check .
ruff format .
```

看看它改了哪些地方。（如果没装 ruff，这题可以跳过）

---

## 过关标准

| 部分 | 标准 |
|---|---|
| Part 1 · 配置分层 | 能改、能切换环境 |
| Part 2 · pytest | **能写出 3 个测试并跑通** |
| Part 3 · FastAPI | 能跑起来、能打开 `/docs` |
| Part 4 · 工具链 | 认得即可 |

**这模块不追求精通**。会用 pytest 写几个测试、能把 Agent 包成一个接口，就够开始了。

---

## 参考答案

> **先自己写完再看。**

<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

### 练习 1

`.env.dev`：

```
API_KEY=sk-test-dev
MODEL_NAME=gpt-4
DEBUG=true
```

`.env.prod`：

```
API_KEY=sk-prod-real
MODEL_NAME=gpt-4o
DEBUG=false
```

`config.py`：

```python
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
ENV = os.getenv("APP_ENV", "dev")

env_file = BASE_DIR / f".env.{ENV}"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv(BASE_DIR / ".env")

API_KEY: str = os.getenv("API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


if __name__ == "__main__":
    print(f"环境: {ENV}")
    print(f"模型: {MODEL_NAME}")
    print(f"调试: {DEBUG}")
    print(f"Key 前缀: {API_KEY[:10]}...")
```

验证：

```bash
python config.py                  # 环境: dev
APP_ENV=prod python config.py     # 环境: prod
```

### 练习 2

`tests/test_utils.py`：

```python
from utils import build_context


def test_normal():
    messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
    ]
    result = build_context(messages)
    assert "system: 你是助手" in result
    assert "user: 你好" in result


def test_max_count():
    messages = [
        {"role": "user", "content": "第一条"},
        {"role": "assistant", "content": "第二条"},
        {"role": "user", "content": "第三条"},
    ]
    result = build_context(messages, max_count=2)
    assert "第一条" not in result
    assert "第二条" in result
    assert "第三条" in result


def test_empty():
    assert build_context([]) == ""
```

跑：

```bash
pytest -v
```

### 练习 3

`api.py`：

```python
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="不良品根因追溯 API")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    reply = f"[模拟] 收到问题: {req.message}"
    return ChatResponse(reply=reply, session_id=req.session_id)
```

跑：

```bash
uvicorn api:app --reload
```

然后打开 `http://127.0.0.1:8000/docs`，点 `/chat` → `Try it out` → 填入：

```json
{"message": "3号产线为什么不良？"}
```

点 `Execute` 就能看到返回。

### 练习 4

```bash
ruff check .
```

典型输出：

```
main.py:5:1: F401 [*] `os` imported but unused
Found 1 error.
[*] 1 fixable with the `--fix` option.
```

```bash
ruff check . --fix     # 自动删掉没用的 import
ruff format .          # 统一格式（引号、缩进、换行）
```

---

## 到这里，基础部分全部结束

**A → B → C → D → E → F → G** 是主线，**H 是按需**。

**下一步就是 LangChain / LangGraph**——从这一阶段开始，标准从「会写」放宽为「看懂即可」，因为你是在用它们的 API，不是实现它们。

---

## 最后：整个清单的自检

如果下面这些都能做到，说明基础扎实了：

| 模块 | 自检 |
|---|---|
| A | 不看资料能写处理 `list[dict]` 的函数 |
| B | 能独立建项目、装依赖、读 `.env` |
| C | 能写类、继承、用 `@dataclass` |
| D | 能写 `TypedDict` + Pydantic 模型，能解释 `Annotated` |
| E | 能读懂 traceback 并定位问题 |
| F | 能写 `async def` + `async for` 的流式输出 |
| G | 能写带 `*args, **kwargs` 的装饰器，能解释 `@tool` |
| H | 能写 pytest 测试、能包一个 FastAPI 接口 |

**全部打勾，可以开始了。**
