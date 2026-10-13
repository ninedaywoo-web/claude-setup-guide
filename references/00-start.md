# Claude Max 防封奶妈级教程

目前，Claude 无法做到百分之百不封号。这份教程会尽可能全面地讲清楚网络环境、账号准备和使用中的注意事项，帮助你尽可能降低被封号的风险。如果不幸被封号，也有退款申请、申诉与清理的操作资料。

把项目文件夹交给 AI，打开 [SKILL.md](../SKILL.md)，就可以开始。AI 会先通读网络部署、浏览器与 iPhone 配置两篇，再根据你的设备和进度，每次带你做一小步。你做完发截图，或告诉它页面上出现了什么，再继续下一步。有 Codex 且电脑操作工具可用时，可以让它协助操作。

购买前可以先看下面的入口：需要检测 IP、核对节点，或需要购买账号，这里都已整理好，按自己的需要使用。

## 1. 优先查看

### 1.1 Claude IP 纯净度检测

[打开检测网站](https://ip.net.coffee/claude/)。使用计划注册时的网络检测，文档建议达到 80 分以上再注册。

### 1.2 账号购买网站

[打开账号网站](https://chuhai91.cc)。具体可购买的账号以网站在售情况为准。

### 1.3 Ping0 节点检测凭证

[打开 Ping0 IP 检测](https://ping0.cc/)。连接要检查的节点，在实际准备使用的浏览器环境里检测，查看出口地区、ASN / 运营商、IP 类型、风控值、是否原生 IP 和共享人数。

把检测时间、设备与浏览器环境、节点名称和页面结果记到本机 `.local/progress.md`；截图先隐藏完整 IP，再保存到 `.local/`，作为本次节点检测的凭证。换节点或环境后重新检测，不能用别人的截图代替自己的结果。具体检查和记录方式见[浏览器检查步骤](02-browser-iphone.md#14-配好后先检查再注册)。

Ping0 的风控值越低表示该站评估的风险越低，与前面 Claude 检测的“80 分以上”不是同一个量表。它的结果作为辅助证据，仍需完成实际出口、IPv6、DNS、WebRTC 和断线行为检查。

## 2. 配置教程

### 2.1 [纯净魔法从零部署](01-network.md)

以 DMIT 为例，从 VPS 购买、登录和节点部署开始，完成 Mac / Karing 配置，并附 Windows、安卓操作和常见问题排查。

### 2.2 [指纹浏览器与 iPhone 网络配置](02-browser-iphone.md)

AdsPower、本机 HTTP 代理、邮箱与 Claude 注册，以及 iPhone 镜像带做、网络、时区和客户端检查。手机首次注册、登录或订阅前，优先由 Codex Computer Use 操作镜像导入节点；镜像问题先排查修复，小火箭使用「全局路由 → 代理」并完成手机独立验收。

### 2.3 [Apple 账号、礼品卡与内购](03-apple.md)

Apple 账号准备、App Store 登录、礼品卡充值和 App 内订阅。

购买未完成、无法购买或需要 Apple 复核时，进入[Apple 购买受限人工支持](07-apple-purchase-support.md)：Codex 负责官方入口与客服沟通，用户负责登录和 Support PIN 输入，记录处理答复与具体重试安排。

### 2.4 [退款、封号申诉与旧账号清理](04-recovery.md)

按付款渠道申请退款、准备申诉资料，以及备份和清理登录残留。“退出旧账号”的独立操作段落待补充。

### 2.5 [注册／登录前自检](06-before-login.md)

在注册、登录 Claude 或授权 Claude Code 前，让 AI 核对浏览器、电脑与手机时区、IP 检测评分、IPv6、WebRTC、DNS 和断线行为；未完成的先补齐。

## 3. 给 AI 的带做说明

[AI 从零带做指南](05-ai-walkthrough.md)。开始前完整读取网络与浏览器两篇，其他资料按阶段读取。VPS 选购以文档推荐的 DMIT 套餐为对照。DMIT 缺货时，最推荐[搬瓦工](https://bandwagonhost.com/order/ecommerce/Los%20Angeles/USCA_9)；其次并列推荐 [AKILE Cloud](https://akile.ai/) 与 [Hostinger KVM 1](https://www.hostinger.com/vps-hosting)。先匹配 DMIT 的优化线路，再对照硬件、流量和带宽，最后列出价格，不以十美元预算筛选。搬瓦工默认选 USCA_9 的 1 GB 档（49.99 美元/季），AKILE 默认选 LAXPremium-Mini（79.99 元/月），Hostinger 默认选 KVM 1（1 vCPU、4 GB、50 GB NVMe、4 TB）；不为对齐 DMIT 的内存自动升级。Hostinger 美国机房为 Phoenix 或 Boston，当前未核实同级大陆优化线路；官网月价与续费金额按付款周期分别核对。具体配置、流量差别和库存见[网络教程的套餐对照](01-network.md)。选择商家后再比较是否预留云端运行配置。
