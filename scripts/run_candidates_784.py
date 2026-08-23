import subprocess
import sys

res = subprocess.run([r"C:\Users\29006\AppData\Local\Programs\Python\Python311\python.exe", "career-tracker/scripts/find_candidates_784.py"], capture_output=True, text=True, encoding="utf-8")
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
