from functools import cache
import os

from dotenv import load_dotenv


OLLAMA_BASE_URL = "http://localhost:11434/v1"
LOCAL_MODEL = "qwen2.5-coder:7b"
CLOUD_MODEL = "gpt-5-nano"


@cache
def get_open_ai_key() -> str | None:
    load_dotenv(override=True)
    return os.getenv("OPENAI_API_KEY")


@cache
def check_use_cloud() -> bool:
    if get_open_ai_key is not None and os.getenv("RICH") == "True":
        return True
    return False


@cache
def is_debug_mode_active() -> bool:
    return os.getenv("DEBUG") == "True"
