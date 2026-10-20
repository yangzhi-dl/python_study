#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/18 22:15
@Desc    : async / await

async def get_data():            # ① async def 定义"协程函数"
    result = await something()    # ② await 等待一个异步操作
    return result

asyncio.run(get_data())          # ③ 入口，启动事件循环
"""
import asyncio


async def step1():
    print("step1 开始")
    await asyncio.sleep(1)
    print("step1 结束")
    return "A"


async def step2():
    print("step2 开始")
    await asyncio.sleep(1)
    print("step2 结束")
    return "B"


async def main():
    print("=== 顺序 await（总共 2 秒）===")
    a = await step1()
    b = await step2()
    print(f"结果: {a}, {b}")


asyncio.run(main())
"""
=== 顺序 await（总共 2 秒）===
step1 开始
step1 结束
step2 开始
step2 结束
结果: A, B
"""