# Xray VLESS → VMess Chain

一个尽量简单、可回滚的 Docker 项目，用 Xray-core 实现：

```text
本机或虚拟机
  → SOCKS5 127.0.0.1:1286
  → Vultr VLESS + REALITY（第一跳）
  → 美国 VMess 普通 TCP（最终出口）
  → 目标网站
```

目标网站看到的是美国 VMess 节点的出口 IP。

本项目沿用旧 VMess→VMess 配置的链式方式：美国 VMess 出站使用 `proxySettings.tag=transit`，只把原来的第一跳 VMess 替换成 VLESS + REALITY。美国 VMess 是普通 TCP，因此 `transportLayer=false`，并且两跳都关闭 Mux。

## 1. 下载

```bash
git clone https://github.com/lpearf-pixel/taoli.git xray-vless-vmess-chain
cd xray-vless-vmess-chain
```

> 当前先使用你的空仓库 `taoli` 承载项目；项目内部名称为 `xray-vless-vmess-chain`。

## 2. 填写变量

```bash
cp .env.example .env
nano .env
```

必须填写四个凭据：

```dotenv
VLESS_UUID=完整的_VLESS_UUID
REALITY_PUBLIC_KEY=完整的_REALITY_Public_Key
REALITY_SHORT_ID=完整的_REALITY_Short_ID
US_VMESS_UUID=完整的_美国_VMess_UUID
```

地址和端口已作为默认变量保存，可按服务商页面修改。不要把 `.env` 提交到 GitHub。

## 3. 启动

```bash
chmod +x *.sh scripts/render_config.py
./start.sh
```

`start.sh` 会依次：

1. 根据 `.env` 生成 `config/config.json`；
2. 拉取固定版本 Xray-core；
3. 使用 `xray run -test` 校验配置；
4. 启动容器。

## 4. 验证

```bash
./test.sh
```

或手工测试：

```bash
curl --proxy socks5h://127.0.0.1:1286 https://ipinfo.io
```

查看日志：

```bash
./logs.sh
```

停止：

```bash
./stop.sh
```

## 端口冲突

默认只监听 Mac 本机：

```dotenv
CHAIN_BIND_HOST=127.0.0.1
CHAIN_LOCAL_PORT=1286
```

需要让虚拟机访问时，将绑定地址改为 Mac 虚拟网络可访问的地址，或临时设为 `0.0.0.0`。使用 `0.0.0.0` 会向局域网开放无密码 SOCKS5，必须配合防火墙限制来源。

## 排错

确认容器运行的是 Xray，而不是 V2Fly：

```bash
docker exec xray-vless-vmess-chain xray version
```

检查容器状态：

```bash
docker compose ps
docker compose logs --tail=200 xray-chain
```

当前配置不包含 DoH、自定义 DNS、分流或 Mux，先只验证两跳链路，避免额外变量干扰。
