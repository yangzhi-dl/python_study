#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/18 20:19
@Desc    : 
"""

# utils.py
def build_context(messages):
    lines = []
    for m in messages:
        lines.append(f'{m["role"]}: {m.get("content", "")}')
    return "\n".join(lines)


# main.py
MESSAGES = [
    {"role": "system", "content": "你是助手"},
    {"role": "user"},                          # ← 少了 content
]
print(build_context(MESSAGES))