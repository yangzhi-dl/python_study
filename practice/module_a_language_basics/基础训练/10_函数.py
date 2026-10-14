#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 10_函数.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】函数定义、参数、默认值、返回值、关键字实参。参考答案见 10_函数_demo.py
"""

# 在本文件手敲练习，卡住时对照 10_函数_demo.py
# ============================================================
# 一、定义与返回值
# ============================================================
def greet(name):
    """一个带 docstring 的简单函数。"""
    return f"你好，{name}！"


def demo_return():
    print("=" * 50)
    print("一、定义与返回值")
    print("=" * 50)

    print(greet("张三"))
    # 没有 return 的函数默认返回 None
    result = print  # 仅示意
    # 多返回值：其实是返回一个元组，可解包接收
    def min_max(nums):
        return min(nums), max(nums)
    lo, hi = min_max([3, 1, 4, 1, 5])
    print("多返回值解包 -> 最小:", lo, "最大:", hi)


# ============================================================
# 二、参数：位置 / 默认值 / 关键字实参
# ============================================================
def call_llm(model, temperature=0.7, max_tokens=1024, stream=False):
    """带默认值的参数：调用时可省略，也可按需覆盖。"""
    return (f"调用 model={model} temperature={temperature} "
            f"max_tokens={max_tokens} stream={stream}")


def demo_params():
    print("\n" + "=" * 50)
    print("二、参数与默认值")
    print("=" * 50)

    # 1. 全用默认值
    print(call_llm("gpt-4"))
    # 2. 位置实参（按定义顺序传）
    print(call_llm("gpt-4", 0.2))
    # 3. 关键字实参（★ LLM/库调用最常见）：顺序无关、可读性高
    print(call_llm(model="gpt-4", stream=True, temperature=0.9))

# ============================================================
# 三、默认值规则与坑
# ============================================================
def demo_default_pitfall():
    print("\n" + "=" * 50)
    print("三、默认值坑（详见 13_可变对象陷阱）")
    print("=" * 50)

    # 默认参数必须是"不可变"值；用可变对象(列表/dict)做默认值会跨调用共享！
    # ❌ 错误示范
    def bad(item, bucket=[]):
        bucket.append(item)
        return bucket
    print("错误 bad(1):", bad(1))
    print("错误 bad(2):", bad(2), "  # 竟带着上次的 1！")

    # ✅ 正确：默认 None，函数内再新建
    def good(item, bucket=None):
        if bucket is None:
            bucket = []
        bucket.append(item)
        return bucket
    print("正确 good(1):", good(1))
    print("正确 good(2):", good(2))


# ============================================================
# 四、仅位置 / 仅关键字参数（进阶）
# ============================================================
def create(name, /, model, *, temperature=0.7):
    """name 只能按位置传；model 及之后可按关键字；* 之后强制关键字。"""
    return f"name={name} model={model} temperature={temperature}"


def demo_special():
    print("\n" + "=" * 50)
    print("四、仅位置/仅关键字")
    print("=" * 50)

    # name 在 / 前 -> 必须位置传；temperature 在 * 后 -> 必须关键字传
    print(create("我的Agent", model="gpt-4", temperature=0.3))
    # create(name="x", ...) 会报错，因为 name 是仅位置参数

# ============================================================
# 五、实战：封装一个可复用的 prompt 构造函数
# ============================================================
def build_prompt(system, user_input, *, lang="中文", tone="友好"):
    """把参数拼成一段 prompt，演示关键字参数 + 默认值 + f-string。"""
    return (
        f"[system] 你是助手，用{lang}、以{tone}语气回答。\n"
        f"[user] {user_input}"
    )


def demo_real():
    print("\n" + "=" * 50)
    print("五、实战：构造 prompt")
    print("=" * 50)
    print(build_prompt("你是助手", "解释一下函数"))
    print("-" * 30)
    print(build_prompt("你是助手", "解释一下函数", lang="英文", tone="正式"))




if __name__ == "__main__":
    # demo_return()
    # demo_params()
    # demo_default_pitfall()
    # demo_special()
    demo_real()
