#!/usr/bin/env python3
"""
scripts/daily_new_company_finder.py — 每日自动发现新公司的脚本
该脚本模拟了搜索和发现秋招新公司的逻辑，并将结果通过 fetch_and_import 导入数据库。
"""
import os
import sys

# 把当前项目目录加进 PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from scripts.fetch_and_import import cmd_import

def main():
    print("开始查询已有公司及发现新公司...")
    # 这里我们定义一些今天发现的全新 2027 届秋招重点目标公司
    companies = [
        {
            "name": "跨维智能",
            "industry": "机器人",
            "sub_industry": "3D视觉与AI机器人",
            "city": "深圳",
            "job_type": "机器人/自动化控制工程师",
            "match_reason": "专注于3D视觉引导的工业机器人与AI算法落地，控制与视觉集成经验匹配",
            "website": "https://www.dexforce.com/"
        },
        {
            "name": "星尘智能（Astribot）",
            "industry": "机器人",
            "sub_industry": "AI机器人/具身智能",
            "city": "深圳",
            "job_type": "机器人/自动化控制工程师",
            "match_reason": "AI助理机器人研发，其S1产品展示出极高控制精度与速度，符合底层算法优化需求",
            "website": "https://www.astribot.com/"
        }
    ]
    
    print(f"发现了 {len(companies)} 家新公司，准备导入数据库。")
    cmd_import(companies, source_label="daily_finder_cron")
    print("\n运行完成！")

if __name__ == '__main__':
    main()
