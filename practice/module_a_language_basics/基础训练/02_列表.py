#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : 02_列表.py
@Author  : yz.yangzhi
@Date    : 2026/10/13 20:01
@Desc    : 
"""

def list_crud():
    print("=" * 50)
    print("一、增删改查")
    print("=" * 50)

    # ---- 创建 ----
    fruits = ["apple", "banana", "cherry"]#下标从0开始
    empty1 = []                # 空列表
    empty2 = list()            # 等价写法
    nums = list(range(1, 6))  # [1, 2, 3, 4, 5]
    print("原始列表:", fruits)
    print("空列表:", empty1, empty2, "| 数字:", nums)

    fruits.append("orange")
    fruits.insert(1,"grape")
    fruits.extend(["pear", "peach"])
    print("增之后:", fruits)

    # ---- 查（读取/查找/是否存在）----
    print("第一个:", fruits[0], "| 最后一个:", fruits[-1])
    print("切片[1:3]:", fruits[1:3])  # 从下标1到下标3，不包括下标3
    if "banana" in fruits:
        print("banana 的下标:", fruits.index("banana"))
    print("apple 出现次数:", fruits.count("apple"))

    # ---- 改（替换/批量修改）----
    fruits[0] = "APPLE"                          # 按下标改单个
    print("改之后:", fruits)

    # 批量修改：每个元素转小写（推荐用列表推导式生成新列表）
    lower = [f.lower() for f in fruits]
    print("批量转小写:", lower)

    # ---- 删 ----
    fruits.remove("APPLE")       # 按值删除（删第一个匹配的，不存在会报错）
    popped = fruits.pop()        # 删除并返回最后一个元素
    del fruits[0]                # 按下标删除，不返回值
    print("删除后剩余:", fruits, "| pop 拿到的:", popped)

    fruits.clear()               # 清空列表
    print("清空后:", fruits)

def list_sort():
    print("\n" + "=" * 50)
    print("二、排序")
    print("=" * 50)

    nums = [3, 1, 4, 1, 5, 9, 2, 6]
    # sorted() 返回新列表，原列表不变（非破坏性）
    asc = sorted(nums)
    print("sorted 升序:", asc, "| 原列表未变:", nums)

    # list.sort() 原地排序，改变原列表，返回 None
    nums.sort()
    print("sort 原地升序:", nums)

    # 降序
    nums.sort(reverse=True)
    print("降序:", nums)

    # 按 key 排序：字符串按长度
    words = ["pear", "fig", "banana", "apple"]
    by_len = sorted(words,key=len)
    print("按长度排序:", by_len)

    # 自定义 key + 多条件排序：先按长度，再按字母
    multi = sorted(words, key=lambda w: (len(w), w))
    print("多条件(长度→字母):", multi)

    # 对象/字典列表按某字段排序
    users = [{"name": "Tom", "age": 30},
             {"name": "Amy", "age": 25},
             {"name": "Bob", "age": 35}]
    by_age = sorted(users,key=lambda u:u["age"])
    print(f"{users[0]['name']}({users[0]['age']})") # Tom(30)
    print("按年龄排序:", [f"{u['name']}({u['age']})" for u in by_age])

    # ============================================================
    # 三、实战：消息列表（LLM messages 常见结构）
    # ============================================================
def demo_message_list():
    print("\n" + "=" * 50)
    print("三、消息列表 messages")
    print("=" * 50)
    # 1. 初始化：系统提示 + 用户首轮输入
    # messages 是一个列表，里面每一项是字典
    messages = [
        {"role": "system", "content": "你是一个乐于助人的助手。"},
        {"role": "user", "content": "你好，介绍一下 Python 的列表。?"}
    ]

    # 2. 追加对话轮次（模拟多轮）
    messages.append({"role": "assistant", "content": "列表是 Python 的有序可变集合……"})
    messages.append({"role": "user", "content": "那它和元组有什么区别？"})

    print(f"当前共有{len(messages)}条消息")
    for i,msg in enumerate(messages): # enumerate 是一个函数，返回索引和值
        print(f"  [{i}] {msg['role']:<9}: {msg['content']}") #
        """
        `[{i}]`：打印消息序号，比如 `[0]`、`[1]`
        `msg['role']`：取出字典的 role 值（system /user）
        `:<9` 格式化：**左对齐，占 9 个字符宽度**，保证后面冒号整齐对齐
        `msg['content']`：取出消息内容
        """
    # 4. 修改：修正最后一条用户输入（拼 prompt 时常见）
    messages[-1]["content"] += "（请用一句话回答）"
    print("修改最后一条 ->", messages[-1]["content"])

    # 5. 删除：去掉某条 / 撤回上一轮
    messages.pop()                     # 删最后一条
    # messages.remove(target_msg)      # 也可按对象删除
    print("撤回一轮后剩:", len(messages), "条")

    # 6. 取最近 N 条历史（滑动窗口，控制上下文长度）
    recent = messages[-2:]
    print("最近 2 条角色:", [m["role"] for m in recent])

def demo_tool_list():
    print("\n" + "=" * 50)
    print("四、工具列表 tools")
    print("=" * 50)

    # 1. 声明可用工具
    tools = [
        {
            "name": "get_weather",
            "description": "查询指定城市天气",
            "parameters": {"city": "str"},
        },
        {
            "name": "search_web",
            "description": "联网搜索关键词",
            "parameters": {"query": "str"},
        },
    ]

    # 2. 注册新工具（增）
    tools.append({
        "name": "send_email",
        "description": "发送邮件",
        "parameters": {"to": "str", "subject": "str"},
    })
    print(f"已注册{len(tools)}个工具,{[t['name'] for t in tools]}")

    # 3. 查找某个工具（查）—— 用 next + 生成器取第一个匹配
    target  = next((t for t in tools if t["name"] == "search_web"), None) #在 tools 里面查找第一个 name=="search_web" 的字典，找到就返回这个字典；找不到返回 None。
    print("找到工具:", target["description"] if target else "未找到")

    # 4. 按名称排序（稳定输出）
    tools.sort(key=lambda t: t["name"])
    print("按名称排序:", [t["name"] for t in tools])

    # 5. 注销工具（删）—— 列表推导式生成"保留项"，比循环 remove 更安全
    name_to_remove = "send_email"
    # tools = [t for t in tools if t["name"] != name_to_remove] #列表推导式 用来删除某个列表元素
    tools[:] = [t for t in tools if t["name"] != name_to_remove] #简洁原地 API
    print(f"注销 {name_to_remove} 后:", [t["name"] for t in tools])

    # 6. 修改工具描述（改）
    tools[0]["description"] += "（免费版，仅支持国内城市）"
    print("更新描述:", tools[0]["description"])



if __name__== "__main__":
    # list_crud()  # 列表的CRUD
    # list_sort()  # 列表的排序
    # demo_message_list() # 消息列表
    demo_tool_list()