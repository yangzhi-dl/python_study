#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : 定义一个 `Message` 类，有 `role` 和 `content` 两个属性，通过构造传入。
要求能这样用：
```python
msg = Message("user", "3号产线有不良")
print(msg.role)      # user
print(msg.content)   # 3号产线有不良
```
> 考察：`class` 定义、`__init__`、`self`
"""
class Message:

    def __init__(self,role,content):#`self` 就是"这个实例自己"。`self.role = role` 的意思是：把参数 `role` 存到实例身上。
        self.role=role
        self.content = content






msg = Message("user","xxxxxxxx")
print(msg.role)
print(msg.content)