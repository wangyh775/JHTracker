"""Security and validation helpers for JHTracker to prevent injection,
path traversal, and unauthorized direct SQL/system command execution.
NOTE: Database queries must always use parameterized bindings (e.g., '?' placeholders).
The patterns here serve as a defense-in-depth sanitization layer for user inputs.
"""
import re
from typing import Optional

DANGEROUS_SQL_PATTERNS = [
    r";\s*(?:DROP|DELETE|UPDATE|INSERT|ALTER)\b",
    r"--",
    r"/\*[\s\S]*?\*/",
    r"\bUNION\s+ALL\s+SELECT\b",
    r"\bUNION\s+SELECT\b",
    r"\bEXEC(?:\s+|\()",
    r"\bXP_",
]

SAFE_CHANNEL_PATTERN = r"^[a-zA-Z0-9_\-\u4e00-\u9fa5]{1,50}$"
SAFE_IDENTIFIER_PATTERN = r"^[a-zA-Z0-9_\-\u4e00-\u9fa5]{1,128}$"
URL_PATTERN = r"^https?:\/\/[^\s\/$.?#].[^\s]*$"

def sanitize_identifier(ident: Optional[str]) -> Optional[str]:
    """Validate and sanitize IDs (job_id, resume_id, application_id).
    Returns None if malformed or containing SQL/command injection markers.
    """
    if not ident:
        return None
    cleaned = str(ident).strip()
    if not re.match(SAFE_IDENTIFIER_PATTERN, cleaned):
        return None
    return cleaned

def sanitize_text_input(text: Optional[str], max_len: int = 500) -> str:
    """Sanitize general textual parameters, stripping dangerous injection patterns."""
    if not text:
        return ""
    cleaned = str(text).strip()[:max_len]
    for pattern in DANGEROUS_SQL_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def validate_url(url: Optional[str]) -> Optional[str]:
    """Validate HTTP/HTTPS URL and prevent javascript:/file: protocols."""
    if not url:
        return None
    cleaned = str(url).strip()
    if not cleaned.lower().startswith(("http://", "https://")):
        return None
    if not re.match(URL_PATTERN, cleaned):
        return None
    return cleaned

def sanitize_search_keyword(keyword: Optional[str]) -> str:
    """Sanitize and clamp search keywords."""
    if not keyword:
        return ""
    cleaned = keyword.strip()
    if len(cleaned) > 100:
        cleaned = cleaned[:100]
    for pattern in DANGEROUS_SQL_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def validate_safe_text(text: Optional[str], field_name: str = "text", max_length: int = 500) -> str:
    """Validate general text fields for safety and reasonable length."""
    if not text:
        return ""
    cleaned = text.strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    for pattern in DANGEROUS_SQL_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise ValueError(f"Dangerous input detected in field '{field_name}'.")
    return cleaned

def validate_channel(channel: Optional[str]) -> str:
    """Validate application channel name."""
    if not channel:
        return "智能体推荐"
    ch = channel.strip()
    if not re.match(SAFE_CHANNEL_PATTERN, ch):
        return "智能体推荐"
    return ch
