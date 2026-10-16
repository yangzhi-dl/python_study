#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : 给 Message 加一个类方法 from_dict()，从字典创建实例。

data = {"role": "user", "content": "你好"}
msg = Message.from_dict(data)
print(msg.role)      # user
关键区别：

普通方法第一个参数是 self（实例）
类方法第一个参数是 cls（类本身）
考察：@classmethod 为什么需要：这是"工厂方法"模式，Agent 项目里从 JSON 还原对象时天天用
"""
from dataclasses import dataclass


@dataclass
class Message:

    role: str
    content: str


    @classmethod
    def from_dict(cls, data):
        return cls(data["role"], data["content"])


data = {"role": "user", "content": "你好"}
msg = Message.from_dict(data)
print(msg.role)
