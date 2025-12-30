#!/usr/bin/env python3
"""
同时启动前端和后端服务的 Python 脚本
支持跨平台 (Windows/macOS/Linux)
"""

import os
import sys
import subprocess
import platform
import signal
import time
from pathlib import Path


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
LOGS_DIR = PROJECT_ROOT / "logs"

# 日志文件
BACKEND_LOG = LOGS_DIR / "backend.log"
FRONTEND_LOG = LOGS_DIR / "frontend.log"


def print_header():
    """打印启动横幅"""
    print("=" * 42)
    print("      HW_ASR 服务启动脚本")
    print("=" * 42)
    print()


def check_environment():
    """检查运行环境"""
    print("检查运行环境...")

    # 检查后端虚拟环境
    venv_paths = [
        BACKEND_DIR / "venv" / "Scripts" / "python.exe",  # Windows
        BACKEND_DIR / "venv" / "bin" / "python",         # Unix
    ]

    venv_found = any(path.exists() for path in venv_paths)
    if venv_found:
        print("  ✓ 后端虚拟环境已找到")
    else:
        print("  ✗ 后端虚拟环境未找到")
        print("    请先在 backend 目录创建虚拟环境:")
        print("    cd backend && python -m venv venv")
        return False

    # 检查前端依赖
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        print("  ✓ 前端依赖已安装")
    else:
        print("  ✗ 前端依赖未安装")
        print("    请先运行: cd frontend && npm install")
        return False

    print()
    return True


def get_python_executable():
    """获取 Python 可执行文件路径"""
    system = platform.system()
    if system == "Windows":
        return BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    else:
        return BACKEND_DIR / "venv" / "bin" / "python"


def start_backend():
    """启动后端服务"""
    print("[1/2] 启动后端服务 (FastAPI + uvicorn)...")

    LOGS_DIR.mkdir(exist_ok=True)

    python_exe = get_python_executable()
    cmd = [
        str(python_exe),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8002",
        "--reload"
    ]

    # 打开日志文件
    backend_log = open(BACKEND_LOG, "w", encoding="utf-8")

    # 启动进程
    process = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        stdout=backend_log,
        stderr=backend_log,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
    )

    # 等待启动
    time.sleep(3)

    if process.poll() is None:
        print(f"  ✓ 后端服务已启动 (PID: {process.pid})")
        print("  - 后端地址: http://localhost:8002")
        print("  - API文档: http://localhost:8002/docs")
        return process
    else:
        print(f"  ✗ 后端服务启动失败,请查看日志: {BACKEND_LOG}")
        return None


def start_frontend():
    """启动前端服务"""
    print()
    print("[2/2] 启动前端服务 (Vite + React)...")

    LOGS_DIR.mkdir(exist_ok=True)

    # 确定 npm 可执行文件名
    npm = "npm.cmd" if platform.system() == "Windows" else "npm"

    cmd = [npm, "run", "dev"]

    # 打开日志文件
    frontend_log = open(FRONTEND_LOG, "w", encoding="utf-8")

    # 启动进程
    process = subprocess.Popen(
        cmd,
        cwd=FRONTEND_DIR,
        stdout=frontend_log,
        stderr=frontend_log,
        shell=platform.system() == "Windows",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
    )

    # 等待启动
    time.sleep(3)

    if process.poll() is None:
        print(f"  ✓ 前端服务已启动 (PID: {process.pid})")
        print("  - 前端地址: http://localhost:5173")
        return process
    else:
        print(f"  ✗ 前端服务启动失败,请查看日志: {FRONTEND_LOG}")
        return None


def stop_processes(backend_process, frontend_process):
    """停止所有进程"""
    print()
    print("正在停止所有服务...")

    system = platform.system()

    def kill_process(process, name):
        if process and process.poll() is None:
            try:
                if system == "Windows":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    process.terminate()

                # 等待进程结束
                process.wait(timeout=5)
                print(f"  ✓ {name}已停止")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"  ✓ {name}已强制停止")
            except Exception as e:
                print(f"  ✗ 停止{name}时出错: {e}")

    kill_process(backend_process, "后端服务")
    kill_process(frontend_process, "前端服务")


def wait_for_processes(backend_process, frontend_process):
    """等待进程退出"""
    try:
        backend_process.wait()
        print("后端服务已退出")
    except KeyboardInterrupt:
        pass

    try:
        frontend_process.wait()
        print("前端服务已退出")
    except KeyboardInterrupt:
        pass


def main():
    """主函数"""
    print_header()

    # 检查环境
    if not check_environment():
        sys.exit(1)

    # 启动服务
    print("正在启动服务...")
    print()

    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)

    frontend_process = start_frontend()
    if not frontend_process:
        stop_processes(backend_process, None)
        sys.exit(1)

    # 显示成功信息
    print()
    print("=" * 42)
    print("      所有服务已成功启动!")
    print("=" * 42)
    print()
    print("服务访问地址:")
    print("  • 前端应用: http://localhost:5173")
    print("  • 后端API: http://localhost:8002")
    print("  • API文档: http://localhost:8002/docs")
    print()
    print("日志文件:")
    print(f"  • 后端日志: {BACKEND_LOG}")
    print(f"  • 前端日志: {FRONTEND_LOG}")
    print()
    print("按 Ctrl+C 停止所有服务")
    print("=" * 42)
    print()

    # 注册信号处理
    def signal_handler(signum, frame):
        stop_processes(backend_process, frontend_process)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, signal_handler)

    # 等待进程
    wait_for_processes(backend_process, frontend_process)
    stop_processes(backend_process, frontend_process)


if __name__ == "__main__":
    main()
