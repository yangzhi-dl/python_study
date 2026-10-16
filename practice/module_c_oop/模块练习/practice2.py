#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : 给 Message 加一个方法 to_text()，返回 "role: content" 格式的字符串。

msg = Message("user", "3号产线有不良")
print(msg.to_text())     # user: 3号产线有不良
考察：方法的定义与调用、self 在方法里怎么用
"""
class Message:

    def __init__(self,role,content):#`self` 就是"这个实例自己"。`self.role = role` 的意思是：把参数 `role` 存到实例身上。
        self.role=role
        self.content = content

    def to_text(self):
        return f"{self.role}:{self.content}"




msg = Message("user","xxxxxxxx")
print(msg.role)
print(msg.content)
print(msg.to_text())# user: 3号产线有不良