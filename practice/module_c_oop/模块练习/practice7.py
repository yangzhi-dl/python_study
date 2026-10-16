#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : 定义一个 Tool 类，有 name 和 description。再加一个 is_dangerous 属性，判断这个工具是否危险。
t1 = Tool("delete_file", "删除文件")
t2 = Tool("query_workorder", "查询工单")
print(t1.is_dangerous)   # True
print(t2.is_dangerous)   # False
关键要求：is_dangerous 调用时不加括号，像普通属性一样访问。
危险工具名单：delete_file、execute_shell、drop_table
考察：@property —— 把方法伪装成属性 为什么需要：调用方不用关心它是算出来的还是存起来的
"""
from dataclasses import dataclass


@dataclass
class Tool:
    name:str
    description:str


    @property
    def is_dangerous(self):
        dangerous_tools = ["delete_file", "execute_shell", "drop_table"]
        return self.name in dangerous_tools

t1 = Tool("delete_file", "删除文件")
t2 = Tool("query_workorder", "查询工单")
print(t1.is_dangerous)   # True
print(t2.is_dangerous)   # False
