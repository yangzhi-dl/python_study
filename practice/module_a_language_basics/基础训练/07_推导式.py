#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 07_推导式.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】列表/字典推导式（过滤消息、批量转换）。参考答案见 07_推导式_demo.py
"""

# 在本文件手敲练习，卡住时对照 07_推导式_demo.py
def demo_list_comp():
    print("=" * 50)
    print("一、列表推导式")
    print("=" * 50)

    # 基本式：[表达式 for 变量 in 可迭代]
    squares = [x * x for x in range(1,6)]
    print("平方:", squares) #平方: [1, 4, 9, 16, 25]

    # 带过滤：[表达式 for 变量 in 可迭代 if 条件]
    evens = [x for x in range(10) if x % 2 == 0]
    print("偶数:", evens)


    # 等价的传统写法（对比可读性）
    evens2 = []
    for x in range(10):
        if x % 2 == 0:
            evens2.append(x)
    print("传统写法:", evens2)


    # 带三元：偶数保留、奇数变 0
    mixed = [x if x % 2 == 0 else 0 for x in range(6)]
    print("条件替换:", mixed)

# ============================================================
# 二、字典推导式
# ============================================================
def demo_dict_comp():
    print("\n" + "=" * 50)
    print("二、字典推导式")
    print("=" * 50)

    # {键表达式: 值表达式 for ...}
    words = ["apple", "banana", "cherry"]
    lengths = {w: len(w) for w in words}
    print("单词->长度:", lengths)

    # 键值互换
    prices = {"book": 30, "pen": 5}
    inverted = {v: k    for k,v in prices.items()}
    print("键值互换:", inverted)

    # 从两个列表构造字典（等价 dict(zip(...))）
    names = ["张三", "李四"]
    scores = [90, 85]
    d = { n: s for n ,s in zip(names,scores) }
    print("zip 构造字典:", d)

# ============================================================
# 三、集合推导式 + 嵌套
# ============================================================
def demo_set_nested():
    print("\n" + "=" * 50)
    print("三、集合推导式 / 嵌套")
    print("=" * 50)

    # 集合推导式（自动去重）
    nums = [1, 2, 2, 3, 3, 3]
    uniq_squares = {x * x for x in nums}
    print("去重平方集合:", uniq_squares)

    # 嵌套 for：展开二维
    matrix = [[1, 2], [3, 4], [5, 6]]
    flat = [n for row in matrix for n in row]
    print("展平:", flat)


# ============================================================
# 四、实战：过滤 / 转换消息
# ============================================================
def demo_messages():
    print("\n" + "=" * 50)
    print("四、实战：消息过滤与转换")
    print("=" * 50)

    messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好呀"},
        {"role": "user", "content": "再见"},
    ]

    # 1. 过滤：只保留用户消息
    user_msgs = [m for m in messages if m['role'] == 'user']
    print("用户消息数:", len(user_msgs))



    # 2. 批量转换：抽取所有 content
    contents = [m['content'] for m in messages]
    print("全部内容:", contents)

    # 3. 转换结构：role->content 的字典（同 role 会覆盖，只留最后一条）
    last_map = {m["role"]: m["content"] for m in messages}
    print("角色->最后内容:", last_map)

    # 4. 加前缀的新列表（批量改字段）
    tagged = [{**m, "content": f"[{m['role']}] {m['content']}"} for m in messages]
    print("加标签首条:", tagged[0]["content"])

if __name__ == "__main__":
    # demo_list_comp()
    # demo_dict_comp()
    # demo_set_nested()
    demo_messages()