"""services/safety_guard.py 的单元测试。"""
import pytest
from services.safety_guard import (
    classify_field,
    is_submit_button,
    is_sensitive_category,
    SafetyBlockedError,
)


class TestClassifyField:
    def test_benign_label(self):
        assert classify_field(label_text='姓名') == 'benign'
        assert classify_field(label_text='学校') == 'benign'
        assert classify_field(label_text='邮箱') == 'benign'
        assert classify_field(label_text='电话') == 'benign'

    def test_identity(self):
        assert classify_field(label_text='身份证号') == 'identity'
        assert classify_field(label_text='护照号码') == 'identity'
        assert classify_field(name='ssn') == 'identity'
        assert classify_field(name='national_id') == 'identity'
        assert classify_field(id_attr='id_number') == 'identity'

    def test_legal(self):
        assert classify_field(label_text='是否需要签证') == 'legal'
        assert classify_field(label_text='Sponsorship required') == 'legal'
        assert classify_field(label_text='犯罪记录') == 'legal'
        assert classify_field(name='work_auth') == 'legal'

    def test_compensation(self):
        assert classify_field(label_text='期望薪资') == 'compensation'
        assert classify_field(label_text='当前薪资') == 'compensation'
        assert classify_field(name='salary') == 'compensation'
        assert classify_field(placeholder='expected salary') == 'compensation'

    def test_current_status(self):
        assert classify_field(label_text='推荐人') == 'current_status'
        assert classify_field(label_text='现任雇主') == 'current_status'
        assert classify_field(label_text='在职状态') == 'current_status'
        assert classify_field(name='current_employer') == 'current_status'

    def test_financial(self):
        assert classify_field(label_text='银行账号') == 'financial'
        assert classify_field(label_text='银行卡号') == 'financial'
        assert classify_field(name='bank_account') == 'financial'
        assert classify_field(label_text='社保') == 'financial'

    def test_combined_inputs(self):
        # 多源信息拼接匹配
        assert classify_field(label_text='', name='', id_attr='tax_id', placeholder='') == 'financial'
        # 任一命中即归类
        assert classify_field(label_text='姓名', name='salary_field') == 'compensation'

    def test_empty_inputs(self):
        assert classify_field() == 'benign'
        assert classify_field(label_text='', name='', id_attr='', placeholder='') == 'benign'

    def test_case_insensitive(self):
        assert classify_field(label_text='SALARY') == 'compensation'
        assert classify_field(name='SSN') == 'identity'
        assert classify_field(label_text='Apply Salary') == 'compensation'


class TestIsSubmitButton:
    def test_text_match_chinese(self):
        assert is_submit_button(text='提交') is True
        assert is_submit_button(text='确认投递') is True
        assert is_submit_button(text='投递简历') is True
        assert is_submit_button(text='立即投递') is True
        assert is_submit_button(text='申请职位') is True
        assert is_submit_button(text='确认申请') is True
        assert is_submit_button(text='确认提交') is True

    def test_text_match_english(self):
        assert is_submit_button(text='Apply') is True
        assert is_submit_button(text='Submit') is True
        assert is_submit_button(text='apply now') is True

    def test_text_non_match(self):
        assert is_submit_button(text='下一步') is False
        assert is_submit_button(text='保存草稿') is False
        assert is_submit_button(text='取消') is False
        assert is_submit_button(text='上传简历') is False

    def test_text_too_long_skipped(self):
        # 长度 > 30 的文本应被跳过避免误判文章正文
        long_text = '这是一个超过三十个字符的按钮标题不应该被识别为提交按钮因为我太长了啊'
        assert len(long_text) > 30
        assert is_submit_button(text=long_text) is False

    def test_type_submit(self):
        assert is_submit_button(btn_type='submit') is True
        assert is_submit_button(btn_type='SUBMIT') is True
        assert is_submit_button(btn_type='button') is False

    def test_attr_keywords(self):
        assert is_submit_button(btn_id='submit-btn') is True
        assert is_submit_button(btn_class='apply-button') is True
        assert is_submit_button(btn_class='confirm') is True
        assert is_submit_button(btn_id='cancel-link') is False
        assert is_submit_button(btn_class='next-step') is False

    def test_empty_inputs(self):
        assert is_submit_button() is False
        assert is_submit_button(text='') is False


class TestIsSensitiveCategory:
    def test_sensitive_categories(self):
        assert is_sensitive_category('identity') is True
        assert is_sensitive_category('legal') is True
        assert is_sensitive_category('compensation') is True
        assert is_sensitive_category('current_status') is True
        assert is_sensitive_category('financial') is True

    def test_benign(self):
        assert is_sensitive_category('benign') is False
        assert is_sensitive_category('') is False
        assert is_sensitive_category(None) is False


class TestSafetyBlockedError:
    def test_can_raise(self):
        with pytest.raises(SafetyBlockedError, match='forbidden'):
            raise SafetyBlockedError('forbidden action')
