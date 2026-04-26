#!/usr/bin/env python3
"""
Docker 环境设置脚本 - 用于配置 OpenClaw Docker 运行环境
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def check_docker():
    """检查 Docker 是否安装并运行"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Docker 已安装: {result.stdout.strip()}")

        # 检查 Docker 是否运行
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Docker 守护进程正在运行")
            return True
        else:
            print("✗ Docker 守护进程未运行，请启动 Docker Desktop")
            return False
    except FileNotFoundError:
        print("✗ Docker 未安装")
        return False
    except Exception as e:
        print(f"✗ 检查 Docker 时出错: {e}")
        return False

def build_image():
    """构建 Docker 镜像"""
    print("\n正在构建 OpenClaw Docker 镜像...")
    dockerfile = ROOT / "docker" / "Dockerfile.windows"

    if not dockerfile.exists():
        print(f"✗ Dockerfile 不存在: {dockerfile}")
        return False

    try:
        result = subprocess.run(
            ["docker", "build", "-f", str(dockerfile), "-t", "openclaw-membench:latest", "."],
            cwd=ROOT,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print("✓ 镜像构建成功")
            return True
        else:
            print("✗ 镜像构建失败")
            return False
    except Exception as e:
        print(f"✗ 构建镜像时出错: {e}")
        return False

def check_image():
    """检查镜像是否存在"""
    try:
        result = subprocess.run(
            ["docker", "images", "openclaw-membench:latest", "-q"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print("✓ openclaw-membench:latest 镜像已存在")
            return True
        else:
            print("✗ openclaw-membench:latest 镜像不存在")
            return False
    except Exception as e:
        print(f"✗ 检查镜像时出错: {e}")
        return False

def test_container():
    """测试容器是否可以正常运行"""
    print("\n正在测试容器...")
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "openclaw-membench:latest", "openclaw", "--version"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✓ 容器测试成功: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ 容器测试失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ 容器测试超时")
        return False
    except Exception as e:
        print(f"✗ 测试容器时出错: {e}")
        return False

def main():
    print("=" * 50)
    print("OpenClaw Docker 环境设置")
    print("=" * 50)

    # 检查 Docker
    if not check_docker():
        sys.exit(1)

    # 检查或构建镜像
    if not check_image():
        if not build_image():
            sys.exit(1)

    # 测试容器
    if not test_container():
        print("\n警告: 容器测试失败，但镜像已存在")

    print("\n" + "=" * 50)
    print("Docker 环境设置完成!")
    print("=" * 50)
    print("\n现在可以运行测试:")
    print("  python eval/run_batch.py --category 01_Recent_Constraint_Tracking --runtime openclaw-docker")

if __name__ == "__main__":
    main()
