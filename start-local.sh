#!/usr/bin/env bash

# AI 能力测评系统本地启动脚本（不使用 Docker）
# 需要本机已经安装并启动 MySQL、Redis、Java 21、Python 3 和 Node.js。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend-java"
AGENT_DIR="$ROOT_DIR/agent-python"
FRONTEND_DIR="$ROOT_DIR/frontend-ai-assessment"
LOG_DIR="${TMPDIR:-/tmp}/ai-assessment-local"

fail() {
  echo "[启动失败] $1" >&2
  exit 1
}

command -v java >/dev/null 2>&1 || fail "未找到 Java，请安装 Java 21。"
command -v npm >/dev/null 2>&1 || fail "未找到 npm，请先安装 Node.js。"
command -v nc >/dev/null 2>&1 || fail "未找到 nc，无法检查 MySQL/Redis 端口。"

JAVA_VERSION="$(java -version 2>&1 | sed -n '1s/.*version \"\([0-9]*\).*/\1/p')"
[[ "$JAVA_VERSION" == "21" ]] || echo "[提示] 当前 Java 主版本为 ${JAVA_VERSION:-未知}，项目建议使用 Java 21。"

nc -z 127.0.0.1 3306 >/dev/null 2>&1 || fail "MySQL 未运行或未监听 localhost:3306。"
nc -z 127.0.0.1 6379 >/dev/null 2>&1 || fail "Redis 未运行或未监听 localhost:6379。"

[[ -f "$AGENT_DIR/.env" ]] || fail "缺少 agent-python/.env，请先配置 DeepSeek API Key。"
[[ -x "$AGENT_DIR/.venv/bin/uvicorn" ]] || fail "缺少 Python 虚拟环境，请先执行：cd agent-python && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"

mkdir -p "$LOG_DIR"

echo "[1/3] 启动 Python Agent（8090）..."
cd "$AGENT_DIR"
# 测评过程由 Agent 负责，它需要直连 MySQL 写对话记忆和评分结果
DB_HOST="${DB_HOST:-127.0.0.1}" \
DB_PORT="${DB_PORT:-3306}" \
DB_USERNAME="${DB_USERNAME:-root}" \
DB_PASSWORD="${DB_PASSWORD:-123456}" \
DB_NAME="${DB_NAME:-ai_assessment}" \
./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8090 >"$LOG_DIR/agent.log" 2>&1 &
AGENT_PID=$!

echo "[2/3] 启动 Java 后端（8080）..."
cd "$BACKEND_DIR"
DB_PASSWORD="${DB_PASSWORD:-123456}" \
AGENT_SERVICE_TOKEN="${AGENT_SERVICE_TOKEN:-change-me}" \
REDIS_HOST="${REDIS_HOST:-localhost}" \
./mvnw -q spring-boot:run >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

echo "[3/3] 启动前端（4174）..."
cd "$FRONTEND_DIR"
if [[ ! -d node_modules ]]; then
  npm install
fi
npm run dev -- --host 0.0.0.0 --port 4174 >"$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

cleanup() {
  echo
  echo "正在停止本地服务..."
  kill "$FRONTEND_PID" "$BACKEND_PID" "$AGENT_PID" 2>/dev/null || true
  wait "$FRONTEND_PID" "$BACKEND_PID" "$AGENT_PID" 2>/dev/null || true
  echo "本地服务已停止。"
}
trap cleanup INT TERM EXIT

echo
echo "启动完成，访问：http://localhost:4174"
echo "Java API：http://localhost:8080"
echo "Python Agent：http://localhost:8090/health"
echo "日志目录：$LOG_DIR"
echo "按 Ctrl+C 停止全部本地服务。"
echo

wait "$FRONTEND_PID"
