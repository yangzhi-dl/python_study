#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 21:35
@Desc    : 用 TypedDict 描述消息字典的结构，然后改掉练习 1 里那个 list[dict] 的模糊标注。
class MessageDict(TypedDict):
    role: str
    content: str
改完后，build_context(messages: list[MessageDict], ...)。
关键体验：在 PyCharm 里敲 messages[0][" 的时候，会不会自动提示 role 和 content？
考察：TypedDict 为什么重要：dict 是"什么键都行"，TypedDict 是"只有这几个键"——PyCharm 能据此做补全和检查
"""
from typing import Annotated, get_type_hints

count: Annotated[int, "必须大于0"] = 5
print(get_type_hints(__name__))
# {'count': <class 'int'>}