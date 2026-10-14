#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 11_高阶函数与lambda.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】函数是一等公民（可传参、可返回）+ lambda。参考答案见 11_高阶函数与lambda_demo.py
"""

# 在本文件手敲练习，卡住时对照 11_高阶函数与lambda_demo.py
# ============================================================
# 一、函数是"一等公民"：能赋值、能传参、能返回
# ============================================================
def demo_first_class():
    print("=" * 50)
    print("一、函数是一等公民")
    print("=" * 50)

    # 1. 函数可以赋值给变量
    def shout(text):
        return text.upper() + "!"
    speak = shout                    # speak 现在指向同一个函数
    print("赋值后调用:", speak("hi"))

    # 2. 函数可以作为参数传给另一个函数（= 回调）
    def apply_twice(func, value):
        return func(func(value))

    def add10(x):
        return x + 10
    print("apply_twice(add10, 5) =", apply_twice(add10, 5))  # 5->15->25


# ============================================================
# 二、lambda：一行的小匿名函数
# ============================================================
def demo_lambda():
    print("\n" + "=" * 50)
    print("二、lambda")
    print("=" * 50)

    # lambda 参数: 返回值表达式（只能是表达式，没有 if/else 语句块）
    square = lambda x: x * x
    print("square(6) =", square(6))

    # 最大价值：作为 key/回调，省去单独定义函数
    users = [{"name": "Tom", "age": 30}, {"name": "Amy", "age": 25}]
    by_age = sorted(users, key=lambda u: u["age"])
    print("按年龄排序:", [u["name"] for u in by_age])

    # 多参数
    add = lambda a, b: a + b
    print("add(3,4) =", add(3, 4))

    # 说明：复杂逻辑仍用 def，lambda 只适合一行小函数

# ============================================================
# 三、map / filter：配合 lambda 批量处理
# ============================================================
def demo_map_filter():
    print("\n" + "=" * 50)
    print("三、map / filter")
    print("=" * 50)

    nums = [1, 2, 3, 4, 5, 6]

    # map：对每个元素应用函数（返回迭代器，list 展开）
    print("map 平方:", list(map(lambda x: x * x, nums)))

    # filter：保留使函数返回真的元素
    print("filter 偶数:", list(filter(lambda x: x % 2 == 0, nums)))

    # 对比：这两件事用列表推导式往往更清晰（见 07）
    print("推导式偶数平方:", [x * x for x in nums if x % 2 == 0])

# ============================================================
# 四、实战：注册表（把函数存进 dict，按名调度） 字典注册表路由【装饰器自动注册】
# ============================================================
def demo_registry():
    print("\n" + "=" * 50)
    print("四、实战：函数注册表（LangGraph add_node 的本质）")
    print("=" * 50)

    # 工具/节点处理函数
    def get_weather(city):
        return f"{city}：晴 22°C"

    def search_web(query):
        return f"搜索『{query}』完成"

    # 把"函数本身"（不加括号）作为值放进字典
    registry = {
        "get_weather": get_weather,
        "search_web": search_web,
    }

    # 根据模型返回的工具名，取出对应函数并调用
    for tool_name, arg in [("get_weather", "北京"), ("search_web", "Python 列表")]:
        handler = registry[tool_name]        # 取出函数对象
        print(f"  调用 {tool_name} ->", handler(arg))   # 加括号才执行

    # 也能动态注册新工具
    registry["send_email"] = lambda to: f"已发邮件给 {to}"
    print("  动态注册:", registry["send_email"]("a@b.com"))

if __name__ == "__main__":
    # demo_first_class()
    # demo_lambda()
    # demo_map_filter()
    demo_registry()
