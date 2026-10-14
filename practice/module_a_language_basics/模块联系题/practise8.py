#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practise1.py
@Author  : yz.yangzhi
@Date    : 2026/10/14 21:15
@Desc    :用**一行**代码，把 messages 拆成 `first`（第一条）和 `rest`（剩下所有）。
> 考察：解包赋值
"""

messages = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良，帮我查原因"},
    {"role": "assistant", "content": "好的，我先查一下3号产线的工单记录"},
    {"role": "user", "content": "重点是昨天下午那批"},
    {"role": "assistant", "content": "已找到，下午2点到5点有3个批次异常"},
]

print("messages:",messages,"\n")

first, *rest = messages
print(first)
print(rest)