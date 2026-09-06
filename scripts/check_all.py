#!/usr/bin/env python3
"""
JHTracker 轻量化统一自测门禁 (check_all.py)

定位:
    专为单人高效开发设计，拒绝过度规范与形式主义。
    纯净无副作用（零脏文件写入），极速完成前后端双向校验，确保无失败测试与类型错误。

默认检查:
    1. 版本一致性: 根目录 VERSION / pyproject.toml / package.json 对齐
    2. 后端测试套件: python -m pytest (所有单元测试全部通过)
    3. 前端类型校验: npx tsc --noEmit (0 TypeScript 类型报错)

可选参数:
    --full : 在准备发版或打包验证时追加全量 Vite 生产构建 (npm run build)
"""

import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def check_version_consistency():
    """检查前后端及根目录版本号一致性"""
    print("\n[1/3] 检查版本号一致性 (VERSION / pyproject.toml / package.json)...")
    res = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "bump_version.py"), "check"],
        cwd=str(ROOT_DIR)
    )
    return res.returncode == 0


def run_backend_tests():
    """运行后端 pytest 单元测试套件"""
    print("\n[2/3] 运行后端单元测试 (python -m pytest)...")
    res = subprocess.run(
        [sys.executable, "-m", "pytest"],
        cwd=str(BACKEND_DIR)
    )
    return res.returncode == 0


def run_frontend_typecheck():
    """运行前端 TypeScript 类型检查 (npx tsc --noEmit)"""
    print("\n[3/3] 运行前端类型校验 (npx tsc --noEmit)...")
    res = subprocess.run(
        "npx tsc --noEmit",
        cwd=str(FRONTEND_DIR),
        shell=True
    )
    return res.returncode == 0


def run_frontend_build():
    """可选：前端完整生产构建验证 (Vite Build)"""
    print("\n[*] 正在执行前端全量生产构建 (npm run build)...")
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
        print("\n[FAIL] 版本号不一致，请先确认版本文件！")
        return 1

    # 2. 后端单元测试
    if not run_backend_tests():
        print("\n[FAIL] 后端单元测试未通过！")
        return 1

    # 3. 前端类型校验
    if not run_frontend_typecheck():
        print("\n[FAIL] 前端类型检查报错，请修复 TypeScript 错误！")
        return 1

    # 4. 仅在 --full 时跑打包
    if full_mode:
        if not run_frontend_build():
            print("\n[FAIL] 前端生产打包失败，请检查构建错误！")
            return 1

    print("\n" + "=" * 60)
    print(">> [SUCCESS] 验证通过！代码状态健康，无任何测试失败或类型报错。")
    if not full_mode:
        print("   (提示: 准备发版或做发布打包前可执行 python scripts/check_all.py --full)")
    print("=" * 60 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

