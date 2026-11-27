# 更好地用上 Claude Max 教学

本项目是一套离线图文教程与 AI 带做程序，帮助用户按清晰步骤完成 VPS 部署、电脑与手机网络配置、登录与订阅。正文、操作配图和 10 份客户阅读版 PDF 均在仓库内；日常使用目标是电脑上的 Claude 桌面端或 Claude Code（CLI），AdsPower 负责网页登录与授权。

## 开始使用

**开始前请先在 Codex 新建一个空白对话，并优先选用常规稳定模型执行**（避开会反复追问所在地的模型），避免旧上下文干扰配置顺序。如果配置中途遇到 AI 偏离步骤（例如反复追问你在国内还是国外，或建议跳过手机直接网页登录），切换常规稳定模型、新建空白对话重发链接即可从本机进度无缝继续。

**把本仓库链接直接发给本机 Codex，它会自动下载、解压并校验最新项目完整包**（包含 AI 执行程序／流程与 `assets/reading/` 下的 10 份阅读版 PDF），并直接带您一步步配置。如果您已经手动下载解压，也可以把完整文件夹交给 Codex，从 [SKILL.md](SKILL.md) 开始。

### 给 AI 的启动规则

- 收到本仓库链接开始或恢复带做时，先按[链接交付启动流程](references/12-latest-start.md)实时读取 `main`、下载并校验最新完整包，从返回目录读取 [SKILL.md](SKILL.md) 并运行 `python3 scripts/workflow.py init`，按控制层返回阶段直接带做。
- 本地文件夹日常继续时，沿用 `SKILL.md` 启动规则；用户明确要求审查、解释或其他任务时按其要求处理。

## 交付主线一览

1. **开场核对与清理**：先确认设备是否登录过被封禁的 Claude 账号，按需执行内置的 [Mac 端清理 Skill](references/15-mac-cleanup.md) 或 [Windows 端清理 Skill](references/16-windows-cleanup.md)（iPhone 建议删除重装官方 App）。
2. **设备搭配与阅读版**：说明 Mac＋iPhone（首选）、Windows＋iPhone（可行）、Windows＋Android 的配合方式，介绍并按需另存[客户阅读版 PDF](assets/reading/README.md)。
3. **Google 账号准备**：自有可用 Gmail 直接复用；缺号默认推荐 GmailBuy 全新美国谷歌新号（`id=18&sid=18`）并提供备选出海91，买完展示首登时机原因与 2FA 取码图解（[详见 08 篇](references/08-google-account.md)）。
4. **VPS 与电脑网络**：按 `workflow.py policy` 选购并部署 VPS（Debian 12、3x-ui v3.10.2、Xray 26.7.28、REALITY Cloudflare SNI），Mac 使用固定版本 Karing `1.2.25.2802`（Windows 用 v2rayN）。保留旧 VPN 测通新节点后切换为「系统代理关闭 + TUN + 全局」，并在电脑网络阶段完成 1 次断线测试。
5. **AdsPower 独立环境**：使用 **AdsPower 免费版**直接手动新建环境，配置本机 HTTP 入口与真实硬件指纹，检查实际出口、IPv6／DNS／WebRTC 与三站评分（NetCoffee、Ping0、Scamalytics）。
6. **iPhone 小火箭、时区与订阅**：iPhone／iPad 统一使用 **Shadowrocket（小火箭）**「全局路由 → 代理」导入同一节点 → 统一电脑、手机和 AdsPower 时区（推荐跟随节点，也可选台北）并设置定位 → 完成手机出口、三站评分与 DNS／IPv6 验收 → 核对美区 Apple ID 与新号约两天等待 → 支付宝快捷买礼品卡充值 → 保持节点开启下载官方 Claude App、Google 登录并订阅 Pro → 确认订单与权益后回电脑使用。（安卓用户走[官网 Google Pay 分支](references/11-android-web-pay.md)。）

## 安装成 Skill（可选）

直接把项目文件夹交给 AI 即可使用。若希望在 Codex 中长期调用，可将整个 `claude-setup-guide` 目录放到 `~/.agents/skills/`，再用 `$claude-setup-guide` 启动。

## 自动检查更新

主流程 `workflow.py` 运行时会自动检查公开仓库 `version.json`（24 小时缓存），发现新版会在回答末尾提示，征得您同意后执行更新并保留 `.local/` 个人进度。也可手动运行：

```bash
python3 scripts/update.py check          # 常规检查（24 小时缓存）
python3 scripts/update.py check --force  # 立即联网重查
```

## 目录说明

- `SKILL.md`：AI 带做主入口。
- `references/`：各阶段图文教程与排查章节，控制层见[统一交付控制层](references/17-workflow-controller.md)。
- `assets/images/`、`assets/step-guides/`、`assets/reading/`：本地操作配图与 10 份客户阅读版 PDF。
- `scripts/`：`workflow.py` 控制层、`network.py` 部署与检测、`download_karing.py` 客户端校验下载、`cleanup.py` 平台清理、`update.py` 自动更新。
- `version.json`、`CHANGELOG.md`：版本与更新日志。
