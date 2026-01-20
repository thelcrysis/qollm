import sys
import subprocess
import time
from subprocess import Popen, PIPE

from quick_one_liner_lookup.prompter import prompt
from quick_one_liner_lookup.settings import check_use_cloud


command_description = " ".join(sys.argv[1:])
# Use the generate function for a one-off prompt

start_time = time.time()

command = prompt(command_description=command_description)
print(command)
print(f"[Finished in {time.time() - start_time:.2f}s with{"out" if not check_use_cloud() else ""} using cloud]")
print("\n[ENTER] Run, [c] Copy, [Ctrl+C] Exit?", end=" ")


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
