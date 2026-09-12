#!/usr/bin/env bash
#
# 三端检查一条命令跑完：Agent 单测 + 后端单测 + 前端生产构建。
# 本地提交前和 CI 上跑的是同一份，避免"我本机是好的"。
#
#   ./check.sh           全部
#   ./check.sh agent     只跑 Agent
#   ./check.sh backend   只跑后端
#   ./check.sh frontend  只跑前端

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-all}"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

check_agent() {
  say "Agent：单元测试"
  local python="$ROOT/agent-python/.venv/bin/python"
  if [[ ! -x "$python" ]]; then
    echo "缺少 agent-python/.venv，请先执行：" >&2
    echo "  cd agent-python && python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt" >&2
    exit 1
  fi
  (cd "$ROOT/agent-python" && "$python" -m pytest -q)
}

check_backend() {
  say "后端：单元测试"
  (cd "$ROOT/backend-java" && ./mvnw -q -B test)
}

check_frontend() {
  say "前端：lint + 生产构建"
  (cd "$ROOT/frontend-ai-assessment" && { [ -d node_modules ] || npm install --silent; } && npm run lint && npm run build)
}

case "$TARGET" in
  agent) check_agent ;;
  backend) check_backend ;;
  frontend) check_frontend ;;
  all) check_agent; check_backend; check_frontend ;;
  *) echo "用法：$0 [all|agent|backend|frontend]"; exit 1 ;;
esac

say "全部通过"
