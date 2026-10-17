#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/16 21:35
@Desc    :

"""
from pydantic import BaseModel, Field


class Tool(BaseModel):
    name: str = Field(description="工具名称")
    description: str = Field(description="工具用途说明，给 LLM 看的")
    dangerous: bool = Field(default=False, description="是否为危险操作")


tool = Tool(name="query_workorder", description="查询产线工单记录")
print(tool.dangerous)