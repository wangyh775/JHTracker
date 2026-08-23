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

# 扩展字典与正则映射规则
PATTERNS = {
    "name": [r"姓\s*名", r"真实姓名", r"候选人姓名", r"name", r"username", r"fullname"],
    "gender_male": [r"男", r"male"],
    "phone": [r"手\s*机", r"联系电话", r"移动电话", r"手机号", r"phone", r"mobile", r"tel"],
    "email": [r"邮\s*箱", r"电子邮箱", r"email", r"mail", r"e-mail"],
    "birth_year": [r"出生年份", r"出生年月", r"出生日期", r"生日", r"birth"],
    "political_status": [r"政治面貌", r"党派", r"political"],
    "target_city": [r"期望城市", r"意向城市", r"工作地点", r"期望工作地", r"target_city", r"location"],
    
    # 硕士
    "master_school": [r"硕士学校", r"研究生学校", r"最高学历学校", r"毕业院校", r"毕业学校", r"就读院校", r"学校名称", r"school", r"university"],
    "master_major": [r"硕士专业", r"研究生专业", r"专业名称", r"所学专业", r"专业", r"major"],
    "master_degree": [r"学历", r"最高学历", r"学位", r"degree", r"education"],
    "master_gpa": [r"绩点", r"GPA", r"平均分", r"gpa", r"成绩排名"],
    "start_date_master": [r"入学时间", r"入学年份", r"起止时间.*起", r"开始时间"],
    "end_date_master": [r"毕业时间", r"毕业年份", r"毕业届数", r"起止时间.*止", r"结束时间", r"预计毕业"],
    
    # 项目与综合
    "project_name": [r"项目名称", r"课题名称", r"project_name"],
    "project_role": [r"项目职务", r"担任角色", r"个人职责", r"role"],
    "project_desc": [r"项目描述", r"项目经历", r"科研经历", r"项目内容", r"项目介绍", r"课题介绍", r"project_desc", r"project_detail"],
    "awards_desc": [r"获奖情况", r"获奖经历", r"荣誉奖励", r"竞赛获奖", r"奖项", r"awards", r"honors"],
    "skills_desc": [r"技能特长", r"专业技能", r"掌握技能", r"IT技能", r"skills"],
    "self_evaluation": [r"自我评价", r"自我介绍", r"个人优势", r"总结", r"evaluation", r"self_intro", r"about_me"]
}

def match_field(text):
    text = text.lower().strip()
    for key, regex_list in PATTERNS.items():
        for reg in regex_list:
            if re.search(reg, text, re.I):
                return key
    return None

def get_value_for_key(key, profile):
    b = profile.get("basic_info", {})
    e_master = profile.get("education", [{}])[0]
    e_bachelor = profile.get("education", [{}])[1] if len(profile.get("education", [])) > 1 else {}
    
    # 默认使用机械/自动化最拿得出的项目 1
    p_auto = profile.get("projects", {}).get("automation", [{}])[0]
    
    mapping = {
        "name": b.get("name", ""),
        "phone": b.get("phone", ""),
        "email": b.get("email", ""),
        "gender_male": "男",
        "birth_year": "2001",
        "political_status": b.get("political_status", "共青团员"),
        "target_city": b.get("target_city", "深圳/杭州/上海/长沙"),
        
        "master_school": e_master.get("school", "大连交通大学"),
        "master_major": e_master.get("major", "机械工程"),
        "master_degree": e_master.get("degree", "硕士"),
        "master_gpa": e_master.get("score", "85.44"),
        "start_date_master": "2024-09",
        "end_date_master": "2027-07",
        
        "project_name": p_auto.get("name", "大型高温FDM 3D打印设备分布式控制系统研发"),
        "project_role": p_auto.get("role", "课题负责人"),
        "project_desc": p_auto.get("description", ""),
        
        "awards_desc": "；".join(profile.get("awards", [])),
        "skills_desc": "机械与仿真: " + ", ".join(profile.get("skills", {}).get("cad_cae", [])) + "\n控制与系统: " + ", ".join(profile.get("skills", {}).get("embedded_control", [])),
        "self_evaluation": "大连交通大学机械硕士(2027届)，具备500mm高温FDM整机结构设计、EPLAN电气规划及MPC/EKF控制算法落地经验；发表EI论文1篇，申请发明专利1项，获国家级竞赛一等奖/三等奖。"
    }
    return mapping.get(key, "")

def autofill_current_tab(cdp_url="http://127.0.0.1:9222"):
    profile = load_profile()
    if not profile:
        print("❌ 未找到 applicant_profile.json")
        return

    print("🔌 正在连接 Chrome (CDP: 9222)...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            print(f"❌ 无法连接 Chrome: {e}")
            return

        contexts = browser.contexts
        if not contexts or not contexts[0].pages:
            print("❌ 没有找到打开的标签页")
            return

        # 选定当前最后激活的页面
        page = contexts[0].pages[-1]
        print(f"🎯 正在接管当前网申页面: 《{page.title()}》")
        print(f"🔗 页面 URL: {page.url}")

        # 1. 扫描所有可见的 input 和 textarea
        selectors = [
            "input:not([type=hidden]):not([type=file]):not([type=submit]):not([type=button])",
            "textarea"
        ]
        
        elements = page.query_selector_all(", ".join(selectors))
        print(f"🔎 发现 {len(elements)} 个可交互表单元素，开始智能上下文解析与预填...")

        filled_count = 0
        for el in elements:
            try:
                if not el.is_visible():
                    continue

                # 收集元素自身属性
                p_text = el.get_attribute("placeholder") or ""
                name_text = el.get_attribute("name") or ""
                id_text = el.get_attribute("id") or ""
                aria_text = el.get_attribute("aria-label") or ""
                
                # 寻找紧邻的 label 或上级父级文字
                context_text = f"{p_text} {name_text} {id_text} {aria_text}"
                parent = el.evaluate_handle("node => node.closest('div, tr, li, p, .el-form-item, .ant-form-item, section')")
                if parent and parent.as_element():
                    # 提取 label 文字
                    raw_inner = parent.as_element().inner_text()
                    lines = [l.strip() for l in raw_inner.split("\n") if l.strip() and len(l.strip()) < 30]
                    context_text += " " + " ".join(lines[:3])

                field_key = match_field(context_text)
                if field_key:
                    target_val = get_value_for_key(field_key, profile)
                    if not target_val:
                        continue

                    # 判断元素类型
                    el_type = (el.get_attribute("type") or "text").lower()

                    if el_type in ["radio", "checkbox"]:
                        # 单选框处理 (如性别男)
                        if field_key == "gender_male" and ("男" in context_text or "male" in context_text):
                            if not el.is_checked():
                                el.check()
                                filled_count += 1
                                print(f"  ✅ [单选勾选] {field_key} -> 男")
                    else:
                        # 文本输入/长文本
                        current_val = el.input_value()
                        if not current_val.strip():
                            el.fill(str(target_val))
                            filled_count += 1
                            val_preview = str(target_val).replace("\n", " ")[:25]
                            print(f"  ✅ [文本填入] {field_key} -> {val_preview}...")
            except Exception as e:
                continue

        print(f"\n✨ 智能预填完毕！本次共自动填入 {filled_count} 个字段。")

if __name__ == "__main__":
    autofill_current_tab()
