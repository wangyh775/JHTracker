from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAutofillAdapter(ABC):
    """网申系统自动化适配器基类"""
    
    @abstractmethod
    async def can_handle(self, url: str, page_content: str) -> bool:
        """判断当前适配器是否能够处理该目标系统"""
        pass

    @abstractmethod
    async def fill_form(self, page, profile: Dict[str, Any], resume_path: Optional[str] = None) -> Dict[str, Any]:
        """
        执行表单预填与简历挂载。
        必须严格遵守 Zero-Submit 红线：严禁触发任何提交/确认投递动作。
        """
        pass
