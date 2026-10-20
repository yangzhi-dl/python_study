#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/18 22:15
@Desc    : 生成器 yield（异步的基础
"""
def count_up(n: int):
    print(">>> 生成器开始执行")
    for i in range(n):
        print(f"    [产出前] i={i}")
        yield i
        print(f"    [恢复后] i={i}")
    print(">>> 生成器结束")


gen = count_up(3)
print("① 拿到生成器对象（此时函数体还没执行）")

print("② 开始消费：")
for value in gen:
    print(f"    [消费到] {value}")

print("③ 结束")