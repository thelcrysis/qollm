import os
from pathlib import Path
import sys
import subprocess
import time
from openai import OpenAI
from subprocess import Popen, PIPE
from dotenv import load_dotenv

from quick_one_liner_lookup.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

OLLAMA_BASE_URL = "http://localhost:11434/v1"
LOCAL_MODEL = "qwen2.5-coder:7b"
CLOUD_MODEL = "gpt-5-nano"


def postprocessing(command: str):
    BACKTICK = "`"
    TRIPLE_BACKTICK = "```"
    command = command.strip()
    if command[0:3] == TRIPLE_BACKTICK and command[-3:] == TRIPLE_BACKTICK:
        command = command[3:-3]
    if command[0] == BACKTICK and command[-1] == BACKTICK:
        command = command[1:-1]
    return command.strip()


load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")
use_cloud = False
if os.getenv("OPENAI_API_KEY") is not None and os.getenv("RICH") == "True":
    use_cloud = True


command_description = " ".join(sys.argv[1:])
# Use the generate function for a one-off prompt

user_prompt = USER_PROMPT_TEMPLATE.format(command_description)


if use_cloud:
    open_ai = OpenAI()
else:
    open_ai = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

start_time = time.time()
if not use_cloud:
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

command = postprocessing(response.choices[0].message.content)

print(command)
print(f"[Finished in {time.time() - start_time:.2f}s with{"out" if not use_cloud else ""} using cloud]")
print("\n[ENTER] Run, [c] Copy, [Ctrl+C] Exit?", end=" ")
# Log description result pairs
log_file = Path(__file__).parent / "prompt_answer_pairs.csv"
with open(log_file, "a") as f:
    f.write(f"\n{command_description},{command}")


try:
    option = input()
except KeyboardInterrupt:
    exit()
if option == "c":
    p = Popen(["xsel", "-bi"], stdin=PIPE)
    p.communicate(input=bytes(command, "utf-8"))
    exit()

print(80 * "-")
print(command)
subprocess.run(command, shell=True)
