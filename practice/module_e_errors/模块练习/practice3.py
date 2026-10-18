#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : practice1.py
@Author  : yz.yangzhi
@Date    : 2026/10/18 20:19
@Desc    : 把场景 1 和场景 3 结合起来：写一个 `call_tool_with_retry`，执行工具，失败重试 3 次，3 次都失败返回错误字符串（不抛异常）。
"""
import time

def call_tool_with_retry(tool_func,args:dict,max_retries:int=3) -> str:
    """
    执行工具，失败重试 3 次，3 次都失败返回错误字符串（不抛异常）。
    :param tool_func: 工具函数
    :param args: 工具函数的参数
    :param max_retries: 最大重试次数
    :return: 工具执行结果或错误字符串
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return str(tool_func(*args))
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 每次重试等待时间增加
                print(f"第 {attempt + 1} 次失败: {e}，{wait} 秒后重试")
                time.sleep(wait)

    return f"[工具执行失败] 重试 {max_retries} 次仍失败: {type(last_error).__name__}: {last_error}"