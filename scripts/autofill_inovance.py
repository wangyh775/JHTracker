import json
import time
import os
import re
from playwright.sync_api import sync_playwright

def load_profile():
    profile_path = os.path.join(os.path.dirname(__file__), "..", "data", "applicant_profile.json")
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def fill_element_safely(page_or_frame, profile):
    b = profile.get("basic_info", {})
    e_master = profile.get("education", [{}])[0]
    p_auto = profile.get("projects", {}).get("automation", [{}])[0]

    mapping_rules = [
        # (关键字正则, 待填入的值, 字段名称描述)
        (r"姓\s*名|真实姓名|candidate_name|name", b.get("name", "王云鹤"), "姓名"),
        (r"手\s*机|联系电话|phone|mobile", b.get("phone", "13000000000"), "手机号"),
        (r"邮\s*箱|电子邮箱|email|mail", b.get("email", "wangyh775@163.com"), "邮箱"),
        (r"学校|毕业院校|就读院校|school", e_master.get("school", "大连交通大学"), "硕士院校"),
        (r"专\s*业|所学专业|major", e_master.get("major", "机械工程"), "硕士专业"),
        (r"绩点|GPA|gpa|成绩", e_master.get("score", "85.44"), "硕士成绩"),
        (r"期望城市|意向城市|地点|city", b.get("target_city", "苏州/深圳/上海/杭州"), "意向城市"),
        (r"项目名称|课题名称", p_auto.get("name", "大型高温FDM 3D打印设备分布式控制系统研发"), "项目名称"),
        (r"项目职责|担任角色|职务", p_auto.get("role", "课题负责人"), "项目角色"),
        (r"项目描述|项目经历|科研经历", p_auto.get("description", ""), "项目描述"),
        (r"自我评价|自我介绍|个人总结", "大连交通大学机械硕士(2027届)，具备500mm高温FDM整机结构设计、EPLAN电气规划及MPC/EKF控制算法落地经验；发表EI论文1篇，申请发明专利1项，获国家一等奖。", "自我评价")
    ]

    # 获取当前上下文下的所有 input 和 textarea
    inputs = page_or_frame.query_selector_all("input:not([type=hidden]):not([type=file]):not([type=submit]):not([type=button]), textarea")
    
    filled = 0
    for el in inputs:
        try:
            if not el.is_visible():
                continue
            
            # 提取自身及关联上下文
            placeholder = el.get_attribute("placeholder") or ""
            name_attr = el.get_attribute("name") or ""
            id_attr = el.get_attribute("id") or ""
            aria_label = el.get_attribute("aria-label") or ""
            
            # 寻找 Vue / Element-UI 的关联 label
            label_text = ""
            parent = el.evaluate_handle("node => node.closest('.el-form-item, .form-item, .ant-form-item, div, li, tr')")
            if parent and parent.as_element():
                label_text = parent.as_element().inner_text()
            
            combined = f"{placeholder} {name_attr} {id_attr} {aria_label} {label_text}".lower().strip()
            
            # 匹配对应的值
            for pattern, val, desc in mapping_rules:
                if re.search(pattern, combined, re.I):
                    curr = el.input_value()
                    # 只在为空时填入，避免覆盖已有数据
                    if not curr.strip():
                        el.fill(str(val))
                        # 触发 Vue 的 input 和 change 事件以保证数据双向绑定生效
                        el.dispatch_event("input")
                        el.dispatch_event("change")
                        print(f"  ✅ [已安全填入] {desc} -> {str(val)[:25]}...")
                        filled += 1
                    break
        except Exception as e:
            continue
            
    return filled

def autofill_inovance_system():
    profile = load_profile()
    print("🔌 正在连接 Chrome (CDP: 9222)...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            page = browser.contexts[0].pages[-1]
            print(f"📄 当前页面: 《{page.title()}》")
            print(f"🔗 链接: {page.url}")
            
            # 等待 DOM 和 Vue 挂载完成
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.5)
            
            total_filled = 0
            
            # 1. 扫描主页面
            print("🔍 正在扫描主页面表单...")
            total_filled += fill_element_safely(page, profile)
            
            # 2. 递归扫描所有 iframe
            if page.frames:
                for idx, frame in enumerate(page.frames):
                    if frame != page.main_frame:
                        print(f"🔍 正在扫描内嵌子框架 iframe [{idx+1}]...")
                        total_filled += fill_element_safely(frame, profile)
            
            print(f"\n🎉 汇川网申表单安全预填完成！共填入 {total_filled} 个字段。")
            print("🛡️ 【绝对安全保证】：未触发任何‘提交’、‘下一步’或‘保存’动作，请在浏览器中查看效果！")
            
        except Exception as e:
            print(f"❌ 填表异常: {e}")

if __name__ == "__main__":
    autofill_inovance_system()
