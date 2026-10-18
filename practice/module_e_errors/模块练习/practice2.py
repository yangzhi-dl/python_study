#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/18 20:19
@Desc    :  Agent 里面的四个真是场景
"""
import json
import re, time

def safe_execute_tool(tool_func, args: dict) -> str:
    """场景 1 · 工具执行失败，不能让整个 Agent 崩
    问题：LLM 决定调用某个工具，但工具执行时抛异常了。如果直接往外抛，整个 Agent 就挂了。
    正确做法：把错误信息返回给 LLM，让它自己决定怎么办。

    执行工具，失败时把错误信息变成字符串返回

    关键理解：在 Agent 里，错误不是终点，是给模型的一条信息。模型看到"参数错误"可能会改参数重试。
    """
    try:
        result = tool_func(**args)
        return str(result)
    except TypeError as e:
        return f"[工具参数错误] {e}"
    except Exception as e:
        return f"[工具执行失败] {type(e).__name__}: {e}"


def parse_json_safely(text: str) -> dict:
    """场景 2 · LLM 返回的 JSON 解析失败
    问题：你让 LLM 输出 JSON，它有时候会包在 ` ```json ` 代码块里，有时候会多说一句话。


    尽最大努力从 LLM 输出里解析出 JSON
    这个模式在 Agent 开发里极其常见，建议直接收藏。
    """
    # 先直接试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 再试着从 ```json ... ``` 代码块里提取
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 都不行，抛出带原文的错误，方便排查
    raise ValueError(f"无法从以下内容解析出 JSON:\n{text}")


def call_with_retry(func, max_retries: int = 3):
    """场景 3 · API 调用重试
    **问题**：网络抖动、限流，第一次调用失败很正常。

**关键点**：`2 ** attempt` 叫**指数退避**（1、2、4 秒），避免短时间内反复冲击服务端。

    失败后重试，每次等待时间翻倍"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise                       # 最后一次还失败，往外抛
            wait = 2 ** attempt              # 1s, 2s, 4s
            print(f"第 {attempt + 1} 次失败: {e}，{wait} 秒后重试")
            time.sleep(wait)


def trim_messages(messages: list, max_count: int = 20) -> list:
    """场景 4 · 上下文超长
    **问题**：消息越攒越多，超过模型的上下文窗口，API 直接报错。

    **这就是 Pi Agent 里"上下文压缩"的最简版本** —— 保留 system 提示，砍掉旧对话。

    裁剪消息，但保留 system 消息"""
    if len(messages) <= max_count:
        return messages

    system_msgs = [m for m in messages if m.get("role") == "system"]
    other_msgs = [m for m in messages if m.get("role") != "system"]

    # system 保留，其余只留最近的
    return system_msgs + other_msgs[-(max_count - len(system_msgs)):]

