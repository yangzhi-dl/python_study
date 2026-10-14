#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 04_嵌套结构.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】list[dict]、dict[str, list]（Agent 数据标准形状）。参考答案见 04_嵌套结构_demo.py
"""

# 在本文件手敲练习，卡住时对照 04_嵌套结构_demo.py
def demo_list_of_dist():
    print("=" * 50)
    print("一、list[dict]")
    print("=" * 50)

    # 每条"记录"是一个 dict，多条记录放进一个 list
    users = [
        {"name": "张三", "age": 25, "tags": ["admin", "dev"]},
        {"name": "李四", "age": 30, "tags": ["dev"]},
        {"name": "王五", "age": 22, "tags": ["ops", "dev"]},
    ]
    # 取第 2 个用户的名字：先按下标取元素(dict)，再按 key 取值
    print("第二个用户：",users[1]["name"])

    # 遍历：每个元素是 dict
    for u in users:
        print(f"  {u['name']} - {u['age']}岁 - 标签{u['tags']}")

    older = [u["name"] for u in users if u["age"] > 24]
    print("年龄 > 24 的用户有：", older)

    # 查找单个：next + 生成器，取第一个匹配（找不到返回 None）
    target = next((u for u in users if u["name"] == "李四"), None)
    print("找到的用户是：", target)

    # 访问嵌套的 list：某用户的第一个标签
    print("张三的首个标签:", users[0]["tags"][0])

# ============================================================
# 二、dict[str, list]：字典的值是列表（分组 / 索引结构）
# ============================================================
def demo_dict_of_list():
    print("\n" + "=" * 50)
    print("二、dict[str, list]")
    print("=" * 50)

    # 典型用途：按 key 分组，把同类项归到一个 list
    group = {}
    words = ["apple", "avocado", "banana", "blueberry", "cherry"]

    # 按首字母分组
    for w in words:
        first = w[0]
        # 惯用法：键不存在时先初始化空列表，再 append
        if first not in group:
            group[first] = []
        group[first].append(w)
    print("按首字母分组:", group)

    # 更简洁：setdefault（键不存在才设默认值 []）
    group2 = {}
    for w in words:
        group2.setdefault(w[0], []).append(w)
    print("setdefault 分组:", group2)

    # 遍历分组
    for letter, items in group2.items():
        print(f"group2:  {letter}: {items}")
# ============================================================
# 三、实战：messages（list[dict]）+ 按 role 分组
# ============================================================
def demo_messages():
    print("\n" + "=" * 50)
    print("三、实战：消息分组（过关检验原型）")
    print("=" * 50)

    messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
        {"role": "user", "content": "介绍下列表"},
    ]

    # 按 role 把 content 归类 -> dict[str, list[str]]
    by_role = {}
    for m in messages:
        by_role.setdefault(m["role"],[]).append(m["content"])
    print("按 role 分组:", by_role)

    # 统计每种角色消息数
    counts = {role: len(items) for role, items in by_role.items()}
    print("角色计数:", counts)



# ============================================================
# 四、深层嵌套的链式取值（API 返回常见）
# ============================================================
def demo_deep():
    print("\n" + "=" * 50)
    print("四、深层嵌套安全取值")
    print("=" * 50)

    data = {
        "choices": [
            {"message":
                 {
                     "role": "assistant", "content": "这是回答"
                  }
            }
        ]
    }
    # 直接链式取（结构确定时）
    content = data["choices"][0]["message"]["content"]
    print("模型回答:", content)

    # 结构不确定时，层层 .get 兜底，避免 KeyError / IndexError
    safeMessage = data.get("choices", [{}])[0].get("message", {}).get("content", "无内容")
    print("安全取值:", safeMessage)


if __name__ == "__main__":
    # demo_list_of_dist()
    # demo_dict_of_list()
    # demo_messages()
    demo_deep()