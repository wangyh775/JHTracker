"""utils.py 的单元测试。"""
import pytest
from datetime import date
from utils import parse_date, try_int, validate_salary, validate_dates, parse_markdown_table, safe_filename, humanize_size


class TestParseDate:
    def test_normal(self):
        assert parse_date('2026-07-25') == date(2026, 7, 25)

    def test_with_time(self):
        assert parse_date('2026-07-25T12:00:00') == date(2026, 7, 25)

    def test_empty(self):
        assert parse_date('') is None
        assert parse_date(None) is None

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_date('2026/07/25')
        with pytest.raises(ValueError):
            parse_date('not-a-date')


class TestTryInt:
    def test_normal(self):
        assert try_int('123') == 123

    def test_invalid(self):
        assert try_int('abc') is None
        assert try_int('abc', default=0) == 0

    def test_empty(self):
        assert try_int('') is None
        assert try_int(None) is None


class TestValidateSalary:
    def test_valid(self):
        assert validate_salary(10, 20) == (10, 20)

    def test_equal(self):
        assert validate_salary(15, 15) == (15, 15)

    def test_none(self):
        assert validate_salary(None, 20) == (None, 20)
        assert validate_salary(10, None) == (10, None)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            validate_salary(30, 20)


class TestValidateDates:
    def test_valid(self):
        d1, d2 = date(2026, 7, 1), date(2026, 8, 1)
        assert validate_dates(d1, d2) == (d1, d2)

    def test_none(self):
        assert validate_dates(None, date(2026, 8, 1)) == (None, date(2026, 8, 1))

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            validate_dates(date(2026, 8, 1), date(2026, 7, 1))


class TestParseMarkdownTable:
    def test_basic(self):
        lines = [
            '| 排名 | 公司 | 城市 |',
            '|---|---|---|',
            '| 1 | 拓竹 | 深圳 |',
            '| 2 | 创想 | 深圳 |',
        ]
        headers, rows = parse_markdown_table(lines)
        assert headers == ['排名', '公司', '城市']
        assert len(rows) == 2
        assert rows[0]['公司'] == '拓竹'
        assert rows[1]['城市'] == '深圳'

    def test_bold_headers(self):
        lines = [
            '| **公司** | **城市** |',
            '|---|---|',
            '| 拓竹 | 深圳 |',
        ]
        headers, rows = parse_markdown_table(lines)
        assert headers == ['公司', '城市']

    def test_no_table(self):
        lines = ['some text', 'no table here']
        headers, rows = parse_markdown_table(lines)
        assert headers == []
        assert rows == []


class TestSafeFilename:
    def test_format(self):
        name = safe_filename('中文简历.pdf', 'pdf')
        assert name.endswith('.pdf')
        assert '_' in name

    def test_no_chinese_in_storage(self):
        name = safe_filename('中文简历.pdf', 'pdf')
        # 存储文件名不应包含中文
        assert all(ord(c) < 128 for c in name)


class TestHumanizeSize:
    def test_bytes(self):
        assert humanize_size(500) == '500 B'

    def test_kb(self):
        assert humanize_size(2048) == '2.0 KB'

    def test_mb(self):
        assert humanize_size(1024 * 1024 * 5) == '5.0 MB'
