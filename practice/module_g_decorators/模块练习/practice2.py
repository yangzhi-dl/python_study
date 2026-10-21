#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/20 21:40
@Desc    : 写一个 @logger
打印函数名、参数、返回值：

@logger
def greet(name: str) -> str:
    return f"你好, {name}"

greet("Ember")
期望输出：

[logger] 调用 greet(name='Ember')
[logger] greet 返回: 你好, Ember
"""
import functools


def logger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        parts =[]
        for a in args:
            parts.append(repr(a))
        for k,v in kwargs.items():
            parts.append(f"{k}={v}")


        print(f"[logger] 调用 {func.__name__}({', '.join(parts)})")#获取方法名
        result = func(*args, **kwargs)
        print(f"[logger] {func.__name__} 返回: {result}")
        return result

    return wrapper


@logger
def greet(name:str) -> str:
    return f"你好，{name}"

greet("Ember")
