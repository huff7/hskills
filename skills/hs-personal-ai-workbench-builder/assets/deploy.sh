#!/usr/bin/env bash
#
# deploy.sh — 零成本国内方案（deploy.md 路线 B）一键部署脚本
#
# 自动化做两件事：
#   1) Docker 构建镜像 + 跑容器（端口映射 + 数据卷持久化，SQLite 留在宿主机）
#   2) Cloudflare Tunnel 建隧道 + 路由子域 + 后台起隧道，把子域指向本机容器
#
# 脚本【不代劳】的手工前置（需你先做完）：
#   A. 申请一个稳定子域（eu.org / is-a.dev 免费，或付费真域名）—— deploy.md §2.1
#   B. 把子域接入 Cloudflare（Add a Site → Free）—— deploy.md §2.2
#   C. 本机跑过一次 `cloudflared tunnel login`（浏览器授权绑定账号）—— 只需一次
#   D. 准备 assets/config.json（个性化品牌/城市/扫描根，复制 config.example.json 改）
#
# 用法：
#   ./deploy.sh -d workbench.yourname.eu.org [--tunnel workbench] [--port 8788] [--image workbench]
#   ./deploy.sh -d workbench.yourname.eu.org --no-tunnel      # 只跑 Docker，不起隧道
#   ./deploy.sh -d workbench.yourname.eu.org --skip-build     # 镜像已存在，跳过 build
#
# 停止：
#   容器：  docker rm -f workbench
#   隧道：  pkill -f "cloudflared tunnel run"   （或 launchd/systemd 停对应服务）
#
set -euo pipefail

# ── 默认参数 ──────────────────────────────────────────────
DOMAIN=""            # 必填：完整子域，如 workbench.yourname.eu.org
TUNNEL_NAME="workbench"
PORT="8788"
IMAGE="workbench"
NO_TUNNEL=0
SKIP_BUILD=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 颜色日志 ──────────────────────────────────────────────
log()  { printf '\033[36m[deploy]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[warn]\033[0m %s\n' "$*"; }
err()  { printf '\033[31m[err]\033[0m %s\n' "$*" >&2; }

usage() {
  grep '^#' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

# ── 解析参数 ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--domain)    DOMAIN="$2"; shift 2;;
    -n|--tunnel)    TUNNEL_NAME="$2"; shift 2;;
    -p|--port)      PORT="$2"; shift 2;;
    --image)        IMAGE="$2"; shift 2;;
    --no-tunnel)    NO_TUNNEL=1; shift;;
    --skip-build)   SKIP_BUILD=1; shift;;
    -h|--help)      usage;;
    *) err "未知参数: $1"; usage;;
  esac
done

[[ -z "$DOMAIN" ]] && { err "缺少必填参数 -d/--domain <子域>"; usage; }

cd "$SCRIPT_DIR"

# ── 0. 前置检查 ────────────────────────────────────────────
log "前置检查…"
if ! command -v docker >/dev/null 2>&1; then
  err "未找到 docker，请先安装 Docker（https://docs.docker.com/get-docker/）"
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  err "docker 守护进程未运行，请先启动 Docker Desktop / dockerd"
  exit 1
fi
if [[ "$NO_TUNNEL" -eq 0 ]]; then
  if ! command -v cloudflared >/dev/null 2>&1; then
    err "未找到 cloudflared。请先安装（brew install cloudflared）并跑过一次 'cloudflared tunnel login'。"
    err "若只想跑 Docker 不起隧道，加 --no-tunnel。"
    exit 1
  fi
  # 验证已登录（tunnel list 需要有效证书）
  if ! cloudflared tunnel list >/dev/null 2>&1; then
    err "cloudflared 尚未登录或证书失效。请先手动跑一次：cloudflared tunnel login"
    exit 1
  fi
fi

# ── 1. 构建镜像 ────────────────────────────────────────────
if [[ "$SKIP_BUILD" -eq 0 ]]; then
  log "构建镜像 $IMAGE …"
  docker build -t "$IMAGE" .
else
  log "跳过 docker build（--skip-build）"
fi

# ── 2. 运行容器（端口映射 + 数据卷）────────────────────────
log "准备数据卷目录…"
mkdir -p "$SCRIPT_DIR/data"

# 现有同名容器先停掉（幂等重跑）
if docker ps -a --format '{{.Names}}' | grep -qx "$IMAGE"; then
  log "发现已存在容器 $IMAGE，先移除…"
  docker rm -f "$IMAGE" >/dev/null
