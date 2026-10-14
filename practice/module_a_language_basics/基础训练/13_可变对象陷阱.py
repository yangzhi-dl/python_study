#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 13_可变对象陷阱.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】dict/list 传引用（可变对象陷阱）。参考答案见 13_可变对象陷阱_demo.py
"""
import copy

# 在本文件手敲练习，卡住时对照 13_可变对象陷阱_demo.py
# ============================================================
# 一、赋值 ≠ 复制：可变对象是"传引用"
# ============================================================

def demo_reference():
    print("=" * 50)
    print("一、赋值是引用而非复制")
    print("=" * 50)

    a = [1, 2, 3]
    b = a                # b 和 a 指向同一个列表对象（不是复制！）
    b.append(4)
    print("  改 b 后 a =", a, "  # a 也被影响了")
    print("  a is b:", a is b)          # True，同一对象

    # 不可变对象（int/str/tuple）没这个问题
    x = 10
    y = x
    y = 20
    print("  不可变: x =", x, "y =", y)  # x 不受影响

# ============================================================
# 二、函数参数也是传引用
# ============================================================
def demo_func_ref():
    print("\n" + "=" * 50)
    print("二、函数内修改可变对象会影响外部")
    print("=" * 50)

    def add_item(state):
        state["count"] += 1          # 直接改传入的字典（原地修改）
        state.setdefault("log", []).append("hit")

    my_state = {"count": 0}
    add_item(my_state)
    add_item(my_state)
    print("  两次调用后 state =", my_state)
    # 函数没有 return，外部对象却被改了 —— 因为传的是引用

    # 若想"不改外部"，应在函数内先复制一份
    def add_item_safe(state):
        new = dict(state)            # 浅拷贝一层
        new["count"] = new.get("count", 0) + 1
        return new

    before = {"count": 5}
    after = add_item_safe(before)
    print("  安全版 before =", before, "-> new =", after)


# ============================================================
# 三、浅拷贝 vs 深拷贝
# ============================================================
def demo_copy():
    print("\n" + "=" * 50)
    print("三、浅拷贝 vs 深拷贝")
    print("=" * 50)

    original = {"tags": ["a", "b"], "meta": {"n": 1}}

    # 浅拷贝：只复制最外层，内层可变对象仍共享
    shallow = copy.copy(original)
    shallow["tags"].append("SHARED")
    print("  浅拷贝后 original.tags =", original["tags"], "  # 被连带改了")

    # 深拷贝：递归复制全部层级，彻底独立
    original2 = {"tags": ["a", "b"], "meta": {"n": 1}}
    deep = copy.deepcopy(original2)
    deep["tags"].append("INDEP")
    print("  深拷贝后 original2.tags =", original2["tags"], "  # 未受影响")

    # 常见复制手段对比
    lst = [1, 2, 3]
    print("  切片复制:", lst[:], "| list()复制:", list(lst), "| 推导式:", [x for x in lst])


# ============================================================
# 四、汇总：可变 vs 不可变
# ============================================================
def demo_summary():
    print("\n" + "=" * 50)
    print("四、可变 / 不可变对照")
    print("=" * 50)

    print("  不可变(hashable)：int float bool str tuple None  -> 赋值即独立")
    print("  可变(mutables)  ：list dict set                 -> 赋值传引用")

    # 可变对象不能当 dict 的键 / set 的元素（不可哈希）
    try:
        {[1, 2]: "x"}
    except TypeError as e:
        print("  用 list 做键会报错:", e)

    # 实战建议：处理 Agent state 时，需要"快照"就用 deepcopy，避免污染历史状态
    state = {"messages": ["m1"]}
    snapshot = copy.deepcopy(state)
    state["messages"].append("m2")
    print("  快照保持:", snapshot["messages"], "| 当前:", state["messages"])


if __name__ == "__main__":
    demo_reference()
    demo_func_ref()
    demo_copy()
    demo_summary()
