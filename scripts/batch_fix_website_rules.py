import sqlite3
import re
import requests
from urllib.parse import urlparse

db_path = r"D:\DJTU\HermesWorkspace\career-tracker\data\tracker.db"

KNOWN_MAP = {
    '海康威视': 'https://campushr.hikvision.com',
    '科大讯飞': 'https://www.iflytek.com',
    '中控技术': 'https://www.supcon.com',
    '信捷电气': 'https://www.xinje.com',
    '维宏股份': 'https://www.weihong.com.cn',
    '华中数控': 'https://www.huazhongcnc.com',
    '科德数控': 'https://www.dlkede.com',
    '广州数控': 'https://www.gsk.com.cn',
    '拓斯达': 'https://www.topstarltd.com',
    '埃夫特': 'https://www.efort.com.cn',
    '新松机器人': 'https://www.siasun.com',
    '中科新松': 'https://www.siasun-robot.com',
    '极智嘉': 'https://www.geekplus.com',
    '海柔创新': 'https://www.hairobotics.com',
    '快仓智能': 'https://www.quicktron.com',
    '比亚迪': 'https://job.byd.com',
    '联影医疗': 'https://www.united-imaging.com',
    '迈瑞医疗': 'https://careers.mindray.com',
    '西门子': 'https://careers.siemens.com/global/en/campus-china',
    '施耐德电气': 'https://www.se.com/cn/zh/about-us/careers/',
    'ABB': 'https://careers.abb/global/en',
    '和利时': 'https://www.hollysys.com',
    '台达': 'https://www.delta-china.com.cn',
    '菲尼克斯': 'https://www.phoenixcontact.com/zh-cn/',
    '罗克韦尔': 'https://www.rockwellautomation.com/zh-cn.html',
    '欧姆龙': 'https://www.fa.omron.com.cn',
    '安川电机': 'https://yaskawa.com.cn',
    '大族激光': 'https://www.hanslaser.com',
    '华工科技': 'https://www.hgtech.com.cn',
    '新时达': 'https://www.stepelectric.com',
    '禾川科技': 'https://www.hc-system.com',
    '伟创电气': 'https://www.veichi.com',
    '英威腾': 'https://www.invt.com.cn',
    '蓝海华腾': 'https://www.vtdrive.com',
    '雷赛智能': 'https://www.leisai.com/recruitment/index.html',
    '固高科技': 'https://www.googoltech.com.cn',
    '科瓦斯': 'https://www.ecovacs.com/cn',
    '石头科技': 'https://www.roborock.com',
    '追觅科技': 'https://www.dreame.tech',
    '宇树科技': 'https://www.unitree.com',
    '先临三维': 'https://www.shining3d.cn',
    '华曙高科': 'https://www.farsoon.com',
    '铂力特': 'https://www.blt3d.com',
    '中微半导体': 'https://www.amec-inc.com',
    '北方华创': 'https://www.naura.com',
    '先导智能': 'https://www.leadintelligent.com',
}

def normalize_name(name):
    name = re.sub(r'[（(][^）)]*[）)]', '', name).strip()
    name = name.replace('股份', '').replace('有限', '').replace('公司', '').replace('科技', '').replace('集团', '').strip()
    return name

def run():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, name FROM companies WHERE website LIKE '%zhipin%'")
    rows = c.fetchall()
    
    updated = 0
    for row in rows:
        cid, name = row
        norm_name = normalize_name(name)
        
        match_url = None
        for k, v in KNOWN_MAP.items():
            if k in name or k in norm_name:
                match_url = v
                break
                
        if match_url:
            c.execute("UPDATE companies SET website = ? WHERE id = ?", (match_url, cid))
            updated += 1
            print(f"✅ {name[:15]:15s} -> {match_url}")
            
    conn.commit()
    print(f"\nPhase 1 Rule Engine: Updated {updated} companies out of {len(rows)}")
    conn.close()

if __name__ == '__main__':
    run()