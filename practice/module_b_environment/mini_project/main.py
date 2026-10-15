from config import API_KEY, MODEL_NAME
from utils import build_context, count_by_role, load_prompt

MESSAGES = [
    {"role": "system", "content": "你是一个不良品根因分析助手"},
    {"role": "user", "content": "3号产线昨天有5个批次不良"},
    {"role": "assistant", "content": "我先查一下工单记录"},
    {"role": "user", "content": "重点是昨天下午那批"},
]


def main() -> None:
    print("=" * 40)
    print(f"模型: {MODEL_NAME}")
    print(f"API Key 是否配置: {'是' if API_KEY else '否'}")
    print("=" * 40)

    print("\n[系统提示词]")
    print(load_prompt("system"))

    print("\n[消息统计]")
    print(count_by_role(MESSAGES))

    print("\n[上下文]")
    print(build_context(MESSAGES))


if __name__ == "__main__":#这里也用if的原因   main.py 会被 import，用if来保护，防止被 import 时执行
    main()

""" 【main中标准骨架】
模块说明：这个文件是干什么的

# 1. 导入
from config import MODEL_NAME
from utils import build_context

# 2. 常量（全大写）
MESSAGES = [...]

# 3. 函数定义
def main() -> None:
    主逻辑
    print(MODEL_NAME)
    ...

# 4. 入口（固定套路）
if __name__ == "__main__":
    main()
    
"""