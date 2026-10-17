#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 21:35
@Desc    : 用 TypedDict 描述消息字典的结构，然后改掉练习 1 里那个 list[dict] 的模糊标注。
class MessageDict(TypedDict):
    role: str
    content: str
改完后，build_context(messages: list[MessageDict], ...)。
关键体验：在 PyCharm 里敲 messages[0][" 的时候，会不会自动提示 role 和 content？
考察：TypedDict 为什么重要：dict 是"什么键都行"，TypedDict 是"只有这几个键"——PyCharm 能据此做补全和检查
"""
from typing import TypedDict

# 定义消息字典的结构
class MessageDict(TypedDict):
    role: str
    content: str

messages = [
    {"role": "system", "content": "你是不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良"},
    {"role": "assistant", "content": "我先查一下工单记录"},
    {"role": "user", "content": "3号产线昨天有5个批次不良222"},
    {"role": "assistant", "content": "好的，我会尽快处理"}
]
# 构建上下文
def build_context(messages: list[MessageDict],max_count: int) -> str:
    recent = messages[-max_count:] #取倒数的max_count个消息，顺序的
    recent.reverse() # 逆序排列
    lines = []
    for m in recent:
        lines.append(f"{m['role']}:{m['content']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(build_context(messages, 3))
