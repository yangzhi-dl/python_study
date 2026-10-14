#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practise1.py
@Author  : yz.yangzhi
@Date    : 2026/10/14 21:15
@Desc    :写一个函数：
def summarize_messages(messages, max_count=3, include_system=False):

```
要求：
1. 当 `include_system=False` 时，过滤掉所有 `role == "system"` 的消息
2. 从过滤后的结果里取最后 `max_count` 条
3. 返回格式化字符串，每行 `role: content`
> 考察：函数、默认参数、条件判断、推导式、切片、join —— 模块 A 全部知识点的串联
---
"""

messages = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良，帮我查原因"},
    {"role": "assistant", "content": "好的，我先查一下3号产线的工单记录"},
    {"role": "user", "content": "重点是昨天下午那批"},
    {"role": "assistant", "content": "已找到，下午2点到5点有3个批次异常"},
]

print("messages:",messages,"\n")

def summarize_messages(messages, max_count=3, include_system=False):
    filtered = messages
    if not include_system: #当include_system 为false时，not include_system 为true,走下面过滤system的记录
        filtered = [m for m in messages if m["role"] != "system"]

    recent = filtered[-max_count:] # 取出过滤system后的 最后max_count条
    lines = [f'{m["role"]}:{m["content"]}' for m in recent]
    return "\n".join(lines)

print(summarize_messages(messages))
print("---")
print(summarize_messages(messages, max_count=2, include_system=True))