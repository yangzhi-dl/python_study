from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def build_context(messages: list[dict],max_count:int = 3)-> str:
    """把最近几条消息拼成一段文本。"""
    recent = messages[-max_count:]
    lines=[]
    for m in recent:
        lines.append(f'{m["role"]}:{m["content"]}')
    return "\n".join(lines)



def count_by_role(messages:list[dict]) -> dict:
    """统计每种 role 出现多少次。"""
    counts: dict ={}
    for m in messages:
        role = m["role"]
        counts[role] = counts.get(role,0) + 1

    return counts

def load_prompt(name: str) -> str:
    """读取 prompts 目录下的提示词文件。"""
    path = PROMPTS_DIR / f"{name}.txt" #拼出来的目录/文件名.txt
    if not path.exists():
        raise FileNotFoundError(f"提示词文件不存在: {path}")
    return path.read_text(encoding="utf-8")


if __name__ == "__main__": #那个 if 存在的唯一目的，是防止你 import 一个文件时，它的测试代码跟着乱跑。【临时测试】
    print(">>> utils.py 正在被直接运行")
    demo = [{"role": "user", "content": "测试"}]
    print(build_context(demo))
    print("当前文件的绝对路径",__file__) #表示当前文件的绝对路径 C:\Users\Yandel\Desktop\Python学习\practice\module_b_environment\mini_project\utils.py
    print("当前文件所在的目录",Path(__file__).parent)  # 当前文件所在的父级目录  C:\Users\Yandel\Desktop\Python学习\practice\module_b_environment\mini_project
    print("拼出来的目录",PROMPTS_DIR)  # 拼出来的目录 C:\Users\Yandel\Desktop\Python学习\practice\module_b_environment\mini_project\prompts
    print(load_prompt("system")) #这个system  表示文件名