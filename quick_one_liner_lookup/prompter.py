from pathlib import Path
import re
import time
from openai import OpenAI

from quick_one_liner_lookup.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from quick_one_liner_lookup.settings import CLOUD_MODEL, LOCAL_MODEL, OLLAMA_BASE_URL, check_use_cloud, is_debug_mode_active
from quick_one_liner_lookup.utils import create_open_ai_instance


def postprocessing(command: str) -> str:
    REGEX_PATTERN = r"(```|`)?(bash\n)?(?P<command>[^`]*)(```|`)?"

    command = command.strip()
    regex = re.compile(REGEX_PATTERN, re.DOTALL)
    matches = list(regex.finditer(command))
    if not matches:
        return command.strip()

    for m in matches:
        cmd = m.groupdict().get("command")
        if cmd:
            return cmd.strip()

    return command


def prompt(
    command_description: str,
    log: bool = True,
) -> str:
    open_ai = create_open_ai_instance()
    user_prompt = USER_PROMPT_TEMPLATE.format(command_description)

    if not check_use_cloud():
        response = open_ai.chat.completions.create(
            model=LOCAL_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    else:
        response = open_ai.chat.completions.create(
            model=CLOUD_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            reasoning_effort="low",
        )

    raw_command = response.choices[0].message.content

    if is_debug_mode_active():
        print(raw_command)

    command = postprocessing(raw_command)

    # Log description result pairs
    if log:
        log_file = Path(__file__).parent / "prompt_answer_pairs.csv"
        with open(log_file, "a") as f:
            f.write(f"\n{command_description},{command}")

    return command
