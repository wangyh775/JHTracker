import re
import os
from typing import Dict, Any, Optional
from backend.app.services.autofill.base import BaseAutofillAdapter

class GenericFormAdapter(BaseAutofillAdapter):
    """通用企业网申与校招表单启发式适配器"""

    async def can_handle(self, url: str, page_content: str) -> bool:
        # 作为保底通用适配器，始终返回 True
        return True

    async def fill_form(self, page, profile: Dict[str, Any], resume_path: Optional[str] = None) -> Dict[str, Any]:
        filled_count = 0
        uploaded_resume = None

        if resume_path and os.path.exists(resume_path):
            file_input = await page.query_selector("input[type=file]")
            if file_input:
                try:
                    await file_input.set_input_files(resume_path)
                    uploaded_resume = os.path.basename(resume_path)
                except Exception:
                    pass

        b = profile.get("basic_info", {})
        e_master = profile.get("education", [{}])[0]

        mapping_rules = [
            (r"姓\s*名|真实姓名|candidate_name|name", b.get("name", "王云鹤")),
            (r"手\s*机|联系电话|phone|mobile", b.get("phone", "13000000000")),
            (r"邮\s*箱|电子邮箱|email|mail", b.get("email", "wangyh775@163.com")),
            (r"学校|毕业院校|就读院校|school", e_master.get("school", "大连交通大学")),
            (r"专\s*业|所学专业|major", e_master.get("major", "机械工程")),
            (r"绩点|GPA|gpa|成绩", e_master.get("score", "85.44/100")),
            (r"期望城市|意向城市|地点|city", b.get("target_city", "苏州/深圳/上海/杭州")),
            (r"自我评价|自我介绍|个人总结", "大连交通大学机械硕士(2027届)，具备500mm高温FDM整机结构设计、EPLAN电气规划及MPC/EKF控制算法落地经验；发表EI论文1篇，申请发明专利1项，获国家一等奖。")
        ]

        inputs = await page.query_selector_all("input:not([type=hidden]):not([type=file]):not([type=submit]):not([type=button]), textarea")
        for el in inputs:
            try:
                if not await el.is_visible():
                    continue

                p_text = await el.get_attribute("placeholder") or ""
                name_text = await el.get_attribute("name") or ""
                id_text = await el.get_attribute("id") or ""
                aria_text = await el.get_attribute("aria-label") or ""

                label_text = ""
                parent = await el.evaluate_handle("node => node.closest('div, tr, li, p, section')")
                if parent and parent.as_element():
                    label_text = await parent.as_element().inner_text()

                combined = f"{p_text} {name_text} {id_text} {aria_text} {label_text}".lower().strip()

                for pattern, val in mapping_rules:
                    if re.search(pattern, combined, re.I):
                        curr = await el.input_value()
                        if not curr.strip():
                            await el.fill(str(val))
                            await el.dispatch_event("input")
                            await el.dispatch_event("change")
                            filled_count += 1
                        break
            except Exception:
                continue

        return {
            "success": True,
            "platform": "Generic Form (通用表单系统)",
            "filled_fields": filled_count,
            "uploaded_resume": uploaded_resume,
            "message": "通用网申表单预填完成，请核实后手动提交。",
            "zero_submit_safe": True
        }
