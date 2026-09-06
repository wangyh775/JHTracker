#!/usr/bin/env python3
"""
JHTracker 轻量化统一自测门禁 (check_all.py)

定位:
    专为单人高效开发与智能体自测设计，拒绝过度规范与形式主义。
    默认 5 秒内极速完成前后端双向校验，保证“代码不倒退、类型不报错”。

默认检查:
    1. 质量棘轮 (Ratchet): 后端 pytest (41+ 用例全绿且不减少) + 前端 tsc 类型校验 (0 错误)
    2. 版本一致性: 根目录 VERSION / pyproject.toml / package.json 对齐

可选参数:
    --full : 在准备发版或提交 PR 时追加全量 Vite 生产打包验证 (npm run build)
"""

import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
FRONTEND_DIR = ROOT_DIR / "frontend"


def check_version_consistency():
    """检查前后端及根目录版本号一致性"""
    res = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "bump_version.py"), "check"],
        cwd=str(ROOT_DIR)
    )
    return res.returncode == 0


def run_ratchet_gate():
    """运行质量棘轮，保证单元测试与类型定义不发生任何倒退"""
    res = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "check_ratchet.py")],
        cwd=str(ROOT_DIR)
    )
    return res.returncode == 0


def run_frontend_build():
    """可选：前端完整生产构建验证 (Vite Build)"""
    print("\n[*] 正在执行前端全量构建验证 (npm run build)...")
    res = subprocess.run(
        "npm run build",
        cwd=str(FRONTEND_DIR),
        shell=True
    )
    return res.returncode == 0


def main():
    full_mode = "--full" in sys.argv

    print("\n" + "=" * 60)
    print(">> [JHTracker] 正在执行轻量化开发自测门禁...")
    print("=" * 60)

    # 1. 版本一致性
    if not check_version_consistency():
        print("[FAIL] 版本号不一致，请先确认版本文件！")
        return 1

    # 2. 质量棘轮核心验证 (测试套件 + 类型系统)
    if not run_ratchet_gate():
        print("\n[FAIL] 自测未通过：存在测试失败、用例减少或类型报错！")
        return 1

    # 3. 仅在 --full 时跑耗时的打包
    if full_mode:
        if not run_frontend_build():
            print("\n[FAIL] 前端生产打包失败，请检查构建错误！")
            return 1

    print("\n" + "=" * 60)
    print(">> [SUCCESS] 验证通过！代码状态健康，无质量滑坡。")
    if not full_mode:
        print("   (提示: 准备发版或提 PR 前可执行 python scripts/check_all.py --full)")
    print("=" * 60 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
