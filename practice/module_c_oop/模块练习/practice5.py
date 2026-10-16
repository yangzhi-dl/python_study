#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : SystemMessage 的 to_text() 要改成 "[系统] content" 的格式（覆盖父类的实现）。
sys_msg = SystemMessage("你是助手")
print(sys_msg.to_text())     # [系统] 你是助手
msg = Message("user", "你好")
print(msg.to_text())         # user: 你好   ← 父类不受影响
考察：方法覆盖（override）—— 子类定义同名方法，会盖住父类的
"""
from practice.module_c_oop.模块练习.practice2 import Message


class SystemMessage(Message):
    def __init__(self, content):
        super().__init__("system", content)

    def to_text(self):
        return f"[系统] {self.content}"