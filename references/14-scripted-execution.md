# 确定性执行层

用于部署服务器、导出参数、固定网络请求、状态记录和三站评分汇总。按原交付顺序调用 `scripts/network.py`；VPN 切换由现有客户端流程完成。

## 调用约定

由 AI 准备输入、调用脚本并读取 JSON 结果。普通步骤成功后自行继续，不每步询问用户；遇到缺失信息、本人验证、购买付款或现有教程要求的网络恢复确认时才交接。失败先看 `error` 与当前状态，不盲目重试变更操作。

需要 Python 3.9+、原生 OpenSSH 和 curl。Windows 使用可用的 `py -3` 或 `python`，脚本调用 `curl.exe`。

输入与输出文件保存在本项目 `.local/`；聊天展示执行结果，密码、密钥和令牌留在本机。默认输入 `.local/network/input.json`。只做检测时可省略 `server` 和 `ssh`；部署时需要两者。示例地址是文档专用，必须换成当前客户实值：

```json
{
  "context": "customer-device-node-session-1",
  "ssh": {
    "host": "203.0.113.10",
    "user": "root",
    "port": 22,
    "identity_file": "/actual/private/key",
    "sudo": false,
    "batch_mode": true
  },
  "server": {
    "address": "203.0.113.10",
    "port": 18555,
    "panel_port": 18899,
    "sni": "www.microsoft.com"
  },
  "probe": {
    "proxy": "http://127.0.0.1:actual-port",
    "expected_exit_ipv4": "203.0.113.10"
  }
}
```

`context` 标识本次客户、设备、节点与网络配置组合，不填账号秘密。输入发生变化会使旧证据失效。客户端网络栈、规则、旧 VPN 接管状态变化但输入没变时，先执行 `invalidate`，再重新测受影响项目。恢复对话沿用同一项目，不混用客户目录。

首次 SSH 在真实终端核对主机指纹。默认 `batch_mode: true` 使用已可用的密钥／代理认证；密码登录可在真实交互终端设置 `batch_mode: false`，密码由用户在 SSH 隐藏提示输入，不能写入 JSON。用户和 SSH 端口按实际值填写；非 root 登录仅在已有 `sudo -n` 权限时设置 `sudo: true`。不能登录、缺 Python 或 sudo 不可用时先按原教程处理，不自动改 SSH 权限。

## 服务器与节点

```bash
python3 scripts/network.py preflight
python3 scripts/network.py deploy
python3 scripts/network.py export
```

- `preflight` 只读检查 Linux、amd64／arm64、systemd、权限、磁盘、端口及目标网站 TLS 1.3。云安全组和外部可达性仍待实测。
- `deploy` **仅支持全新服务器，或本脚本自己创建的部署**。锁定 3x-ui v3.10.2 官方发行包并校验 SHA-256；附带 Xray v26.10.10。客户端连接按原教程实测，Karing 故障沿用既有修复顺序。
- 已有其他面板返回 `existing_panel_requires_manual_path`，沿原教程检查和复用；首版部署脚本只管理自己创建的安装。
- 节点 UUID、密钥和 Short ID 在创建之前持久保存到服务器 `/var/lib/claude-setup-network/receipt.json`。失败后重新执行先读回面板，复用同一节点；遇到人工改动返回 `node_config_drift`，不自动覆盖。
- 安装位置 `/usr/local/x-ui`，服务 `x-ui.service`，数据库 `/etc/x-ui`。不做系统全量升级，不改防火墙。开放节点 TCP 端口需要按实际云安全组与服务器防火墙核对。
- 面板监听 `127.0.0.1`，通过 SSH 隧道管理，不安装公网 SSL。用实际 SSH 参数建立 `ssh -N -L <本地管理端口>:127.0.0.1:<面板端口> ...`，在本机浏览器访问 `http://127.0.0.1:<本地管理端口>/<base_path>/`。已有面板按原教程管理。
- `deploy` 结束后重新建立 SSH 连接，读回节点并检查服务、Xray 状态与本机监听。`export` 同样先复查再导出。成功后进入客户端导入与线路检测。

导出文件：`.local/network/node.txt` 是 VLESS 链接；`.local/network/panel-private.json` 是面板登录资料。均为私密文件，供本机导入。只在本次 `deploy`／`export` 成功后使用它们；失败／失效后磁盘可能保留旧文件，不能按“文件存在”判定有效。标准输出只给状态与文件路径，不显示密码、链接、密钥或完整 IP。服务端执行回执含秘密，只保留在服务器受限目录。脚本新部署直接导入 VLESS 链接，因此关闭未使用的默认订阅服务。

