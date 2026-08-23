import subprocess
import os

try:
    res = subprocess.run(["python", "career-tracker/scripts/inspect_sa_companies.py"], capture_output=True, text=True, check=True)
    with open("career-tracker/scripts/inspect_output.txt", "w", encoding="utf-8") as f:
        f.write(res.stdout)
except Exception as e:
    with open("career-tracker/scripts/inspect_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {e}\nStderr: {getattr(e, 'stderr', '')}")
