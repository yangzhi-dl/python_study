#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 06_循环.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】for/while、enumerate/zip/range。参考答案见 06_循环_demo.py
"""

# 在本文件手敲练习，卡住时对照 06_循环_demo.py
def demo_for_range():
    print("=" * 50)
    print("一、for + range")
    print("=" * 50)

    # range(起点, 终点, 步长)，含头不含尾
    for i in range(3):            # 0 1 2
        print("  i =", i)

    print("range(1,6):", list(range(1, 6)))       # [1,2,3,4,5]
    print("range(0,10,2):", list(range(0, 10, 2)))  # [0,2,4,6,8]
    print("倒序 range:", list(range(3, 0, -1)))      # [3,2,1]

    # 遍历列表
    fruits = ["apple", "banana", "cherry"]
    for f in fruits:
        print("  水果:", f)


# ============================================================
# 二、enumerate：带下标遍历
# ============================================================
def demo_enumerate():
    print("\n" + "=" * 50)
    print("二、enumerate")
    print("=" * 50)

    tasks = ["写代码", "测试", "部署"]

    # 反例（不推荐）：手动维护下标
    i = 0
    for t in tasks:
        print(f"  [{i}] {t}")
        i += 1

    # 正例：enumerate 自带下标，start 可指定起始值
    for idx, task in enumerate(tasks, start=1):
        print(f"  第{idx}项: {task}")

# ============================================================
# 三、zip：并行遍历多个序列
# ============================================================
def demo_zip():
    print("\n" + "=" * 50)
    print("三、zip")
    print("=" * 50)

    names = ["张三", "李四", "王五"]
    scores = [90, 85, 78]

    # 按下标配对，长度不一致时以短的为准
    for name, score in zip(names, scores):
        print(f"  {name}: {score}分") # 张三: 90分 ,zip 相当于把两个数组按照下标进行配对

    # zip 常用来把两个列表拼成字典
    d = dict(zip(names, scores))
    print("拼成字典:", d)

    # 错位演示：多的被丢弃
    print("长度不等:", list(zip([1, 2, 3], ["a"])))  # [(1, 'a')]



# ============================================================
# 四、while + break / continue / else
# ============================================================
def demo_while():
    print("\n" + "=" * 50)
    print("四、while 与控制流")
    print("=" * 50)

    # while：条件为真就一直循环
    countdown = 3
    while countdown > 0:
        print("  倒计时:", countdown)
        countdown -= 1
    print("  发射！")

   # break 提前退出整个循环
    for n in range(10):
        if n == 5:
            print("  找到 5，break")
            break

    # continue 跳过本次、进入下一次
    for n in range(5):
        if n%2 ==0:
            continue
        print(" 奇数：",n)
    # 循环的 else：循环"自然结束"(没被 break)才执行
    for n in range(5):
        if n == 99:
            break
    else:
        print("  全程没找到 99（else 执行）")

# ============================================================
# 五、实战：遍历消息历史
# ============================================================
def demo_messages():
    print("\n" + "=" * 50)
    print("五、实战：遍历 messages")
    print("=" * 50)

    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好呀"},
        {"role": "user", "content": "再见"},
    ]

    # 只打印用户消息，并带上有编号
    for i,m in enumerate(messages):
        if m["role"] == "user":
            print(f" [#{i}]用户说：{m['content']}")

    # 统计轮次
    user_turns = sum(1 for m in messages if m["role"] == "user")
    print(f"  用户共发言 {user_turns} 次")



if __name__ == '__main__':
    # demo_for_range()
    # demo_enumerate()
    # demo_zip()
    # demo_while()
    demo_messages()