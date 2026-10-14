#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 09_内置函数.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】any/all/sum/sorted(key=...)。参考答案见 09_内置函数_demo.py
"""

# 在本文件手敲练习，卡住时对照 09_内置函数_demo.py
# ============================================================
# 一、sum / min / max / len：聚合
# ============================================================
def demo_agg():
    print("=" * 50)
    print("一、sum / min / max / len")
    print("=" * 50)

    nums = [3, 1, 4, 1, 5, 9, 2, 6]
    print("总和 sum:", sum(nums))
    print("最小 min:", min(nums), "| 最大 max:", max(nums), "| 个数 len:", len(nums))

    # sum 可指定起始值；对空列表 sum 返回 0（很安全）
    print("空列表 sum:", sum([]))
    print("从100开始累加:", sum(nums, start=100))

    # 配合生成器表达式：只加偶数
    print("偶数之和:", sum(x for x in nums if x % 2 == 0))


# ============================================================
# 二、any / all：存在性 & 全满足判断
# ============================================================
def demo_any_all():
    print("\n" + "=" * 50)
    print("二、any / all")
    print("=" * 50)

    # any：只要有一个为真就 True（"是否存在"）
    scores = [55, 72, 88, 49]
    print("有不及格的吗 any(<60):", any(s < 60 for s in scores))

    # all：全部为真才 True（"是否都满足"）
    print("全部及格吗 all(>=60):", all(s >= 60 for s in scores))

    # 实战：校验必填参数是否都齐
    params = {"city": "北京", "date": ""}
    required = ["city", "date"]
    ok = all(params.get(k) for k in required)   # 空字符串是 falsy
    print("必填齐全吗:", ok)

    # 空集合的边界：any([]) 为 False，all([]) 为 True
    print("any([]) =", any([]), "| all([]) =", all([]))

# ============================================================
# 三、sorted / max / min 的 key 参数
# ============================================================
def demo_key():
    print("\n" + "=" * 50)
    print("三、sorted(key=...)")
    print("=" * 50)


    words = ["banana", "fig", "apple", "kiwi"]

    # 按长度排序（key 传入一个"取比较依据"的函数）
    print("按长度:", sorted(words, key=len))
    print("按长度降序:", sorted(words, key=len, reverse=True))

    # 字典列表按某字段排序
    users = [{"name": "Tom", "age": 30}, {"name": "Amy", "age": 25}]
    by_age = sorted(users, key=lambda u: u["age"])
    print("按年龄:", [u["name"] for u in by_age])

    # max/min 也支持 key
    longest = max(words, key=len)
    print("最长的单词:", longest)

    # 多条件：先按长度、再按字母
    print("多条件:", sorted(words, key=lambda w: (len(w), w)))


# ============================================================
# 四、其他常用：round / abs / divmod / enumerate 回顾
# ============================================================
def demo_misc():
    print("\n" + "=" * 50)
    print("四、其他常用内置函数")
    print("=" * 50)

    print("绝对值 abs(-5):", abs(-5))
    print("四舍五入 round(3.14159, 2):", round(3.14159, 2))
    print("整除余数 divmod(17, 5):", divmod(17, 5))   # (商, 余) = (3, 2)

    # bool 是 int 子类：True=1 False=0，可用 sum 统计条件成立数
    flags = [True, False, True, True]
    print("真值个数 sum(flags):", sum(flags))

    # reversed 反转迭代
    print("反转:", list(reversed([1, 2, 3])))




if __name__ == "__main__":
    # demo_agg()
    # demo_any_all()
    # demo_key()
    demo_misc()