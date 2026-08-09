"""utils.role_family_normalize / role_family_match 的单元测试。"""
import pytest
from utils import role_family_normalize, role_family_match


class TestRoleFamilyNormalize:
    def test_simple_chinese(self):
        assert role_family_normalize('机器人算法') == '机器人算法'

    def test_separator_slash(self):
        assert role_family_normalize('机器人 / 算法') == '机器人/算法'
        assert role_family_normalize('机器人/算法') == '机器人/算法'

    def test_separator_full_slash(self):
        assert role_family_normalize('机器人／算法') == '机器人/算法'

    def test_separator_chinese_comma(self):
        assert role_family_normalize('机器人、算法') == '机器人/算法'

    def test_separator_comma(self):
        assert role_family_normalize('机器人,算法') == '机器人/算法'
        assert role_family_normalize('机器人，算法') == '机器人/算法'

    def test_multiple_separators_merged(self):
        assert role_family_normalize('机器人 // 算法') == '机器人/算法'
        assert role_family_normalize('机器人 /  / 算法') == '机器人/算法'

    def test_strip_leading_trailing_slash(self):
        assert role_family_normalize('/机器人/') == '机器人'
        assert role_family_normalize(' / 机器人 / ') == '机器人'

    def test_lowercase_english(self):
        assert role_family_normalize('  Embedded  / Software ') == 'embedded/software'
        assert role_family_normalize('Embedded Software') == 'embedded/software'

    def test_empty(self):
        assert role_family_normalize('') == ''
        assert role_family_normalize(None) == ''
        assert role_family_normalize('   ') == ''


class TestRoleFamilyMatch:
    def test_exact_match(self):
        assert role_family_match('机器人算法', '机器人算法') is True
        assert role_family_match('机器人/算法', '机器人/算法') is True

    def test_general_matches_all(self):
        # stored 为空 = 通用，恒匹配
        assert role_family_match('', '机器人算法') is True
        assert role_family_match(None, '嵌入式') is True

    def test_empty_query_no_match_specific(self):
        # 查询为空，不匹配任何具体岗位族
        assert role_family_match('机器人算法', '') is False
        assert role_family_match('机器人算法', None) is False

    def test_substring_match(self):
        # 「算法」是「算法工程师」的子串
        assert role_family_match('算法', '算法工程师') is True
        assert role_family_match('算法工程师', '算法') is True

    def test_normalize_before_match(self):
        assert role_family_match('机器人 / 算法', '机器人、算法') is True

    def test_non_match(self):
        assert role_family_match('嵌入式', '算法') is False
