#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practise1.py
@Author  : yz.yangzhi
@Date    : 2026/10/14 21:15
@Desc    : 写一个函数 `call_llm(messages, **kwargs)`，把传入的额外参数打印出来。
 然后这样调用：
call_llm(messages, temperature=0.7, model="gpt-4", max_tokens=1024)

            要求输出能看清每个参数名和值。
            > 考察：`**kwargs` 的接收与遍历
            > **为什么重要**：LangChain 的每个调用都是这个形状 —— `llm.invoke(messages, temperature=0.7, ...)`
"""

messages = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良，帮我查原因"},
    {"role": "assistant", "content": "好的，我先查一下3号产线的工单记录"},
    {"role": "user", "content": "重点是昨天下午那批"},
    {"role": "assistant", "content": "已找到，下午2点到5点有3个批次异常"},
]

print(messages)

def call_llm(messages, **kwargs):
    print(f"消息条数: {len(messages)}")
    print("额外参数:")
    for key,value in kwargs.items():
        print(f"   {key}: {value}")


call_llm(messages, temperature=0.7, model="gpt-4", max_tokens=1024)
