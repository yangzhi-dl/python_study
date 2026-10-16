#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : 现在直接 print(msg) 会输出类似 <__main__.Message object at 0x000001A2B3C4> —— 完全看不懂。
给 Message 加 __repr__ 方法，让它输出：
print(msg)     # <Message user: 3号产线有不良>
考察：魔术方法（双下划线方法） 为什么需要：调试时 print(对象) 能直接看到内容，不用一个个属性点出来
"""
class Message:

    def __repr__(self):
        return f"<Message {self.role}: {self.content}>"

