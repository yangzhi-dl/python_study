#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 03_字典.py
@Author  : yz.yangzhi
@Date    : 2026-10-13 22:10
@Desc    : 【手写练习】dict 取值、.get()、遍历。参考答案见 03_字典_demo.py
"""
from dateutil.utils import today


# 在本文件手敲练习，卡住时对照 03_字典_demo.py
def demo_crud():
    print("=" * 50)
    print("一、字典增删改查")
    print("=" * 50)
    # ---- 创建 ----
    # 字面量（最常用）
    user = {"name": "张三", "age": 25}
    # dict() 关键字方式（键必须是合法标识符）
    user2 = dict(name="李四", age=30)
    # 空字典
    empty = {}
    # 从键值对列表构造
    pairs = [("a", 1), ("b", 2)]
    d = dict(pairs)
    print("字面量:", user, "| dict():", user2, "| 空:", empty, "| 构造:", d)

    # ---- 查（取值）----
    print("name ->", user["name"])          # 键不存在会抛 KeyError

    # 安全取值：键不存在时返回默认值，不报错（推荐）
    print("存在  ->", user.get("age"))       # 25
    print("不存在->", user.get("email"))            # 返回 None
    print("带默认->", user.get("email", "未填写"))  # 返回 "未填写"

    # 判断键是否存在
    print("'name' in user:", "name" in user)
    print("'email' in user:", "email" in user)

    # ---- 增 / 改（同一个语法：键存在则改，不存在则增）----
    user["age"] = 26                 # 键已存在 -> 修改
    user["city"] = "上海"            # 键不存在 -> 新增
    print("增改之后:", user)

    # 批量更新（合并另一个字典）
    user.update({"level": "VIP", "age": 27})
    print("update 之后:", user)

    # setdefault：键不存在才设默认值（存在则不覆盖）
    user.setdefault("city", "北京")  # city 已存在，保持不变  还是上海
    user.setdefault("phone", "无")   # phone 不存在，新增
    print("setdefault 之后:", user)

    # ---- 删 ----
    del user["phone"]                # 按键删除（键不存在会报错）
    removed = user.pop("level")      # 删除并返回被删的值
    print("删 level 拿到:", removed, "| 剩余:", user)

    # user.clear()                   # 清空整个字典（需要时再放开）


# ============================================================
# 二、遍历
# ============================================================

def demo_iterate():
    print("\n" + "=" * 50)
    print("二、遍历")
    print("=" * 50)

    config = {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1024}

    # 遍历键（默认就是遍历键）
    for key in config:
        print("  key:", key)

    # 遍历值
    for value in config.values():
        print("  value:", value)

    # 同时遍历键和值（最常用）—— items() 返回 (key, value) 元组
    for k, v in config.items():
        print(f"  {k} = {v}")

    # 遍历键并排序输出
    for k in sorted(config):
        print("  排序键:", k)

# ============================================================
# 三、实战：Agent 状态（state）
# ============================================================
def demo_state():
    print("\n" + "=" * 50)
    print("三、实战：Agent 状态（state）")
    print("=" * 50)

    # LangGraph 里 state 常是一个 dict，字段用 .get 兜底避免 KeyError
    state = {
        "step": 1,
        "user_input": "帮我查天气",
        "tool_calls": [],          # 还没有工具调用
    }

    # 读取字段（对可能不存在的字段用 .get）
    print("当前步骤:", state.get("step"))
    print("错误信息:", state.get("error", "无"))   # error 还没出现，兜底

    # 更新状态（合并新字段）
    state.update({"step": 2, "tool_calls": ["get_weather"]})
    print("更新后:", state)


    # 统计字段数量
    print("字段数:", len(state), "| 所有键:", list(state.keys()))

# ============================================================
# 四、实战：工具参数 & API 返回解析
# ============================================================
def demo_api():
    print("\n" + "=" * 50)
    print("四、实战：工具参数 / API 返回解析")
    print("=" * 50)

    # 1. 工具调用参数（模型返回的 arguments 常是 dict）
    tool_args = {"city": "北京", "unit": "celsius"}
    # 用 ** 把字典解包成关键字参数传给函数（详见 解包.py）
    city = tool_args.get("city", "未知城市")
    # 2. 解析嵌套的 API 返回（层层 .get 安全取值）
    response = {
        "status": "ok",
        "data": {
            "weather": "晴",
            "temp": 22,
            "forecast": [
                {"day": "周一", "temp": 23},
                {"day": "周二", "temp": 20},
            ],
        },
    }
    # 安全地一层层往里取，任何一层缺失都不会崩
    temp = response.get("data",{}).get("temp", "N/A")
    today = response.get("data",{}).get("forecast", [{}])[0].get("day", "N/A")
    print(f"当前温度: {temp}°C | 预报首日: {today}")


    # 3. 判断请求是否成功
    if response.get("status") == "ok":
        print("请求成功，开始处理数据……")
    else:
        print("请求失败:", response.get("error", "未知错误"))


if __name__ == "__main__":
    # demo_crud()
    # demo_iterate()
    # demo_state()
    demo_api()