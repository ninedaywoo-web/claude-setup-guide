# Claude Max 防封奶妈级教程

带做由[统一控制层](17-workflow-controller.md)返回当前阶段：完成启动读取后运行 `python3 scripts/workflow.py init`，每阶段取得实际结果后提交，再按程序返回的下一步继续。

目前，Claude 无法做到百分之百不封号。这份教程会尽可能全面地讲清楚网络环境、账号准备和使用中的注意事项，帮助你尽可能降低被封号的风险。如果不幸被封号，也有退款申请、申诉与清理的操作资料。

把项目文件夹交给 AI，打开 [SKILL.md](../SKILL.md)，就可以开始。AI 会先通读网络部署、浏览器与 iPhone 配置两篇，再根据你的设备和进度，每次带你做一小步。你做完发截图，或告诉它页面上出现了什么，再继续下一步。有 Codex 且电脑操作工具可用时，可以让它协助操作。

## 第一个问题：设备有没有用过被封禁的 Claude 账号

**您准备使用的电脑或手机，之前有没有登录过被 Claude 封禁的账号？**

有的话，请告诉 Codex 是哪台设备、用过浏览器还是 App；它会先按实际情况推荐[旧登录残留清理](04-recovery.md#有封禁经历时先处理旧登录残留)。Mac 有配套清理 Skill；iPhone 建议删除并重新下载官方 Claude App。清理前先检查和备份，不能保证清除平台记录或解除封禁。没有这段经历，就进入设备确认与搭配说明。

## 确认设备后，说明搭配与阅读版

**设备搭配优先选 Mac＋iPhone，其次是 Windows＋iPhone；Windows＋Android 暂不作为新手首选。**Mac 的 iPhone 镜像和操作工具可用时，Codex 能协助配置手机；Windows 默认需要您按图操作，再提供手机截图或日志排查。默认 Apple 内购路线需要 iPhone 或 iPad，iPad 不套用 iPhone 镜像。Android 要另外确认可用支付渠道，Google Pay 仅在实际付款页提供时使用。Codex 会在确认电脑和手机类型后，当场按[设备搭配说明](13-reader-guide.md#确认设备后当场说明搭配与需要亲自操作的部分)讲清楚您需要配合的部分，验证和付款仍由您本人完成。

另外，这里有一套[给您自己看的图文 PDF](../assets/reading/README.md)，讲具体操作和一些基本原理，建议保存到本地。您可以让 Codex 帮您保存；哪一步不明白就翻对应篇目，也可以问 Codex“这一步在 PDF 第几页”。PDF 里看不懂的内容，截图给 GPT 问就可以，不用先读完整套再开始。

## 完成设备和 Google 账号准备后，进入 VPS

此时再确认您的节点进度。VPS 就是一台租来的云端服务器，我们用它搭建自己的 VPN，也就是“自建魔法节点”。买 VPS 的网站是服务商，VPS 是您租到的服务器。

您现在是还没买 VPS、买了但没配置，还是已经有自己搭建并能管理的节点？平时买的梯子或机场订阅不算这里说的自建节点。没有也没关系，跟着程序一步步做；已经有服务器就先检查，不用重复买。自建节点是否合适，配置好后还要检测。

购买前可以先看下面的入口：需要检测 IP、核对节点，或需要购买账号，这里都已整理好，按自己的需要使用。

## 1. 优先查看

### 1.1 Claude IP 纯净度检测

[打开检测网站](https://ip.net.coffee/claude/)。使用计划注册时的网络检测，文档建议分数约 80 或更高，结合其余检查再登录。

### 1.2 账号购买网站

- 原有综合账号渠道：[chuhai91](https://chuhai91.cc)。
- Google 账号补充渠道：[GmailBuy](https://gmailbuy.com/)。
- Apple ID 补充渠道：[xintaikeji](https://xintaikeji.eu.org/)。

原有渠道保留，后两项作为补充。AI 按用户当前需要的账号类型提供对应链接；已有可用账号就复用，不要求重复购买。商品地区、交付字段、价格、库存和售后以实际商品页为准。

### 1.3 Ping0 节点检测凭证

[打开 Ping0 IP 检测](https://ping0.cc/)。连接要检查的节点，在实际准备使用的浏览器环境里检测，查看出口地区、ASN / 运营商、IP 类型、风控值、是否原生 IP 和共享人数。

把检测时间、设备与浏览器环境、节点名称和页面结果记到本机 `.local/progress.md`；截图先隐藏完整 IP，再保存到 `.local/`，作为本次节点检测的凭证。换节点或环境后重新检测，不能用别人的截图代替自己的结果。具体检查和记录方式见[浏览器检查步骤](02-browser-iphone.md#14-配好后先检查再进入手机)。

Ping0 的风控值越低表示该站评估的风险越低，与前面 Claude 检测的“80 分以上”不是同一个量表。它的结果作为辅助证据，仍需完成实际出口、IPv6、DNS、WebRTC 和断线行为检查。

### 1.4 Scamalytics 风险对照

[打开 Scamalytics](https://scamalytics.com/ip)，查询当前代理出口 IP，建议风险值低于 10。三站分别记录：NetCoffee 约 80 分或更高；Ping0 风险值低于 30 可接受参考、优先低于 25；Scamalytics 低于 10。不能将高分和低风险数值直接平均。

### 1.5 Google 账号与默认交付路线

开始时先确认有没有自己可用的 Google 账号；没有则提供[原有购号网站](https://chuhai91.cc)及 [Google 账号补充渠道 GmailBuy](https://gmailbuy.com/)，选择商家标明的美区 Google 账号。交付串和 2FA 使用方法见[Google 账号准备](08-google-account.md)。账号由用户自己保管，不发给 AI。

默认顺序：账号与设备准备 → VPS → Mac Karing／Windows v2rayN（系统代理关闭、TUN＋全局开启）→ AdsPower → 按平台带做 iPhone 小火箭全局代理 → 电脑／手机时区选择与定位权限设置 → 核对美区 Apple ID、等待安排与客户选择记录和余额／礼品卡 → 保持手机节点开启，下载 Claude → 使用 Google 账号登录 Claude 并订阅 Pro → 订单与手机权益确认，结束交付。手机主要用于登录和订阅，Claude Code 教学不在交付范围。

## 2. 配置教程

### 2.1 [纯净魔法从零部署](01-network.md)

以 DMIT 为例，从 VPS 购买、登录和节点部署开始，完成 Mac / Karing 配置，并附 Windows、安卓操作和常见问题排查。

### 2.2 [指纹浏览器与 iPhone 网络配置](02-browser-iphone.md)

AdsPower、本机 HTTP 代理、邮箱与 Claude 注册，以及 iPhone 镜像带做、网络、时区和客户端检查。手机首次注册、登录或订阅前，Mac 优先由 Codex Computer Use 操作镜像导入节点并排查镜像问题；Windows 默认图解和截图带做，小火箭默认使用「全局路由 → 代理」，随后按具体设置路径完成电脑／手机时区和定位权限设置，分别验收后接手机登录和订阅。

### 2.3 [Apple 账号、礼品卡与内购](03-apple.md)

Apple 账号准备、App Store 登录、礼品卡充值和 App 内订阅。网络自检通过后，单独确认账户新旧；根据客户反馈，新注册或刚接手的成品号建议先正常使用约两天，再充值和订阅。

购买未完成、无法购买或需要 Apple 复核时，进入[Apple 购买受限人工支持](07-apple-purchase-support.md)：Codex 负责官方入口与客服沟通，用户负责登录和 Support PIN 输入，记录处理答复与具体重试安排。

### 2.4 [退款、封号申诉与旧账号清理](04-recovery.md)

按付款渠道申请退款、准备申诉资料，以及备份和清理登录残留。旧账号由客户自行退出，本项目不提供具体退出指导。

### 2.5 [注册／登录前自检](06-before-login.md)

在注册、登录 Claude 或授权 Claude Code 前，让 AI 核对浏览器、电脑与手机时区、IP 检测评分、IPv6、WebRTC、DNS 和断线行为；未完成的先补齐。

### 2.6 [Windows 专门流程](10-windows.md)

Windows 本机连接 Linux VPS，默认用 v2rayN 与 AdsPower。先保留旧 VPN 测新节点，再切换 TUN＋全局，检查实际出口与 Codex 新回复。Windows＋iPhone 用图解带做；Android 手机网络通过后可按下面的官网 Google Pay 基础指引继续。真实 Windows 整机验收仍待完成。

### 2.7 [安卓官网 Google Pay 基础订阅](11-android-web-pay.md)

配置并验收安卓手机节点后，用手机浏览器进入 Claude 官网；实际显示 Google Pay 时才选择支付。付款前主动告知目前案例较少、可能存在风险，以及作者目前掌握的封号后无法退款反馈；用户接受后再继续。这是官网付款，不是 Google Play 内购，不套用 Apple 充值与退款步骤。

## 3. 给 AI 的带做说明

[AI 从零带做指南](05-ai-walkthrough.md)。开始前完整读取网络与浏览器两篇，其他资料按阶段读取。VPS 选购以文档推荐的 DMIT 套餐为对照。DMIT 缺货时，最推荐[搬瓦工](https://bandwagonhost.com/order/ecommerce/Los%20Angeles/USCA_9)；其次并列推荐 [AKILE Cloud](https://akile.ai/) 与 [Hostinger KVM 1](https://www.hostinger.com/vps-hosting)。先匹配 DMIT 的优化线路，再对照硬件、流量和带宽，最后列出价格，不以十美元预算筛选。搬瓦工默认选 USCA_9 的 1 GB 档（49.99 美元/季），AKILE 默认选 LAXPremium-Mini（79.99 元/月），Hostinger 默认选 KVM 1（1 vCPU、4 GB、50 GB NVMe、4 TB）；不为对齐 DMIT 的内存自动升级。Hostinger 美国机房为 Phoenix 或 Boston，当前未核实同级大陆优化线路；官网月价与续费金额按付款周期分别核对。具体配置、流量差别和库存见[网络教程的套餐对照](01-network.md)。套餐仅按网络节点用途选择。
