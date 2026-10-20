#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/18 22:15
@Desc    : 异步生成器 async for（流式输出的核心）

"""
import asyncio


async def fake_llm_stream(prompt: str):
    """模拟 LLM 逐字返回（真实场景里是 llm.astream）"""
    response = "3号产线的不良根因是：回流焊温度偏低 5 度。"

    for char in response:
        await asyncio.sleep(0.1)     # 模拟网络延迟
        yield char                     # 一个字一个字往外吐


async def main():
    print("用户: 3号产线为什么不良？")
    print("助手: ", end="", flush=True)

    async for chunk in fake_llm_stream("3号产线为什么不良？"):
        print(chunk, end="", flush=True)

    print()     # 换行


asyncio.run(main())