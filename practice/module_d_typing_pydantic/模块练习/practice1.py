#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 21:35
@Desc    :  给下面这个函数加上完整的类型注解：
```python
def build_context(messages, max_count=3):
    recent = messages[-max_count:]
    lines = []
    for m in recent:
        lines.append(f'{m["role"]}: {m["content"]}')
    return "\n".join(lines)
```
要求标注出：

- `messages` 是「字典组成的列表」
- `max_count` 是整数
- 返回值是字符串
> 考察：`list[dict]`、`int`、`-> str
"""
def build_context(messages:list[dict], max_count: int = 3) -> str:
    recent = messages[-max_count:]
    lines=[]
    for m in messages:
        lines.append(f'{m["role"]}:{m["content"]}')
    return "\n".join(lines)

if __name__ == '__main__':
    messages = [
        {"role": "system", "content": "你是不良品根因分析助手"},
        {"role": "user", "content": "3号产线昨天有5个批次不良"},
        {"role": "assistant", "content": "我先查一下工单记录"},
    ]
    print(build_context(messages)+"\n")
    print(build_context(messages, max_count=2))
