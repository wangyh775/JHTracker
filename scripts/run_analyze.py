import subprocess
import sys

res = subprocess.run([sys.executable, "career-tracker/scripts/analyze_candidates.py"], capture_output=True, text=True, encoding="utf-8")
print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
