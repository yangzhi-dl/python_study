#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 21:35
@Desc    : 写一个函数 find_message(messages, role)：在消息列表里找第一条指定 role 的消息，找到就返回它，找不到返回 None。
msg = find_message(messages, "user")
if msg is not None:
    print(msg["content"])

请用两种写法各写一遍：
Optional[dict]
dict | None
考察：Optional[X] 和 X | None 两种写法完全等价，| 是 Python 3.10+ 的新语法，更简洁
"""
def find_message(messages:list[dict], role:str) -> dict | None:
    for message in messages:
        if message["role"] == role:
            return message
    return None


if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "你是不良品根因分析助手"},
        {"role": "user", "content": "3号产线昨天有5个批次不良"},
        {"role": "assistant", "content": "我先查一下工单记录"},
        {"role": "user", "content": "3号产线昨天有5个批次不良222"},
        {"role": "assistant", "content": "好的，我会尽快处理"}
    ]
    msg = find_message(messages, "user") # 找到指定 role 的消息
    if msg is not None:
        print(msg["content"])
