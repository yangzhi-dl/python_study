#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practise1.py
@Author  : yz.yangzhi
@Date    : 2026/10/14 21:15
@Desc    :写一个函数 `apply_to_messages(func, messages)`，把 `func` 应用到每条消息上，返回新列表。
然后传一个 `lambda m: m["content"]` 进去，打印结果。
> 考察：函数作为参数传递
> **为什么重要**：`builder.add_node("agent", call_model)` 之所以成立，就是因为函数能当参数传
"""

messages = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良，帮我查原因"},
    {"role": "assistant", "content": "好的，我先查一下3号产线的工单记录"},
    {"role": "user", "content": "重点是昨天下午那批"},
    {"role": "assistant", "content": "已找到，下午2点到5点有3个批次异常"},
]

print(messages)

def apply_to_messages(func,messages):
    return [func(m) for m in messages]

contents = apply_to_messages(lambda m:m["content"],messages)
print(contents)