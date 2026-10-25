#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : config.py
@Author  : yz.yangzhi
@Date    : 2026/10/21 21:29
@Desc    : 
"""
import os
from pathlib import Path
from traceback import print_tb

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


# 加载 .env（路径基于当前文件位置，避免换目录就失效）
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "")
MODEL_CODE = os.getenv("MODEL_CODE", "")

if not DASHSCOPE_API_KEY:
    raise RuntimeError(".env 中缺少 DASHSCOPE_API_KEY")

if not BASE_URL:
    raise RuntimeError(".env 中缺少 BASE_URL")

if not MODEL_CODE:
    raise RuntimeError(".env 中缺少 MODEL_CODE")

MODEL = ChatOpenAI(
    model=MODEL_CODE,
    api_key=DASHSCOPE_API_KEY,
    base_url=BASE_URL,
)




# if __name__ == "__main__":
#     print(BASE_URL)
#     print(DASHSCOPE_API_KEY)
#     print(MODEL_CODE)