端口支持 1–65535，检查实际占用情况。节点连接失败时按原网络章节诊断。

## 独立测通与切换后复测

```bash
python3 scripts/network.py probe --route proxy
# 按原教程安排恢复方法，完成旧 VPN → 新客户端交接后：
python3 scripts/network.py invalidate
python3 scripts/network.py probe --route system
python3 scripts/network.py status
```

`proxy` 强制请求走指定的本机 HTTP／混合端口，忽略 `NO_PROXY` 和 curl 用户配置；失败不回退直连。首版仅支持无需认证的回环入口；已有入口要求认证时沿原教程测试，不为迁就脚本关闭认证。`system` 禁用 curl 显式／环境代理，让请求走当前系统路由。系统代理、TUN 和旧 VPN 接管状态通过客户端实际设置核对。

两种方式都实测两个 IPv4 出口服务与一个 HTTPS 204 地址：至少一个出口服务返回有效 IPv4，所有取得的出口都与预期一致，并且 HTTPS 204 成功才判本次请求通过。一个服务不可用会在记录中保留；两站出口不一致不通过。预期出口来自实际 VPS／节点核验，不能把检测返回的任意 IP 自动填作预期。

探针覆盖 IPv4 出口和 HTTPS 请求；DNS、IPv6、WebRTC、浏览器与手机检查按各自章节完成。VPN 切换后实际确认 Codex 能收到新回复。

## 三站结果与建议

在当前 AdsPower 环境／手机浏览器打开 NetCoffee、Ping0、Scamalytics。AI 自行观察并记录页面结果；工具不可用时由用户提供，验证码由用户完成。

将结果保存为 `.local/network/scores-input.json`：

```json
{
  "context": "与 input.json 一致",
  "environment": "adspower",
  "observed_at": "带时区的实际 ISO 时间",
  "exit_matches": true,
  "scores": {
    "netcoffee": {"value": 79, "evidence": "实际页面观察记录或本机凭证路径"},
    "ping0": {"value": 35, "evidence": "实际页面观察记录或本机凭证路径"},
    "scamalytics": {"value": null, "evidence": ""}
  }
}
```

`environment` 可为 `adspower`、`iphone_wifi`、`iphone_cellular`、`android_wifi`、`android_cellular`，分别记录。没有测到填 `null`；有分数时，`evidence` 填实际观察来源或本机凭证路径，无需为汇总另存一份文件。原教程要求保留的 Ping0 凭证照常保存。超过 24 小时的结果仍展示原值和时间，附复测建议；客户、节点或设备上下文不符时先核对来源。环境变化后复验受影响项。

```bash
python3 scripts/network.py scores --input .local/network/scores-input.json
```

| 网站 | 原建议参考 | 本地流程的轻微偏离容差 | 超出容差 |
| --- | --- | --- | --- |
| NetCoffee（高较好） | ≥80 | 75–79 | 建议复查 |
| Ping0（低较好） | <30，优先 <25 | 30–35 | 建议复查 |
| Scamalytics（低较好） | <10 | 10–15 | 建议复查 |

这些是流程建议值。79、35 这类轻微偏离继续流程；大幅偏离先复查，再建议检查或更换节点。三站分别展示原值和建议，缺失项标为未验证；实际出口与泄漏检测单独判断。

## 记录与恢复

`.local/network/state.json` 记录 `running / interrupted / stale / failed / passed / configured / exported / recorded`。`running` 遇到下次恢复会变成 `interrupted`。配置变化或 `invalidate` 保留旧结果但标为 `stale`。状态坏掉会停止，不静默重建。

`.local/network/report.json` 以 `scope: script_execution` 汇总每个脚本步骤的实际结果。`.local/progress.md` 只追加一次报告入口，保留原内容；VPN 交接、浏览器、手机和账号阶段的结果继续记在进度文件。

常见错误：`ssh_or_remote_protocol_failed` 先查 SSH、主机指纹、Python 与 sudo；`managed_config_changed` 先查当前输入是否属于同一客户；`node_config_drift` 对照现有节点；`panel_not_ready`／`xray_not_running` 查看服务器日志；探针 `failed` 检查本机入口、实际出口与 HTTPS。原始日志可能含秘密，只在本机检查，给用户显示脱敏结论。
