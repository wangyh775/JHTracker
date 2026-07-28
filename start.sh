#!/bin/bash
cd "$(dirname "$0")"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "[初始化] 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "[安装依赖] ..."
pip install -r requirements.txt -q

mkdir -p data/resumes

echo "[启动] JHTracker http://127.0.0.1:5000"
python app.py
