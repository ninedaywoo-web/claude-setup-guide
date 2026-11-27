# 更好地用上 Claude Max 教学

本项目整理了从 VPS 搭建、电脑与手机网络配置到账号登录与订阅的完整操作步骤。由[统一控制层](17-workflow-controller.md)管理阶段顺序：启动读取后运行 `python3 scripts/workflow.py init`，按返回阶段逐步推进；配套 10 份[客户阅读版 PDF](../assets/reading/README.md) 供随时翻阅。日常使用目标是电脑上的 Claude 桌面端或 CLI。

## 全流程步骤总览

1. **开场核对**：先问设备是否登录过被 Claude 封禁的账号，有的话按[旧登录残留清理](04-recovery.md#有封禁经历时先处理旧登录残留)处理。
2. **设备与阅读版**：优先推荐 **Mac＋iPhone**，其次 **Windows＋iPhone**（[设备搭配说明](13-reader-guide.md#确认设备后当场说明搭配与需要亲自操作的部分)），并按需另存 PDF 阅读版。
3. **Google 账号准备**：已有可用 Gmail 直接复用；缺号默认推荐 **[GmailBuy](https://gmailbuy.com/)**「[【新号】全新美国谷歌账号(首登不弹二维码验证，推荐，不支持GV)](https://gmailbuy.com/home/goods.html?id=18&sid=18)」并提供备选 **[出海91](https://chuhai91.cc/)**（详见[Google 账号准备](08-google-account.md)）。
4. **VPS 与电脑网络**：选购并部署 VPS（默认 Debian 12），Mac 用 Karing、Windows 用 v2rayN，保留旧 VPN 测通新节点后切换为「系统代理关闭 + TUN + 全局」，在电脑网络阶段完成 1 次断线测试。
5. **AdsPower（免费版）**：免费版直接手动新建环境，配本机 HTTP 入口与真实硬件指纹，检查实际出口、IPv6／DNS／WebRTC 与三站评分。
6. **iPhone 小火箭、时区与订阅**：iPhone／iPad 统一使用 **Shadowrocket（小火箭）**「全局路由 → 代理」→ 统一电脑／手机／AdsPower 时区并设置定位 → 手机独立验收实际出口、三站评分与 IPv6／DNS → 核对美区 Apple ID 与新号约两天等待 → 支付宝快捷买礼品卡充值 → 保持节点开启下载官方 Claude App、Google 登录并订阅 Pro → 确认订单与权益结束交付。（安卓走[官网 Google Pay 分支](11-android-web-pay.md)。）

## 常用入口与参考标准

- **三站选线参考值**（电脑与手机各自独立记录，达标即继续下一步）：
  - [NetCoffee](https://ip.net.coffee/claude/)：约 80 分或更高
  - [Ping0](https://ping0.cc/)：风险值低于 30（优先低于 25），保存隐藏完整 IP 后的脱敏截图到 `.local/`
  - [Scamalytics](https://scamalytics.com/ip)：查询当前代理出口 IP，风险值低于 10
- **账号渠道**：Google 首推 [GmailBuy](https://gmailbuy.com/)（备选 [出海91](https://chuhai91.cc/)）；Apple ID 可选 [出海91](https://chuhai91.cc/) 或 [xintaikeji](https://xintaikeji.eu.org/)。以现场商品页实时价格与库存为准。

## 各专题目录

- [纯净魔法从零部署](01-network.md)｜[搬瓦工图解](09-vps-purchase.md)｜[VPS 库存核对](18-vps-stock.md)
- [指纹浏览器与 iPhone 网络配置](02-browser-iphone.md)｜[注册／登录前自检](06-before-login.md)
- [Apple 账号、礼品卡与内购](03-apple.md)｜[Apple 购买受限人工支持](07-apple-purchase-support.md)
- [退款、封号申诉与旧账号清理](04-recovery.md)｜[AI 从零带做指南](05-ai-walkthrough.md)
- [Windows 专门流程](10-windows.md)｜[安卓官网 Google Pay 分支](11-android-web-pay.md)
