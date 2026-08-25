@echo off
:: Career Tracker 停止服务脚本
taskkill /F /FI "WINDOWTITLE eq CareerTrackerDaemon*" /T >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo Career Tracker 服务已停止。
