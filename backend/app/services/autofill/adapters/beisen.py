import re
import os
import asyncio
from typing import Dict, Any, Optional
from backend.app.services.autofill.base import BaseAutofillAdapter
from backend.app.services.autofill.guard import ZeroSubmitGuard

class BeisenAutofillAdapter(BaseAutofillAdapter):
    """北森（Beisen/Zhiye/Inovance）前后端分离与表单系统适配器"""

    async def can_handle(self, url: str, page_content: str) -> bool:
        return bool(re.search(r"zhiye\.com|recruit\.inovance\.com|beisen", url, re.I))

    async def fill_form(self, page, profile: Dict[str, Any], resume_path: Optional[str] = None) -> Dict[str, Any]:
        filled_count = 0
        uploaded_resume = None

        # 1. 如果存在文件上传控件，并且提供了简历 PDF，执行拖拽上传/解析
        if resume_path and os.path.exists(resume_path):
            file_input = await page.query_selector("input[type=file]")
            if file_input:
                await file_input.set_input_files(resume_path)
                uploaded_resume = os.path.basename(resume_path)
                await asyncio.sleep(2)

        # 2. 扫描并安全填入当前页面的文本与长文本输入框
        b = profile.get("basic_info", {})
        e_master = profile.get("education", [{}])[0]
        p_auto = profile.get("projects", {}).get("automation", [{}])[0]

        mapping_rules = [
            (r"姓\s*名|真实姓名|candidate_name|name", b.get("name", "王云鹤")),
            (r"手\s*机|联系电话|phone|mobile", b.get("phone", "13000000000")),
            (r"邮\s*箱|电子邮箱|email|mail", b.get("email", "wangyh775@163.com")),
            (r"学校|毕业院校|就读院校|school", e_master.get("school", "大连交通大学")),
            (r"专\s*业|所学专业|major", e_master.get("major", "机械工程")),
            (r"绩点|GPA|gpa|成绩", e_master.get("score", "85.44/100")),
            (r"期望城市|意向城市|地点|city", b.get("target_city", "苏州/深圳/上海/杭州")),
            (r"项目名称|课题名称", p_auto.get("name", "大型高温FDM 3D打印设备分布式控制系统研发")),
            (r"项目职责|担任角色|职务", p_auto.get("role", "课题负责人")),
            (r"项目描述|项目经历|科研经历", p_auto.get("description", "")),
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
                parent = await el.evaluate_handle("node => node.closest('.el-form-item, .form-item, .ant-form-item, div, li, tr')")
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

        # Zero-Submit 安全验证：不执行任何提交动作，返回结果
        return {
            "success": True,
            "platform": "Beisen (北森校招系统)",
            "filled_fields": filled_count,
            "uploaded_resume": uploaded_resume,
            "message": "北森系统安全预填已完成，请在浏览器中核对并手动提交。",
            "zero_submit_safe": True
        }
