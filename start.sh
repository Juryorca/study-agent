#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ─── Python 路径：可通过 --python 参数指定 ───
PYTHON="python"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --python) PYTHON="$2"; shift 2 ;;
        *) echo "未知参数: $1"; echo "用法: $0 [--python /path/to/python]"; exit 1 ;;
    esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

cleanup() {
    echo ""
    echo -e "${CYAN}正在关闭...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}已关闭所有服务${NC}"
}
trap cleanup EXIT INT TERM

# ─── 清理残留进程 ───
echo -e "${CYAN}清理残留端口占用...${NC}"
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 0.5

# ─── 检查 .env ───
if [ ! -f "$ROOT/backend/.env" ]; then
    echo -e "${RED}错误: backend/.env 不存在，请先配置 LLM API Key${NC}"
    echo "复制 backend/.env.example 为 backend/.env 并填入你的密钥"
    exit 1
fi

# ─── 检查前端依赖 ───
if [ ! -d "$ROOT/frontend/node_modules" ]; then
    echo -e "${CYAN}安装前端依赖...${NC}"
    cd "$ROOT/frontend"
    npm install
fi

# ─── 启动后端 ───
echo -e "${CYAN}[1/2] 启动后端 FastAPI (端口 8000)...${NC}"
cd "$ROOT/backend"
$PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 等后端起来
sleep 1
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}后端启动失败，请检查错误信息${NC}"
    exit 1
fi
echo -e "${GREEN}  后端已启动 → http://localhost:8000${NC}"
echo -e "  API 文档 → http://localhost:8000/docs"

# ─── 启动前端 ───
echo -e "${CYAN}[2/2] 启动前端 Next.js (端口 3000)...${NC}"
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

sleep 3
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Study Agent 已启动${NC}"
echo -e "${GREEN}  前端: http://localhost:3000${NC}"
echo -e "${GREEN}  后端: http://localhost:8000${NC}"
echo -e "${GREEN}  API:  http://localhost:8000/docs${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待任意子进程退出
wait
