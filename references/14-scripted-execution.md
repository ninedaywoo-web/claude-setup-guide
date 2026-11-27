# 确定性执行层

通过[统一控制层](17-workflow-controller.md)调用现有脚本完成服务器部署、节点导出、网络探针与三站评分汇总。

## 固定交付版本

| 组件 | 交付值 |
| --- | --- |
| Mac Karing | `1.2.25.2802`（Universal，macOS 12+） |
| 3x-ui 面板 | `3.10.2` |
| 服务端 Xray | `26.7.28` |
| REALITY minClientVer | `1.0.0` |
| 目标 / 两端 SNI | `www.cloudflare.com:443` / `www.cloudflare.com` |

Mac 通过 `python3 scripts/workflow.py run --action download_karing` 自动下载并校验 SHA-256，安装后核对应用版本 `1.2.25`、构建号 `2802`。

## 输入与首次 SSH

需 Python 3.9+（Windows 用 `py -3` 或 `python`）、OpenSSH 与 curl（Windows 自动调用 `curl.exe`）。输入配置保存在 `.local/network/input.json`（只做探针可省略 `ssh`/`server`）：

```json
{
  "context": "customer-device-node-session-1",
  "ssh": {"host": "203.0.113.10", "user": "root", "port": 22, "identity_file": "/actual/private/key", "sudo": false, "batch_mode": true},
  "server": {"address": "203.0.113.10", "port": 18555, "panel_port": 18899, "sni": "www.cloudflare.com"},
  "probe": {"proxy": "http://127.0.0.1:actual-port", "expected_exit_ipv4": "203.0.113.10"}
}
```

首次连接先在真实终端运行 `ssh -p <端口> [-i <私钥>] <用户>@<服务器>` 与商家控制台核对主机指纹后输入 `yes`；密码认证时设 `batch_mode: false` 由用户在终端隐藏输入。输入变化自动失效旧证据；仅客户端规则变化时可执行 `invalidate` 后重测。

## 服务器部署与导出

```bash
python3 scripts/workflow.py run --action server_preflight
python3 scripts/workflow.py run --action server_deploy   # 已有本脚本节点用 server_export
```

- `preflight`：只读核对 Linux、架构、systemd、磁盘、端口与目标 TLS 1.3。
- `deploy`：支持全新服务器或本脚本创建的部署，校验安装 3x-ui `3.10.2` + Xray `26.7.28`，节点凭据持久化在 `/var/lib/claude-setup-network/receipt.json`；已有其他面板返回 `existing_panel_requires_manual_path` 沿原教程复用。
- 面板监听 `127.0.0.1`（通过 SSH 本地转发管理）；部署结束自动读回服务与监听状态，并导出私密文件 `.local/network/node.txt` 与 `.local/network/panel-private.json`（仅存本机）。Karing 握手报错按[网络章节第十节](01-network.md#十karing-reality-握手失败)修复并同步回执重导。

## 独立测通与切换后复测

```bash
python3 scripts/workflow.py run --action probe_proxy   # 保留旧 VPN，走本机 HTTP 入口测新节点
python3 scripts/workflow.py run --action probe_system  # 切换 TUN+全局后，走系统路由复验
python3 scripts/network.py status
```

两项探针均实测两个 IPv4 出口服务与一个 HTTPS 204 地址，确认返回出口与目标 VPS 一致且 HTTPS 成功。重配客户端后执行 `workflow.py change --scope handoff --reason "客户端接管改变"` 重跑两项探针。

## 三站结果与建议

在 AdsPower 或手机浏览器打开 NetCoffee、Ping0、Scamalytics，将结果保存为 `.local/network/scores-input.json` 并运行 `browser_scores`（手机用 `phone_scores`）：

```json
{
  "context": "与 input.json 一致",
  "environment": "adspower",
  "observed_at": "带时区的实际 ISO 时间",
  "exit_matches": true,
  "scores": {
    "netcoffee": {"value": 80, "evidence": "实际页面观察或脱敏截图路径"},
    "ping0": {"value": 20, "evidence": "实际页面观察或脱敏截图路径"},
    "scamalytics": {"value": 0, "evidence": "实际页面观察或脱敏截图路径"}
  }
}
```

| 网站 | 建议参考 | 轻微偏离容差（照常推进） | 超出容差 |
| --- | --- | --- | --- |
| NetCoffee（越高越好） | ≥80 | 75–79 | 先复查 |
| Ping0（越低越好） | <30（优先 <25） | 30–35 | 先复查 |
| Scamalytics（越低越好） | <10 | 10–15 | 先复查 |

## 状态与排障

状态保存在 `.local/network/state.json`，汇总报告写入 `.local/network/report.json` 并链接到 `.local/progress.md`。常见错误按返回值直接排查：`ssh_or_remote_protocol_failed` 查 SSH／指纹／Python；`node_config_drift` 对照现有节点；`panel_not_ready`／`xray_not_running` 查服务日志；`xray_version_changed` 恢复固定 Xray 版本；探针失败核对监听入口、出口与 HTTPS。
