# Windows 带做：从 VPS 到电脑与手机验收

按[统一控制层](17-workflow-controller.md)推进，本章提供 Windows 电脑对应的客户端、网络切换、AdsPower、时区和手机配合步骤；VPS 仍统一选用 Linux（Debian 12），账号与订阅沿用主流程。

## 1. 确认设备与环境

沿用开场记录的设备信息，补齐 Windows 版本、x64／ARM64 架构、管理员授权条件和当前 VPN 软件及接管方式（可在「设置 → 系统 → 系统信息」查看）。默认电脑路线为 **Windows → v2rayN → AdsPower（免费版）**；手机为 iPhone 时按图解手动配小火箭与 Apple 内购，Android 时验收手机网络后走[安卓官网 Google Pay 分支](11-android-web-pay.md)。

命令执行使用本机已验证的 Python 3.9+ 入口（`py -3`、`python` 或 `python3`）和 `curl.exe`。

## 2. 保留旧 VPN 并部署 Linux VPS

1. **留好旧 VPN 恢复方式**：记录旧客户端名称、原节点和重连按钮，部署与单测新节点期间保持旧 VPN 运行。
2. **选购与连接 VPS**：商家、套餐与图解沿用[网络教程](01-network.md)和[搬瓦工图解](09-vps-purchase.md)。在本机 PowerShell 用 `ssh -V` 确认 OpenSSH 可用后，按服务商实际端口、用户和密钥／密码连接：
   ```powershell
   ssh -p <SSH端口> <登录用户>@<服务器地址>
   ssh -i "<私钥实际完整路径>" -p <SSH端口> <登录用户>@<服务器地址>
   ```
   私钥权限按 Windows 文件 ACL 处理。每条命令明确标出是在「本机 PowerShell」还是「VPS Linux 终端」运行；进入 VPS 后通过 `workflow.py run` 完成 `server_preflight`、`server_deploy` 与节点导出。

## 3. 安装 v2rayN 并导入节点

从 [v2rayN 官方发布页](https://github.com/2dust/v2rayN/releases)下载匹配 Windows 架构的稳定包，解压到固定可写目录运行。通过剪贴板导入 `.local/network/node.txt` 中的 VLESS 链接，核对节点参数并固定选中目标节点，读取客户端实际监听的本机 HTTP／混合入口端口（供测试与 AdsPower 使用）。

## 4. 先单测新节点，再切换 TUN＋全局

1. **独立测通**：保持旧 VPN 在线，关闭 v2rayN 的 TUN 和自动系统代理，运行 `workflow.py run --action probe_proxy`（内部调用 `curl.exe` 指定本机 HTTP 入口）确认新节点 HTTPS 正常且出口为目标 VPS。HTTP 失败先查监听与节点，确认不可用时再试实测可用的 SOCKS5。
2. **切换前告知恢复动作**：把按实际软件填好的恢复步骤发给客户：
   > 接下来切换网络，Codex 可能短暂重连。如果新线路连不上，请先关闭【v2rayN 的 TUN／连接】，再打开【旧客户端】选择【原节点】重连，恢复后发一句“继续”。
3. **切换与复验**：解除旧 VPN 接管，按需完成管理员授权，开启 v2rayN 的 **TUN＋全局**（固定目标节点）并**关闭／清除系统代理**，保留本机 HTTP 入口。运行 `workflow.py run --action probe_system` 验证新出口，再请客户发一条新消息确认 Codex 回复正常。
4. **电脑断线测试**：在 `computer_network` 阶段完成 1 次受控断线测试并确认恢复（后续 AdsPower 与手机阶段不再做断线测试）。切换失败时先恢复旧 VPN，再查本机内核、TUN 路由和日志。

### 6.1 HTTP 测通，TUN 后反复连接 VPS

**触发现象**：本机显式 HTTP 代理访问正常且出口为目标 VPS，但开启 TUN 后断网或测速一直“测试中”，日志大量重复 `accepted tcp:<VPS_IP>:443 [socks -> proxy]`（客户案例环境：Windows v2rayN 7.10.4 + Xray 25.1.1 + sing-box 1.11.5，疑似节点流量被 TUN 再次送回本机代理）。

先向客户说明：“单独代理已经测通，现在排查 TUN 接管后节点自身连接有没有绕回本机，查完路由立刻复测。”随后按序排查：
1. 保持旧 VPN 可恢复状态，记录当前配置与核心版本。
2. 读取 v2rayN、Xray、sing-box 实际进程路径、加载配置、监听端口和物理网卡；在 PowerShell 运行 `Find-NetRoute -RemoteIPAddress <实际VPS地址>` 对照 TUN 开关前后的路由。
3. 为正在使用的 VPS 地址配置持久生效的 TUN 路由排除（IPv4 单地址 `/32`，IPv6 为 `/128`）或正确物理网卡直连出口，修改后回读加载配置与路由确认生效。
4. 在新 TUN 独立接管、系统代理关闭状态下，用 `curl.exe --noproxy "*"` 验证实际出口、确认循环日志消失，并请客户发新消息确认 Codex 回复后提交 `computer_network`。

## 7. 配置 AdsPower 与电脑自检

1. **AdsPower（免费版）**：按[浏览器章节](02-browser-iphone.md)使用 **AdsPower 免费版**直接点左上角「新建环境」手动配置（系统选 Windows，无需付费 API）。代理填 v2rayN 本机 HTTP 入口（点检查代理通过），点「确定」前一次配齐 WebRTC 禁用、地理位置禁止、时区、噪音全关与真实硬件参数（WebGL 元数据／WebGPU／CPU／内存）。
2. **验收**：在打开的环境内核对实际出口、IPv6／DNS／WebRTC 及 NetCoffee、Ping0、Scamalytics 三站分数（浏览器阶段不做断线测试）。
3. **Windows 时区与定位（在手机代理连上后的 `timezone` 阶段执行）**：
   - 打开「设置 → 时间和语言 → 日期和时间」：关闭「自动设置时区」，手动选择已选方案（跟随节点城市或台北，自动处理夏令时），保留自动校时；可用 PowerShell `Get-TimeZone` 核对。
   - 打开「设置 → 隐私和安全性 → 位置」（Win10 为「设置 → 隐私 → 位置」）：关闭设备定位服务。
   - 返回复查自动时区已关闭、手动时区与手机及 AdsPower 一致、定位已关闭。

## 8. 浏览器通过后接手机与收尾

- **Windows＋iPhone**：按[浏览器与 iPhone 章节](02-browser-iphone.md)每轮标明操作设备、合并 1～3 个相连动作，电脑展示二维码、手机用 **Shadowrocket（小火箭）**扫码导入同一节点并设全局路由为「代理」。连上后先完成第 7 节时区与定位，再在手机浏览器独立核对 Ping0（记 Wi-Fi／蜂窝网络）、NetCoffee、Scamalytics、IPv6／DNS 与排除路由（**手机阶段不做断线测试**）。小火箭全局超时优先按[2.2.1 节](02-browser-iphone.md#221-小火箭全局超时先试-chrome-140)试 `Chrome 140`。
- **Windows＋Android**：手机配好同一节点并完成时区定位与网络验收后，按[安卓官网 Google Pay 分支](11-android-web-pay.md)提示风险并在手机浏览器完成登录与 Pro 订阅。
- **收尾验收**：手机订单与 Pro 权益确认后展示收尾说明结束交付（无需强制重启电脑）。

官方参考：[v2rayN 界面说明](https://github.com/2dust/v2rayN/wiki/Description-of-some-ui)、[常见问题](https://github.com/2dust/v2rayN/wiki/Faq)。
