#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 05_条件_demo.py
@Author  : yz.yangzhi
@Date    : 2026-10-14 09:00
@Desc    : 条件分支 if/elif/else、三元表达式、真值判断。
"""


# ============================================================
# 一、if / elif / else
# ============================================================
def demo_if():
    print("=" * 50)
    print("一、if / elif / else")
    print("=" * 50)

    score = 85

    if score >= 90:
        level = "优秀"
    elif score >= 80:
        level = "良好"
    elif score >= 60:
        level = "及格"
    else:
        level = "不及格"
    print(f"分数 {score} -> {level}")

    # elif 是自上而下匹配，命中一个就退出，顺序很重要
    # 反例：把 >=60 放最前面，会永远命中它，后面的分支形同虚设


# ============================================================
# 二、三元表达式（条件表达式）
# ============================================================
def demo_ternary():
    print("\n" + "=" * 50)
    print("二、三元表达式")
    print("=" * 50)

    age = 20
    # 语法：值A if 条件 else 值B  —— 条件为真取 A，否则取 B
    status = "成年" if age >= 18 else "未成年"
    print(f"age={age} ->", status)

    # 常用于赋值和 return，替代简短的 if/else
    temp = 38
    print("发烧" if temp >= 37.3 else "正常")

    # 嵌套三元可读性差，超过一层建议改回 if/elif
    x = 5
    label = "大" if x > 10 else ("中" if x > 3 else "小")
    print("嵌套三元:", label)


# ============================================================
# 三、真值判断（falsy / truthy）
# ============================================================
def demo_truthy():
    print("\n" + "=" * 50)
    print("三、真值判断")
    print("=" * 50)

    # 以下都被视为 False（falsy）：0、""、[]、{}、None、False
    empty_list = []
    empty_str = ""
    zero = 0
    nothing = None

    # Pythonic：直接判断对象真假，不用 len(x) == 0
    if not empty_list:
        print("列表为空")
    if not (empty_str or zero or nothing):
        print("这些都是 falsy")

    # 给默认值的惯用法：x = x or default（x 为 falsy 时取 default）
    name = "" or "匿名用户"
    print("兜底默认名:", name)

    # ⚠️ 注意 `==` 与 `is` 的区别：
    #   == 比较值；is 比较是否同一对象。判断 None 用 is None
    val = None
    print("是 None 吗:", val is None)


# ============================================================
# 四、实战：Agent 路由判断
# ============================================================
def demo_routing():
    print("\n" + "=" * 50)
    print("四、实战：意图路由")
    print("=" * 50)

    def route(user_input: str) -> str:
        text = user_input.lower()
        if "天气" in text:
            return "get_weather"
        elif "搜索" in text or "查" in text:
            return "search_web"
        elif "邮件" in text or "发送" in text:
            return "send_email"
        else:
            return "chat"

    for q in ["明天天气如何", "帮我搜索一下", "随便聊聊"]:
        print(f"  '{q}' -> {route(q)}")


if __name__ == "__main__":
    demo_if()
    demo_ternary()
    demo_truthy()
    demo_routing()
