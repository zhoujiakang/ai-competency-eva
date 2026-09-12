#!/usr/bin/env bash
#
# 一键发布到生产服务器
#
#   ./deploy/release.sh            # 全量：后端 + 前端 + Agent
#   ./deploy/release.sh frontend   # 只发前端（改页面/样式时最快，秒级）
#   ./deploy/release.sh backend    # 只发后端
#   ./deploy/release.sh agent      # 只发 Agent
#
# 为什么在本机构建、上传产物，而不是在服务器上拉代码构建：
# 服务器只有 2 核 1.6G 内存，跑 Maven / npm 构建容易把内存吃满，
# 一旦 OOM，同机上的静态页也会跟着挂。所以构建放在本机，服务器只接收产物。
#
# 发布不会碰 /photoelectric/（朋友的静态页），也不会覆盖服务器上的 .env。

set -euo pipefail

SERVER="${SERVER:-root@120.26.93.206}"
APP_DIR="${APP_DIR:-/opt/ai-assessment}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-all}"
HOST="${SERVER#*@}"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

for cmd in ssh rsync scp curl; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "缺少命令：$cmd"; exit 1; }
done

deploy_backend() {
  # 默认连单测一起跑（纯单测，几秒钟）：打包前的门禁。急着发版时用 SKIP_TESTS=1 跳过。
  say "后端：构建 jar${SKIP_TESTS:+（跳过测试）}"
  (cd "$ROOT/backend-java" && ./mvnw -q -B ${SKIP_TESTS:+-DskipTests} package)
  say "后端：上传"
  scp -q "$ROOT/backend-java/target/"*.jar "$SERVER:$APP_DIR/backend/app.jar"
}

deploy_frontend() {
  say "前端：构建静态产物"
  (cd "$ROOT/frontend-ai-assessment" &&
    [ -d node_modules ] || npm install --silent)
  # 生产构建不需要 VITE_API_BASE：默认走同源的 /api（由 nginx 反代）
  (cd "$ROOT/frontend-ai-assessment" && npm run build)
  say "前端：上传"
  rsync -az --delete "$ROOT/frontend-ai-assessment/dist/" "$SERVER:$APP_DIR/frontend/"
}

deploy_agent() {
  say "Agent：上传源码"
  # 排除本机虚拟环境与密钥：服务器上有自己的 .venv 和 .env
  rsync -az \
    --exclude '.venv' --exclude '__pycache__' --exclude '.env' \
    --exclude '.pytest_cache' --exclude '.idea' \
    "$ROOT/agent-python/" "$SERVER:$APP_DIR/agent/"

  local local_hash remote_hash
  local_hash=$(shasum -a 256 "$ROOT/agent-python/requirements.txt" | awk '{print $1}')
  remote_hash=$(ssh "$SERVER" "sha256sum $APP_DIR/agent/requirements.txt 2>/dev/null | awk '{print \$1}'" || true)
  if [ "$local_hash" != "$remote_hash" ]; then
    say "Agent：依赖有变化，重新安装"
    ssh "$SERVER" "$APP_DIR/agent/.venv/bin/pip install -q -r $APP_DIR/agent/requirements.txt"
  fi
}

case "$TARGET" in
  frontend) deploy_frontend ;;
  backend) deploy_backend ;;
  agent) deploy_agent ;;
  all)
    deploy_backend
    deploy_frontend
    deploy_agent
    ;;
  *)
    echo "用法：$0 [all|frontend|backend|agent]"
    exit 1
    ;;
esac

say "重启服务"
ssh "$SERVER" 'systemctl restart ai-assessment-agent; sleep 3; systemctl restart ai-assessment-backend'

say "等待后端就绪"
ssh "$SERVER" 'for i in $(seq 1 25); do sleep 3; ss -tln | grep -q ":8081" && { echo "  后端已监听 8081"; exit 0; }; done; echo "  后端未在预期时间内启动，请查看 journalctl -u ai-assessment-backend"; exit 1'

say "对外自检"
curl -fsS -o /dev/null --max-time 10 "http://$HOST/" && echo "  应用首页 200"
curl -fsS -o /dev/null --max-time 10 "http://$HOST/photoelectric/" && echo "  朋友页面 200"
api_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "http://$HOST/api/questions/taxonomy")
[ "$api_code" = "401" ] && echo "  接口代理正常（未登录返回 401）" || echo "  ⚠ 接口返回 $api_code，请检查"

say "发布完成"
