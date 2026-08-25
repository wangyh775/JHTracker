@echo off
:: Career Tracker 静默后台启动器 (绝对路径防丢)
cd /d "D:\DJTU\HermesWorkspace\career-tracker"
start "" "D:\DJTU\HermesWorkspace\career-tracker\.venv\Scripts\pythonw.exe" "backend\run_daemon.py"
