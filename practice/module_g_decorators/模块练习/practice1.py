#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/20 21:40
@Desc    :  要求：

打印函数名和执行耗时
支持任意参数的函数
保留原函数的 __name__ 和 __doc__
"""
import functools
import time

def timer(func):
    @functools.wraps(func) # 保留原函数的 __name__ 和 __doc__
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[timer] {func.__name__} 耗时 {elapsed:.8f} 秒")
        return result
    return wrapper

@timer
def slow_add(a:int ,b:int) -> int:

    time.sleep(0.1)
    return a+b


print(slow_add(1, 2))
print(slow_add.__name__)
print(slow_add.__doc__)