#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/18 22:15
@Desc    : 同步 vs 异步
"""
import asyncio
import time

def fetch(name: str, seconds: float) -> str:
    print(f"  开始请求 {name}")
    time.sleep(seconds)          # 模拟网络等待
    print(f"  完成请求 {name}")
    return f"{name} 的结果"


def main_sync():
    start = time.perf_counter()

    results = []
    for name in ["工单", "质检", "BOM"]:
        results.append(fetch(name, 1))

    elapsed = time.perf_counter() - start
    print(f"结果: {results}")
    print(f"总耗时: {elapsed:.2f} 秒")



async def fetch_async(name: str, seconds: float) -> str:
    print(f"  开始请求 {name}")
    await asyncio.sleep(seconds)     # ← 注意：不是 time.sleep
    print(f"  完成请求 {name}")
    return f"{name} 的结果"


async def main_async():
    start = time.perf_counter()

    results = await asyncio.gather(
        fetch_async("工单", 1),
        fetch_async("质检", 1),
        fetch_async("BOM", 1),
    )

    elapsed = time.perf_counter() - start
    print(f"结果: {results}")
    print(f"总耗时: {elapsed:.2f} 秒")




if __name__ == "__main__":
    # main_sync()
    asyncio.run(main_async())