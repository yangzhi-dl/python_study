#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practise1.py
@Author  : yz.yangzhi
@Date    : 2026/10/14 21:15
@Desc    :  写一个函数 `build_context(messages, max_count=3)`：
- 只取最后 `max_count` 条
- 返回拼接成的一段文本，每行格式为 `role: content`
- 用换行符 `\n` 分隔
调用 `build_context(messages)` 和 `build_context(messages, 2)`，看结果差异。
> 考察：函数定义、默认参数、切片、字符串 join
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

def build_context(messages,max_count=3):
   recent = messages[-max_count:] #取最后3条
   lines = [f'{m["role"]}:{m["content"]}' for m in recent]
   return "\n".join(lines)


print(build_context(messages))
print("-----------")
print(build_context(messages,2))