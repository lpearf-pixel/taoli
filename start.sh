#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

command -v python3 >/dev/null 2>&1 || { echo '未找到 python3。'; exit 1; }
command -v docker >/dev/null 2>&1 || { echo '未找到 docker。'; exit 1; }
docker compose version >/dev/null 2>&1 || { echo 'Docker Compose 不可用。'; exit 1; }

python3 scripts/render_config.py

echo '1/3 拉取 Xray 镜像……'
docker compose pull xray-chain

echo '2/3 验证 Xray 配置……'
docker compose run --rm --no-deps xray-chain \
  run -test -c /usr/local/etc/xray/config.json

echo '3/3 启动链式代理……'
docker compose up -d --force-recreate xray-chain

docker compose ps xray-chain
printf '\n启动完成。下一步执行：./test.sh\n'
