"""Safety Guard：网申预填安全边界引擎。

职责：
1. classify_field() — 按正则黑名单把表单字段分类为 identity/legal/compensation/current_status/financial/benign。
   敏感字段只能从 data/profile.md 取，缺失则 awaiting_human，绝不猜测。
2. is_submit_button() — 识别提交类按钮，Playwright 禁止点击。
3. SafetyBlockedError — Agent/Playwright 试图违反安全门时抛出。

参考：openspec/changes/application-executor-semiauto/specs/safety-guard-ats/spec.md
"""
import re

from constants import (
    SENSITIVE_FIELD_PATTERNS,
    SUBMIT_BUTTON_TEXT_PATTERNS,
    SUBMIT_BUTTON_ATTR_KEYWORDS,
)


class SafetyBlockedError(Exception):
    """Agent/Playwright 试图违反安全门（如点提交按钮、自动填敏感字段）时抛出。"""


# 预编译敏感字段正则（大小写不敏感）
_SENSITIVE_COMPILED = [
    (re.compile(pat, re.IGNORECASE), category)
    for pat, category in SENSITIVE_FIELD_PATTERNS
]

# 预编译提交按钮文本正则（大小写不敏感）
_SUBMIT_TEXT_COMPILED = [
    re.compile(pat, re.IGNORECASE)
    for pat in SUBMIT_BUTTON_TEXT_PATTERNS
]


def classify_field(label_text='', name='', id_attr='', placeholder=''):
    """把表单字段分类为 identity/legal/compensation/current_status/financial/benign。

    Args:
        label_text: 字段关联的可见 label 文本（最优先）。
        name: input/select 的 name 属性。
        id_attr: 元素 id。
        placeholder: 占位提示文本。

    Returns:
        str: 分类标识。benign 表示非敏感，可走 AnswerBank。
    """
    # 拼接所有线索为一个大字符串，统一匹配
    combined = ' '.join(filter(None, [label_text, name, id_attr, placeholder]))
    if not combined:
        return 'benign'
    for pattern, category in _SENSITIVE_COMPILED:
        if pattern.search(combined):
            return category
    return 'benign'


def is_submit_button(text='', btn_type='', btn_id='', btn_class='', onclick=''):
    """判断元素是否为提交类按钮。命中以下任一条件即返回 True。

    1. type=submit；
    2. id/class 含 'submit'/'confirm'/'apply-button' 等关键词；
    3. 可见文本（长度 ≤ 30）匹配 提交/Apply/确认投递 等模式。

    Playwright 在每次 click() 前必先调此函数，命中则跳过点击并记 safety_blocked_click 轨迹。
    """
    # 1. type=submit 直接判定
    if btn_type and btn_type.lower() == 'submit':
        return True

    # 2. id/class/onclick 含关键词（不区分大小写）
    attrs = ' '.join(filter(None, [btn_id, btn_class, onclick])).lower()
    for kw in SUBMIT_BUTTON_ATTR_KEYWORDS:
        if kw in attrs:
            return True

    # 3. 可见文本匹配（长度 > 30 视为正文，跳过避免误判）
    if text:
        t = text.strip()
        if len(t) <= 30:
            for pattern in _SUBMIT_TEXT_COMPILED:
                if pattern.search(t):
                    return True
    return False


def is_sensitive_category(category):
    """是否为敏感分类（不能走 AnswerBank，必须从 profile 取）。"""
    return category in ('identity', 'legal', 'compensation', 'current_status', 'financial')
