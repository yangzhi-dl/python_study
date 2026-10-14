#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practise1.py
@Author  : yz.yangzhi
@Date    : 2026/10/14 21:15
@Desc    :  用统计每种 `role` 各出现了多少次，输出成一个 dict，形如 `{"system": 1, "user": 2, "assistant": 2}`。
考察：dict 累加、`.get()` 给默认值
"""

from collections import Counter #通过导包计算方法
messages = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良，帮我查原因"},
    {"role": "assistant", "content": "好的，我先查一下3号产线的工单记录"},
    {"role": "user", "content": "重点是昨天下午那批"},
    {"role": "assistant", "content": "已找到，下午2点到5点有3个批次异常"},
]

print(messages)

counts ={}
for m in messages:
    role = m["role"] # 取出 role
    counts[role] = counts.get(role, 0) + 1 #去字典里查当前 role 已经出现了几次。如果还没出现过，就返回默认值 0。

print(counts)
counts2 ={}
counts2  = Counter(m["role"] for m in messages)
print(f"1",counts2)

