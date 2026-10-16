#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : 用 @dataclass 重写 Message 类，看看能省多少代码。
要求功能一样：
msg = Message("user", "你好")
print(msg.role)          # user
print(msg)               # Message(role='user', content='你好')
对比一下：不用 dataclass 时你写了多少行？用了之后呢？
考察：@dataclass 装饰器 它自动帮你生成：__init__、__repr__、__eq__
"""
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


msg = Message("user", "你好")
print(msg.role)
print(msg)