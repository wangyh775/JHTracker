import re
from typing import List

class ZeroSubmitGuard:
    """
    Zero-Submit 硬性物理拦截器
    监控所有 DOM 交互与脚本动作，对任何含有“提交”、“确认投递”、“保存并提交”的动作抛出安全异常并熔断拦截。
    """
    BLOCKED_PATTERNS: List[str] = [
        r"提交申请", r"确认投递", r"立即投递", r"完成投递",
        r"submit", r"confirm_apply", r"final_submit"
    ]

    @classmethod
    def assert_action_safe(cls, element_text: str, element_tag: str, attributes: str):
        combined = f"{element_text} {element_tag} {attributes}".lower()
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, combined, re.I):
                raise PermissionError(
                    f"🛡️ [Zero-Submit Security Violation]: Automated submission attempt intercepted on '{element_text}'. Final submission MUST be performed manually by the candidate."
                )