fi

# 构建容器运行参数数组（只用一次，避免重复 --name/-p）
RUN_ARGS=(--name "$IMAGE" --restart always
  -p "${PORT}:${PORT}"
  -e "PORT=${PORT}"
  -v "${SCRIPT_DIR}/data:/app/data")

# 若用户提供了个性化 config.json 则挂载覆盖（否则用镜像内烘焙的默认）
if [[ -f "$SCRIPT_DIR/config.json" ]]; then
  RUN_ARGS+=(-v "${SCRIPT_DIR}/config.json:/app/config.json")
  log "挂载个性化 config.json"
else
  warn "未找到 config.json，使用镜像内默认示例配置（请复制 config.example.json 为 config.json 并个性化后重跑）。"
fi

RUN_ARGS+=("$IMAGE")
log "启动容器 ${IMAGE}（--restart always，端口 ${PORT}）…"
docker run -d "${RUN_ARGS[@]}" 2>&1 | sed 's/^/  /'

# 等待本机端口就绪
log "等待本机 :${PORT} 就绪…"
for i in $(seq 1 20); do
  if curl -s -o /dev/null "http://localhost:${PORT}/" 2>/dev/null; then
    log "本机服务已就绪：http://localhost:${PORT}/"
    break
  fi
  sleep 1
  [[ "$i" -eq 20 ]] && { err "本机服务 20s 内未就绪，检查 'docker logs $IMAGE'"; }
done

# ── 3. Cloudflare Tunnel ──────────────────────────────────
if [[ "$NO_TUNNEL" -eq 1 ]]; then
  log "已跳过隧道（--no-tunnel）。手动访问：http://localhost:${PORT}/"
  log "若要对外公网，请按 deploy.md §2.3–2.5 手工起隧道。"
  exit 0
fi

# 3a. 建命名隧道（已存在则复用）
if cloudflared tunnel list 2>/dev/null | grep -qw "$TUNNEL_NAME"; then
  log "隧道 '$TUNNEL_NAME' 已存在，复用。"
else
  log "创建命名隧道 '$TUNNEL_NAME' …"
  cloudflared tunnel create "$TUNNEL_NAME"
fi

# 3b. 路由子域（CNAME 已存在则跳过，幂等）
if cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN" 2>&1 | grep -qi "already\|exists"; then
  warn "子域 $DOMAIN 已路由到隧道（幂等跳过）。"
else
  log "子域 $DOMAIN 已路由到隧道 '$TUNNEL_NAME'。"
fi

# 3c. 后台起隧道，指向本机容器
TUNNEL_LOG="$SCRIPT_DIR/tunnel.log"
log "后台启动隧道 → http://localhost:${PORT} （日志：$TUNNEL_LOG）"
nohup cloudflared tunnel run --url "http://localhost:${PORT}" "$TUNNEL_NAME" \
  >"$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!
sleep 3
if kill -0 "$TUNNEL_PID" 2>/dev/null; then
  log "隧道进程 PID=$TUNNEL_PID 已启动。"
else
  err "隧道启动失败，查看 $TUNNEL_LOG"
  exit 1
fi

# ── 4. 验证 ────────────────────────────────────────────────
PUBLIC="https://${DOMAIN}"
log "等待公网地址 $PUBLIC 生效（最长 15s）…"
for i in $(seq 1 15); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "$PUBLIC" 2>/dev/null || echo 000)
  if [[ "$CODE" == "200" ]]; then
    log "✅ 公网可访问：$PUBLIC （HTTP 200）"
    break
  fi
  sleep 1
  [[ "$i" -eq 15 ]] && warn "公网暂未返回 200（当前 $CODE），DNS 可能还在传播，稍后重试 curl $PUBLIC"
done

# ── 5. 交付提示 ────────────────────────────────────────────
echo
log "===== 部署完成 ====="
log "稳定公网地址：$PUBLIC"
log "数据落点：本机 $SCRIPT_DIR/data（SQLite，不随容器删除丢失）"
log "保活：Docker 已 --restart always；隧道进程 PID=$TUNNEL_PID（建议用 launchd/systemd 设为开机自启常驻）"
log "手机加主屏幕：iOS Safari 分享→添加到主屏幕；Android Chrome ⋮→安装应用。"
log "验证 PWA：打开 $PUBLIC，确认离线重开仍能看到壳（service worker 预缓存）。"
