#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 21:35
@Desc    :

"""
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    name: str = Field(description="参数名")
    type: str = Field(default="string", description="参数类型")
    description: str = Field(default="", description="参数说明")


class Tool(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter] = []


tool = Tool(
    name="query_workorder",
    description="查询产线工单记录",
    parameters=[
        ToolParameter(name="line", description="产线编号"),
        ToolParameter(name="date", description="日期"),
    ],
)

print(tool.parameters[0].name)
print(len(tool.parameters))