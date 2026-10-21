#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/20 21:40
@Desc    : 写一个 @retry（带参数）
要求：失败重试 N 次，间隔 0.5 秒。

attempt = 0
@retry(max_attempts=3, delay=0.5)
def unstable():
    global attempt
    attempt += 1
    if attempt < 3:
        raise ValueError(f"第 {attempt} 次失败")
    return "成功"

print(unstable())     # 成功

装饰器：
**记住这个规律**：

- 不带参数 → **两层**
- 带参数 → **三层**
"""
import time,functools


def retry(max_attempts: int = 3, delay: float = 0.5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        print(f"[retry] 第 {attempt + 1} 次失败: {e}，{delay} 秒后重试")
                        time.sleep(delay)
            raise last_error
        return wrapper
    return decorator


attempt = 0

@retry(max_attempts=3, delay=0.5)
def unstable():
    global attempt
    attempt += 1
    if attempt < 3:
        raise ValueError(f"第 {attempt} 次失败")
    return "成功"

print(unstable())