#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo '缺少 .env。'
  exit 1
fi

set -a
# shellcheck disable=SC1091
source ./.env
set +a

PORT="${CHAIN_LOCAL_PORT:-1286}"
EXPECTED_COUNTRY="${EXPECTED_EXIT_COUNTRY:-US}"
EXPECTED_IP="${EXPECTED_EXIT_IP:-}"
TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

echo "测试链路：127.0.0.1:${PORT} → VLESS/REALITY → 美国 VMess/TCP → 网站"
curl --fail --show-error --silent --location \
  --connect-timeout 15 \
  --max-time 60 \
  --proxy "socks5h://127.0.0.1:${PORT}" \
  --output "$TMP_FILE" \
  --write-out '连接=%{time_connect}s 首字节=%{time_starttransfer}s 总计=%{time_total}s 速度=%{speed_download}B/s\n' \
  https://ipinfo.io/json

python3 - "$TMP_FILE" "$EXPECTED_COUNTRY" "$EXPECTED_IP" <<'PY'
import json
import sys
from pathlib import Path

path, expected_country, expected_ip = sys.argv[1:]
data = json.loads(Path(path).read_text(encoding="utf-8"))
ip = str(data.get("ip", "")).strip()
country = str(data.get("country", "")).strip().upper()
print(f"出口 IP：{ip or '未知'}")
print(f"国家：{country or '未知'}")
print(f"城市：{data.get('city', '未知')}")
print(f"网络：{data.get('org', '未知')}")
if country != expected_country.strip().upper():
    raise SystemExit(f"出口国家不符合预期：预期 {expected_country}，实际 {country or '未知'}")
if expected_ip.strip() and ip != expected_ip.strip():
    raise SystemExit(f"出口 IP 不符合预期：预期 {expected_ip}，实际 {ip or '未知'}")
print("链路验证通过。")
PY
