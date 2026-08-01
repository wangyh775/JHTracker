#!/usr/bin/env python3
"""
⚠️ DEPRECATED / 已废弃 ⚠️
----------------------------------------------------------------------
该脚本已废弃。新版本的自动化公司发现已全权交由 Agent + Skill
(skills/job-sourcing-and-scoring) + MCP 检索工具 (Exa/Firecrawl/Playwright) 动态执行。

请勿直接运行此脚本！
----------------------------------------------------------------------
"""
import os
import sys

# 把当前项目目录加进 PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from scripts.fetch_and_import import cmd_import

def main():
    print("[DEPRECATED] daily_new_company_finder.py 已废弃！")
    print("请使用 Agent 唤醒 Skill (job-sourcing-and-scoring) 执行真实网络检索。")
    sys.exit(0)

if __name__ == '__main__':
    main()
