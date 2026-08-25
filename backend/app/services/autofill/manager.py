import json
import os
import urllib.request
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright
from backend.app.services.autofill.adapters.beisen import BeisenAutofillAdapter
from backend.app.services.autofill.adapters.feishu import FeishuJobsAutofillAdapter
from backend.app.services.autofill.adapters.generic import GenericFormAdapter
from backend.app.services.autofill.guard import ZeroSubmitGuard

class CDPManager:
    """Chrome CDP 异步连接与适配器路由器"""

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222"):
        self.cdp_url = cdp_url
        self.adapters = [
            BeisenAutofillAdapter(),
            FeishuJobsAutofillAdapter(),
            GenericFormAdapter() # 默认保底
        ]

    def is_cdp_available(self) -> bool:
        try:
            res = urllib.request.urlopen(f"{self.cdp_url}/json/version", timeout=1.5)
            return res.status == 200
        except Exception:
            return False

    def load_profile(self) -> Dict[str, Any]:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        p_path = os.path.join(base_dir, "data", "applicant_profile.json")
        if os.path.exists(p_path):
            with open(p_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    async def autofill_active_tab(self, resume_path: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_cdp_available():
            return {
                "success": False,
                "platform": "Unknown",
                "filled_fields": 0,
                "message": "无法连接 Chrome 9222 端口，请确保 Chrome 已带 --remote-debugging-port=9222 启动。",
                "zero_submit_safe": True
            }

        profile = self.load_profile()

        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(self.cdp_url)
                if not browser.contexts or not browser.contexts[0].pages:
                    return {"success": False, "platform": "None", "filled_fields": 0, "message": "Chrome 中无激活标签页"}

                page = browser.contexts[0].pages[-1]
                url = page.url
                content = await page.content()

                # 选择最佳适配器
                selected_adapter = self.adapters[-1] # default generic
                for adapter in self.adapters:
                    if await adapter.can_handle(url, content):
                        selected_adapter = adapter
                        break

                # 执行预填
                result = await selected_adapter.fill_form(page, profile, resume_path)
                return result

            except Exception as e:
                return {
                    "success": False,
                    "platform": "Error",
                    "filled_fields": 0,
                    "message": f"预填异常: {str(e)}",
                    "zero_submit_safe": True
                }
