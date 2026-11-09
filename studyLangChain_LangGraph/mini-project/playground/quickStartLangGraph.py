"""LangGraph 官方 Quickstart 本地化版本（计算器 Agent）

【跑这个能看到什么】
用 LangGraph 搭一个"会算数"的 Agent：模型自己决定调 add / multiply / divide，
拿到结果后继续推理，直到给出最终答案。跑完会打印：

  1. 图的 Mermaid 结构（节点和边长什么样）
  2. 完整消息流水（Human → AI 工具调用 → Tool 结果 → AI 最终回答）
  3. 状态里的 llm_calls 计数（模型被调了几轮）

【怎么跑】
    cd studyLangChain_LangGraph/mini-project
    .venv/Scripts/python.exe playground/quickStartLangGraph.py

【和官方文档的差异】
官方用 claude-sonnet-4-6 + ANTHROPIC_API_KEY；
这里换成项目 .env 里的百炼实例（MODEL_CODE / DASHSCOPE_API_KEY / BASE_URL）。
其余步骤、节点名、边的连法和官方完全一致。
"""

import operator
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from typing_extensions import Annotated, TypedDict

from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langgraph.graph import END, START, StateGraph


# ============================================================
# 零、环境：读本地 .env，不用 init_chat_model 的自动读环境变量
# ============================================================

ENV_PATH: Path = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL: str = os.getenv("BASE_URL", "")
MODEL_CODE: str = os.getenv("MODEL_CODE", "")

if not API_KEY:
    raise SystemExit(f"没有读到 DASHSCOPE_API_KEY，检查 {ENV_PATH}")
if not MODEL_CODE:
    raise SystemExit(f"没有读到 MODEL_CODE，检查 {ENV_PATH}")

# init_chat_model 的 model_provider="openai" 表示走 OpenAI 兼容协议；
# base_url 指到百炼网关，api_key 显式传，避免它去读 OPENAI_API_KEY。
model_kwargs: dict = {
    "model": MODEL_CODE,
    "model_provider": "openai",
    "temperature": 0,
    "api_key": API_KEY,
}
if BASE_URL:
    model_kwargs["base_url"] = BASE_URL

model = init_chat_model(**model_kwargs)


# ============================================================
# 一、定义工具
# ============================================================

@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


TOOLS: list = [add, multiply, divide]

# name -> 工具对象。工具节点靠这张表按名字找到要执行的函数
TOOLS_BY_NAME: dict = {t.name: t for t in TOOLS}

# 把工具注册给模型：模型从此能"提议"调哪个工具
MODEL_WITH_TOOLS = model.bind_tools(TOOLS)#模型能调用哪些工具


# ============================================================
# 二、定义状态
#
# messages 用 Annotated[list, operator.add]：节点返回的新消息是【追加】，
# 不是覆盖。少了这个 reducer，后一轮会把前面所有消息冲掉。
# ============================================================

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add] # 这里取消了默认的reducer,通过operator.add显式指定add追加方式
    llm_calls: int


# ============================================================
# 三、模型节点：调 LLM，判断要不要调工具
# ============================================================

def llm_call(state: AgentState) -> dict:
    """调一次模型，返回一条 AIMessage，并把 llm_calls 加 1。"""

    response: AnyMessage = MODEL_WITH_TOOLS.invoke(
        [SystemMessage(content="You are a helpful assistant tasked with performing arithmetic on a set of inputs.")]
        + state["messages"]
    )

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ============================================================
# 四、工具节点：执行模型请求的所有工具调用
# ============================================================

def tool_node(state: AgentState) -> dict:
    """遍历上一条 AIMessage 里的 tool_calls，逐个执行，返回 ToolMessage 列表。"""

    last_message: AnyMessage = state["messages"][-1]
    result: list[ToolMessage] = []

    for tool_call in last_message.tool_calls:
        tool_obj = TOOLS_BY_NAME[tool_call["name"]]
        observation = tool_obj.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))

    return {"messages": result}


# ============================================================
# 五、条件边：决定回工具节点还是结束
# ============================================================

def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    """上一条消息有 tool_calls → 去工具节点；没有 → 结束。"""

    last_message: AnyMessage = state["messages"][-1]

    if last_message.tool_calls:
        return "tool_node"
    return END


# ============================================================
# 六、建图并编译
# ============================================================

agent_builder: StateGraph = StateGraph(AgentState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

agent = agent_builder.compile()


# ============================================================
# 七、运行
# ============================================================

def show_graph() -> None:
    """打印图结构。不用 draw_mermaid_png，避免依赖网络和 pygraphviz。"""
    print("=" * 72)
    print("图结构")
    print("=" * 72)
    print(agent.get_graph(xray=True).draw_mermaid())
    print()


def run(question: str) -> None:
    print("=" * 72)
    print(f"提问：{question}")
    print("=" * 72)

    final_state: dict = agent.invoke({"messages": [HumanMessage(content=question)]})

    for msg in final_state["messages"]:
        msg.pretty_print()

    print()
    print(f"llm_calls = {final_state['llm_calls']}")
    print(f"消息条数   = {len(final_state['messages'])}")


def main() -> None:
    show_graph()
    run("Add 3 and 4.")
    print()
    run("What is (3 + 5) * 12 divided by 2?")


if __name__ == "__main__":
    main()
