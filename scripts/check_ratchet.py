#!/usr/bin/env python3
"""
JHTracker 质量棘轮检查器 (check_ratchet.py)

功能:
    基于 `quality-baseline.json` 记录的历史指标基线，对当前运行的测试与构建结果进行棘轮对比：
    - 绝不允许退步（如测试数量变少、出现测试失败、类型报错）；
    - 若当前指标显著优于基线（如新增了测试用例），支持自动收紧（Tighten Baseline），
      将技术积累强制固化为新的基准线。

用法:
    python scripts/check_ratchet.py [--tighten]
"""

import sys
import json
import subprocess
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BASELINE_FILE = ROOT_DIR / "quality-baseline.json"
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def load_baseline():
    if not BASELINE_FILE.exists():
        print(f"[ERROR] 找不到基线配置文件: {BASELINE_FILE}")
        sys.exit(1)
    try:
        return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] 解析 {BASELINE_FILE} 失败: {e}")
        sys.exit(1)


def save_baseline(baseline_data):
    BASELINE_FILE.write_text(json.dumps(baseline_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] 已成功收紧并固化质量基线到 {BASELINE_FILE.name}")


def run_backend_tests():
    print("[*] 正在执行后端单元测试集...")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    stdout = proc.stdout + proc.stderr
    try:
        print(stdout.strip())
    except UnicodeEncodeError:
        print(stdout.strip().encode("gbk", errors="replace").decode("gbk"))

    # 正则提取 passed 数量
    # 典型格式: "41 passed in 6.50s" 或 "40 passed, 1 failed in ..."
    match = re.search(r"(\d+)\s+passed", stdout)
    passed_count = int(match.group(1)) if match else 0

    fail_match = re.search(r"(\d+)\s+failed", stdout)
    failed_count = int(fail_match.group(1)) if fail_match else (1 if proc.returncode != 0 and passed_count == 0 else 0)

    return passed_count, failed_count


def run_frontend_typecheck():
    print("[*] 正在执行前端 TypeScript 类型检查...")
    # 优先调用本地 node_modules/.bin/tsc，避免跨平台路径问题
    tsc_cmd = "npx tsc --noEmit"
    proc = subprocess.run(
        tsc_cmd,
        cwd=str(FRONTEND_DIR),
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    error_count = 0
    if proc.returncode != 0:
        stdout = proc.stdout + proc.stderr
        print(stdout.strip())
        # 计算报错行数
        error_count = len([line for line in stdout.splitlines() if "error TS" in line])
        if error_count == 0:
            error_count = 1
    else:
        print("  [OK] TypeScript 类型校验完全通过 (0 错误)")

    return error_count


def check_ratchet(auto_tighten=True):
    baseline_data = load_baseline()
    metrics = baseline_data.get("metrics", {})

    base_passed = metrics.get("backend_test_count", {}).get("baseline", 0)
    base_failures = metrics.get("max_backend_failures", {}).get("baseline", 0)
    base_ts_errors = metrics.get("max_typecheck_errors", {}).get("baseline", 0)

    cur_passed, cur_failures = run_backend_tests()
    cur_ts_errors = run_frontend_typecheck()

    violations = []
    improved = False

    # 1. 检查失败用例
    if cur_failures > base_failures:
        violations.append(f"后端测试出现失败用例! 当前失败数: {cur_failures} (基线允许: {base_failures})")

    # 2. 检查测试用例总数（只许增不许减，防止弱化删除测试用例）
    if cur_passed < base_passed:
        violations.append(
            f"后端测试用例总数发生退步! 当前通过数: {cur_passed} < 基线要求数: {base_passed} (-{base_passed - cur_passed})"
        )
    elif cur_passed > base_passed:
        improved = True
        print(f"[+] 发现测试资产增长: 测试用例从 {base_passed} 增至 {cur_passed} (+{cur_passed - base_passed})")

    # 3. 检查 TypeScript 类型安全
    if cur_ts_errors > base_ts_errors:
        violations.append(f"前端 TypeScript 类型错误超出基线! 当前错误: {cur_ts_errors} (基线允许: {base_ts_errors})")

    if violations:
        print("\n" + "=" * 60)
        print("[FAIL] 质量指标棘轮阻断 (QUALITY RATCHET VIOLATIONS):")
        for v in violations:
            print(f"  - {v}")
        print("=" * 60)
        print("请修复上述退步项或补充对应测试后再行提交！")
        return 1

    print("\n[SUCCESS] 所有指标均符合或优于基线要求！")

    # 若指标提升且开启了自动收紧，更新 baseline
    if improved and auto_tighten:
        metrics["backend_test_count"]["baseline"] = cur_passed
        from datetime import date
        baseline_data["updated_at"] = date.today().isoformat()
        save_baseline(baseline_data)

    return 0


if __name__ == "__main__":
    parser = argparse_parser = sys.argv
    tighten_flag = "--no-tighten" not in sys.argv
    sys.exit(check_ratchet(auto_tighten=tighten_flag))
