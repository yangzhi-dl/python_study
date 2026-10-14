#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 12_作用域与闭包.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】作用域（LEGB）、闭包。参考答案见 12_作用域与闭包_demo.py
"""

# 在本文件手敲练习，卡住时对照 12_作用域与闭包_demo.py
# ============================================================
# 一、作用域 LEGB：Local > Enclosing > Global > Builtin
# ============================================================
x = "global"          # 全局作用域

def demo_scope():
    print("=" * 50)
    print("一、作用域查找顺序 LEGB")
    print("=" * 50)

    x = "local"       # 局部作用域，遮蔽同名全局变量

    def inner():
        x = "enclosing-inner"
        print("  inner 看到:", x)

    print("  demo_scope 看到:", x)
    inner()
    print("  全局 x 未被改动:", globals()["x"])

# ============================================================
# 二、global / nonlocal：修改外层变量
# ============================================================
counter = 0


def demo_global():
    print("\n" + "=" * 50)
    print("二、global / nonlocal")
    print("=" * 50)

    global counter
    counter += 1                     # 声明 global 才能修改全局变量
    print("  global counter ->", counter)

    # nonlocal：修改"外层函数"的变量（闭包里常用）
    def outer():
        count = 0
        def increment():
            nonlocal count           # 不声明则 count 只是局部，会报错/无效
            count += 1
        increment()
        increment()
        print("  nonlocal count ->", count)
    outer()
# ============================================================
# 三、闭包：内层函数"记住"外层变量
# ============================================================
def make_multiplier(factor):
    """外层函数的参数 factor 被内层函数捕获，形成闭包。"""
    def multiply(x):
        return x * factor            # 引用了外层的 factor
    return multiply                  # 返回内层函数


def demo_closure():
    print("\n" + "=" * 50)
    print("三、闭包")
    print("=" * 50)

    double = make_multiplier(2)      # factor 被"记住"为 2
    triple = make_multiplier(3)
    print("  double(10) =", double(10))
    print("  triple(10) =", triple(10))
    # 即使 make_multiplier 已执行完，factor 仍存活在闭包里

# ============================================================
# 四、实战：用闭包做计数器 / 累加器
# ============================================================
def make_counter():
    n = 0
    def counter(step=1):
        nonlocal n
        n += step
        return n
    return counter


def demo_counter():
    print("\n" + "=" * 50)
    print("四、实战：闭包计数器")
    print("=" * 50)

    c = make_counter()
    print("  调用序列:", c(), c(), c(step=10))   # 1, 2, 12（状态被记住）

    c2 = make_counter()                          # 每个闭包有独立状态
    print("  独立的新计数器:", c2())              # 1，不受 c 影响


# ============================================================
# 五、经典坑：循环里创建的闭包共享同一个变量
# ============================================================
def demo_loop_pitfall():
    print("\n" + "=" * 50)
    print("五、坑：循环闭包捕获的是变量本身")
    print("=" * 50)

    # ❌ 常见误解：以为每个函数记住各自的 i
    funcs_bad = [lambda: i for i in range(3)]
    # 循环结束后 i 停在 2，所有函数读到同一个 i
    print("  错误结果:", [f() for f in funcs_bad])   # [2, 2, 2]

    # ✅ 用默认参数在创建时"定格"当前值
    funcs_good = [lambda i=i: i for i in range(3)]
    print("  正确结果:", [f() for f in funcs_good])  # [0, 1, 2]


if __name__ == "__main__":
    demo_scope()
    demo_global()
    demo_closure()
    demo_counter()
    demo_loop_pitfall()
