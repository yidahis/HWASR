#!/bin/bash

# 启动脚本 - 同时启动前端和后端服务

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# 定义日志文件
BACKEND_LOG="$SCRIPT_DIR/logs/backend.log"
FRONTEND_LOG="$SCRIPT_DIR/logs/frontend.log"

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"

# 清理函数
cleanup() {
    echo ""
    echo "正在停止所有服务..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "后端服务已停止"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "前端服务已停止"
    fi
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

echo "=========================================="
echo "      HW_ASR 服务启动脚本"
echo "=========================================="
echo ""

# 检查虚拟环境
if [ -f "$BACKEND_DIR/venv/bin/activate" ]; then
    echo "✓ 后端虚拟环境已找到"
else
    echo "✗ 后端虚拟环境未找到,请先在 backend 目录创建虚拟环境"
    echo "  cd backend && python -m venv venv"
    exit 1
fi

# 检查 node_modules
if [ -d "$FRONTEND_DIR/node_modules" ]; then
    echo "✓ 前端依赖已安装"
else
    echo "✗ 前端依赖未安装,请先运行: cd frontend && npm install"
    exit 1
fi

echo ""
echo "正在启动服务..."
echo ""

# 启动后端服务
echo "[1/2] 启动后端服务 (FastAPI + uvicorn)..."
cd "$BACKEND_DIR"
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
sleep 2

# 检查后端是否启动成功
if ps -p $BACKEND_PID > /dev/null; then
    echo "  ✓ 后端服务已启动 (PID: $BACKEND_PID)"
    echo "  - 后端地址: http://localhost:8002"
    echo "  - API文档: http://localhost:8002/docs"
else
    echo "  ✗ 后端服务启动失败,请查看日志: $BACKEND_LOG"
    exit 1
fi

# 启动前端服务
echo ""
echo "[2/2] 启动前端服务 (Vite + React)..."
cd "$FRONTEND_DIR"
nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
sleep 2

# 检查前端是否启动成功
if ps -p $FRONTEND_PID > /dev/null; then
    echo "  ✓ 前端服务已启动 (PID: $FRONTEND_PID)"
    echo "  - 前端地址: http://localhost:5173"
else
    echo "  ✗ 前端服务启动失败,请查看日志: $FRONTEND_LOG"
    cleanup
    exit 1
fi

echo ""
echo "=========================================="
echo "      所有服务已成功启动!"
echo "=========================================="
echo ""
echo "服务访问地址:"
echo "  • 前端应用: http://localhost:5173"
echo "  • 后端API: http://localhost:8002"
echo "  • API文档: http://localhost:8002/docs"
echo ""
echo "日志文件:"
echo "  • 后端日志: $BACKEND_LOG"
echo "  • 前端日志: $FRONTEND_LOG"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "=========================================="

# 等待任意一个进程退出
wait $BACKEND_PID $FRONTEND_PID
cleanup
