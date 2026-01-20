from functools import cache
from pathlib import Path

from openai import OpenAI

from quick_one_liner_lookup.settings import CLOUD_MODEL, LOCAL_MODEL, OLLAMA_BASE_URL, check_use_cloud


@cache
def create_open_ai_instance() -> OpenAI:
    if check_use_cloud():
        return OpenAI()
    else:
        return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


def get_dataset_location() -> Path:
    return Path(__file__).parent / "dataset.json"


@cache
def get_current_model() -> str:
    if check_use_cloud():
        return CLOUD_MODEL
    else:
        return LOCAL_MODEL
