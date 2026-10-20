#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/18 22:15
@Desc    : asyncio.gather 并发

"""
import asyncio

from practice.module_f_async.模块练习.practice3 import step1, step2


async def main():
    print("=== gather 并发（总共 1 秒）===")
    results = await asyncio.gather(
        step1(),
        step2(),
    )
    print(f"结果: {results}")


asyncio.run(main())
"""
=== gather 并发（总共 1 秒）===
step1 开始
step2 开始
step1 结束
step2 结束
结果: ['A', 'B']

注意：两个 开始 都在前面 —— 说明是同时启动的。
"""