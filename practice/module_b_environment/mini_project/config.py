import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env（路径基于当前文件位置，避免换目录就失效）
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

API_KEY: str = os.getenv("API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4")
BASE_URL: str = os.getenv("BASE_URL", "")


if __name__ == "__main__":
    print(f"API_KEY = {API_KEY}")
    print(f"MODEL_NAME = {MODEL_NAME}")
    print(f"BASE_URL = {BASE_URL}")