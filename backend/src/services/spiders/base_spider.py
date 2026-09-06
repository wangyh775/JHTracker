import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from src.models import JobItem


def sanitize_date_str(val: Optional[str], default_today: bool = True) -> str:
    """Safely sanitize arbitrary date strings into standard YYYY-MM-DD.
    
    Handles formats like:
      - '2026-09-01'
      - '2026/09/01'
      - '2026.09.01'
      - '2026-09-01 12:00:00'
      - '09-01'
    Falls back safely to current date if unparseable.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    if not val or not str(val).strip():
        return today_str if default_today else ""
    
    raw = str(val).strip()
    
    # 1. Standard YYYY-MM-DD pattern
    m = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', raw)
    if m:
        year, month, day = m.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    
    # 2. MM-DD pattern (e.g. "09-05")
    m_short = re.search(r'(\d{1,2})[-/.](\d{1,2})', raw)
    if m_short:
        current_year = datetime.now().year
        month, day = m_short.groups()
        # Ensure month is valid 1-12 and day 1-31
        m_val, d_val = int(month), int(day)
        if 1 <= m_val <= 12 and 1 <= d_val <= 31:
            return f"{current_year:04d}-{m_val:02d}-{d_val:02d}"
    
    return today_str if default_today else ""


class BaseJobSpider(ABC):
    @abstractmethod
    async def fetch_jobs(self, since_date: str) -> List[JobItem]:
        """Fetch jobs published on or after since_date."""
        pass

