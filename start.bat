@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist venv (
    echo [初始化] 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [安装依赖] ...
pip install -r requirements.txt -q

if not exist data mkdir data
if not exist data\resumes mkdir data\resumes

echo [启动] JHTracker http://127.0.0.1:5000
python app.py
pause
