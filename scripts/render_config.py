#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
TEMPLATE_PATH = ROOT / "config" / "config.template.json"
OUTPUT_PATH = ROOT / "config" / "config.json"

REQUIRED = {
    "VLESS_ADDRESS",
    "VLESS_PORT",
    "VLESS_UUID",
    "REALITY_SERVER_NAME",
    "REALITY_PUBLIC_KEY",
    "REALITY_SHORT_ID",
    "US_VMESS_ADDRESS",
    "US_VMESS_PORT",
    "US_VMESS_UUID",
}

DEFAULTS = {
    "XRAY_LOG_LEVEL": "info",
    "VLESS_ENCRYPTION": "none",
    "VLESS_FLOW": "xtls-rprx-vision",
    "REALITY_FINGERPRINT": "chrome",
    "REALITY_SPIDER_X": "/",
    "US_VMESS_SECURITY": "auto",
}

INTEGER_KEYS = {"VLESS_PORT", "US_VMESS_PORT"}
PLACEHOLDER_RE = re.compile(r"^REPLACE_WITH_")


def parse_env(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit("缺少 .env：先执行 cp .env.example .env，然后填写节点参数。")

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise SystemExit(f".env 第 {line_number} 行格式错误：缺少 =")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'\"', "'"}:
            value = value[1:-1]
        values[key] = value
    return {**DEFAULTS, **values}


def require(values: dict[str, str], key: str) -> str:
    value = values.get(key, "").strip()
    if not value or PLACEHOLDER_RE.match(value):
        raise SystemExit(f"缺少有效参数：{key}")
    return value


def validate_uuid(values: dict[str, str], key: str) -> None:
    value = require(values, key)
    try:
        uuid.UUID(value)
    except ValueError as exc:
        raise SystemExit(f"{key} 不是完整 UUID：{value}") from exc


def validate_port(values: dict[str, str], key: str) -> None:
    value = require(values, key)
    try:
        port = int(value)
    except ValueError as exc:
        raise SystemExit(f"{key} 必须是数字：{value}") from exc
    if not 1 <= port <= 65535:
        raise SystemExit(f"{key} 必须在 1 到 65535 之间：{port}")


def validate(values: dict[str, str]) -> None:
    for key in REQUIRED:
        require(values, key)
    validate_uuid(values, "VLESS_UUID")
    validate_uuid(values, "US_VMESS_UUID")
    validate_port(values, "VLESS_PORT")
    validate_port(values, "US_VMESS_PORT")

    short_id = require(values, "REALITY_SHORT_ID")
    if len(short_id) > 16 or len(short_id) % 2 != 0 or not re.fullmatch(r"[0-9a-fA-F]+", short_id):
        raise SystemExit("REALITY_SHORT_ID 必须是偶数位十六进制字符串，最多 16 位。")

    if values["US_VMESS_SECURITY"] not in {
        "auto",
        "aes-128-gcm",
        "chacha20-poly1305",
        "none",
        "zero",
    }:
        raise SystemExit("US_VMESS_SECURITY 的值无效。")


def replace_placeholders(node: Any, values: dict[str, str]) -> Any:
    if isinstance(node, dict):
        return {key: replace_placeholders(value, values) for key, value in node.items()}
    if isinstance(node, list):
        return [replace_placeholders(value, values) for value in node]
    if isinstance(node, str) and node.startswith("__") and node.endswith("__"):
        key = node[2:-2]
        if key not in values:
            raise SystemExit(f"模板引用了未定义变量：{key}")
        value: Any = values[key]
        if key in INTEGER_KEYS:
            value = int(value)
        return value
    return node


def main() -> int:
    values = parse_env(ENV_PATH)
    validate(values)
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    rendered = replace_placeholders(template, values)
    OUTPUT_PATH.write_text(json.dumps(rendered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_PATH.chmod(0o600)
    print(f"已生成 {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
