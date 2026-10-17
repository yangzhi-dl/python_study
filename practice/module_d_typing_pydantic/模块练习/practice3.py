#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 21:35
@Desc    : 定义一个类型 Role，只能是 "system"、"user"、"assistant" 三个值之一。

然后用它写一个函数 filter_by_role(messages, role)，只返回指定 role 的消息。
user_msgs = filter_by_role(messages, "user")    # ✅
bad = filter_by_role(messages, "boss")          # ⚠️ 类型检查器会警告
考察：Literal —— 把取值限定在几个常量里 为什么需要：比 str 精确得多，能防止传错值
"""
from typing_extensions import Literal

Role = Literal["system", "user", "assistant"]
messages = [
    {"role": "system", "content": "你是不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良"},
    {"role": "assistant", "content": "我先查一下工单记录"},
    {"role": "user", "content": "3号产线昨天有5个批次不良222"},
    {"role": "assistant", "content": "好的，我会尽快处理"}
]

def filter_by_role(messages: list[dict], role: Role) -> list[dict]:
    return [m for m in messages if m["role"] == role]

if __name__ == "__main__":
    print(filter_by_role(messages, "user"))#打出所有的
    print(filter_by_role(messages, "assistant"))#输出空[]
