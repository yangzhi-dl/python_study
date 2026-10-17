#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 21:35
@Desc    :

"""
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


msg = Message(role="user", content="你好")
print(msg.role)      # user
print(msg)           # role='user' content='你好'