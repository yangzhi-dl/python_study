#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 19:58
@Desc    : 用 @dataclass 定义 Tool 类，包含：
name: str
description: str
parameters: dict
再加一个方法 to_schema()，返回 OpenAI 工具调用格式的字典：

tool = Tool(
    name="query_workorder",
    description="查询产线工单记录",
    parameters={"type": "object", "properties": {"line": {"type": "string"}}},
)
print(tool.to_schema())
期望输出：
{
    "type": "function",
    "function": {
        "name": "query_workorder",
        "description": "查询产线工单记录",
        "parameters": {"type": "object", "properties": {"line": {"type": "string"}}},
    },
}
考察：@dataclass + 方法 + 嵌套字典构造 —— 模块 C 全部知识点的串联 这题做通，你就理解了 LangChain 里 @tool 装饰器背后在干什么
"""
from dataclasses import dataclass




@dataclass
class Tool:
    name:str
    description:str
    parameters:dict


    def to_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

tool = Tool(
        name="query_workorder",
        description="查询产线工单记录",
        parameters={"type": "object", "properties": {"line": {"type": "string"}}},
    )

print(tool.to_schema())