#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : 定义 SystemMessage 类，继承 Message，但 role 固定为 "system"，只需要传 content。
sys_msg = SystemMessage("你是不良品根因分析助手")
print(sys_msg.role)      # system
print(sys_msg.content)   # 你是不良品根因分析助手
print(sys_msg.to_text()) # system: 你是不良品根因分析助手
考察：继承、super().__init__() 的调用
"""
from practice.module_c_oop.模块练习.practice2 import Message


class SystemMessage(Message):
    def __init__(self, content):
        super().__init__("system", content)


sys_msg = SystemMessage("你是不良品根因分析助手")
print(sys_msg.role)
print(sys_msg.content)
print(sys_msg.to_text())