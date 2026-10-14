#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 08_解包.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】序列解包 a,b=x、*args、**kwargs、**d。参考答案见 08_解包_demo.py
"""

# 在本文件手敲练习，卡住时对照 08_解包_demo.py
# ============================================================
# 一、序列解包（赋值左侧拆开右侧）
# ============================================================
def demo_unpack():
    print("=" * 50)
    print("一、基本解包")
    print("=" * 50)

    # 元组/列表拆给多个变量
    point = (3, 4)
    x, y = point
    print(f"x={x}, y={y}")

    # 交换变量（Python 惯用法，无需临时变量）
    a, b = 1, 2
    a, b = b, a
    print("交换后 a,b =", a, b)

    # * 收集"剩余"元素（星号表达式）
    first, *rest = [1, 2, 3, 4, 5]
    print("first =", first, "| rest =", rest)

    # 解包同时用于函数调用：* 拆可迭代给位置参数
    def add(p, q):
        return p + q
    print("add(*[2,3]) =", add(*[2, 3]))


# ============================================================
# 二、*args：接收任意个位置参数
# ============================================================
def demo_args():
    print("\n" + "=" * 50)
    print("二、*args")
    print("=" * 50)

    # args 在函数内部是一个元组
    def summarize(*args):
        print("  收到", len(args), "个位置参数:", args)

    summarize(1, 2, 3)
    summarize("a", "b")

    # 常见：普通参数 + *args
    def log(level, *messages):
        print(f"  [{level}] 共{len(messages)}条:", messages)
    log("INFO", "启动", "加载中", "完成")

# ============================================================
# 三、**kwargs：接收任意个关键字参数
# ============================================================
def demo_kwargs():
    print("\n" + "=" * 50)
    print("三、**kwargs")
    print("=" * 50)

    # kwargs 在函数内部是一个字典
    def call_llm(model, **kwargs): # kwargs 是关键字参数的集合，类型为字典
        print(f"  调用 {model}")
        for k, v in kwargs.items():
            print(f"    {k} = {v}")

    # 这就是 LLM/LangChain 的典型调用形态
    call_llm("gpt-4", temperature=0.7, max_tokens=1024, stream=True)

    # **d 把字典解包成关键字参数
    config = {"temperature": 0.2, "max_tokens": 256}
    call_llm("gpt-4", **config)

# ============================================================
# 四、参数顺序规则（位置/默认/*/**）
# ============================================================
def demo_order():
    print("\n" + "=" * 50)
    print("四、参数定义顺序：普通→默认→*args→keyword-only→**kwargs")
    print("=" * 50)

    def f(a,b =10, *args,c,**kwargs):
        print(f"  a={a} b={b} c={c}")
        print(f"  args={args}")
        print(f"  kwargs={kwargs}")

    # c 是仅关键字参数（在 *args 之后），调用时必须写 c=...
    f(1, 2, 3, 4, c=5, x=6, y=7)

# ============================================================
# 五、实战：合并配置字典（** 解包合并）
# ============================================================
def demo_merge():
    print("\n" + "=" * 50)
    print("五、实战：配置合并")
    print("=" * 50)

    default = {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1024}
    user_override = {"temperature": 0.2}

    # 用 ** 解包合并（后者覆盖前者），生成新字典不改原值
    final = {**default, **user_override}
    print("最终配置:", final)
    print("原 default 未变:", default["temperature"])

    # Python 3.9+ 也可用 d1 | d2
    print("用 | 合并:", default | user_override)


if __name__ == "__main__":
    # demo_unpack()
    # demo_args()
    # demo_kwargs()
    # demo_order()
    demo_merge()