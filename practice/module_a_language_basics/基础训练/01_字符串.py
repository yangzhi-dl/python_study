

# str1 = '''
# sdfasfasdfasdfsadfsafdasdfas
# '''
#
# print(str1)
# print(str1 + '1a')

role = 'AI助手'
user_input = 'HelloWorld'

prompt = f"你是一个{role}，请把下面内容翻译成中文：{user_input}"
print(prompt)

def build_translate_prompt(text: str, target_lang: str) -> str:
    return f"""你是一个专业翻译。
规则：
1. 只输出译文，不要解释
2. 目标语言：{target_lang}

待翻译内容：
\"\"\"{text}\"\"\"
"""
print(build_translate_prompt('HelloWorld', '中文'))


