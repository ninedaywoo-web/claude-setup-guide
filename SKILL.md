---
name: claude-setup-guide
description: 根据完整本地图文教程，逐步带新手完成 VPS、Mac Karing／Windows v2rayN、AdsPower HTTP 代理、iPhone 小火箭网络、Claude 账号与 Apple 订阅；遇到退款、申诉、旧账号残留时按对应章节排查。用户交给你此项目、要求照教程从零配置或继续客户交付流程时使用。
---

# Claude 客户交付带做

收到本仓库链接或项目文件夹且用户未提出其他任务时，完成下面的上下文自检后立即下载校验最新完整包，读取资料并直接提出第一个问题（设备封禁经历）开始带做。用户明确提出其他任务时按其要求处理。

## 启动前上下文自检（第一优先）

收到仓库链接、交付指令或开始带做前，先核对当前对话之前是否存在无关任务历史：
- **全新空白对话**（当前指令是第一条实质消息，或仅恢复本项目带做）：静默通过，直接下载并启动。
- **旧对话已有无关上下文**：先暂停并回复客户：「检测到您是在聊过其他任务的旧对话里发的指令。旧上下文容易干扰配置顺序，请先**新建一个空白对话**，把刚才那段指令原样粘贴过去，我在新对话里从头带您配置。（如果您确认要在当前对话继续，请回复「继续当前对话」。）」客户回复「继续当前对话」后，直接从 `workflow.py` 起步。

## 收到仓库链接：下载并校验最新版

用户发来公开仓库链接开始或恢复带做时，先执行 [链接交付启动流程](references/12-latest-start.md)：实时核对远端 `main`、下载并校验最新完整包，再从返回的新目录重新读取本文件并按控制层 `reading` 阅读当前小节。向客户说明“已下载并校验项目完整包 vX.X.X，包含供 Codex 执行的程序／流程和给您阅读的 PDF 图文教程”，并附项目目录与 PDF 目录链接。恢复时从旧目录迁移 `.local/` 进度，旧目录原样保留。

## 本地启动与统一控制层

1. 以本文件所在目录为根目录，读取 `version.json` 与 `references/17-workflow-controller.md`，然后运行：
   ```bash
   python3 scripts/workflow.py init
   python3 scripts/workflow.py next
   ```
   （Windows 用已验证的 `py -3` 或 `python` 替代 `python3`。）
2. **流程边界：**每轮严格按 `workflow.py` 返回的当前阶段推进，每项进度均通过 `submit` 提交实际结果。按顺序完成电脑网络、AdsPower、手机小火箭、时区定位与手机网络验收，在 `workflow.py` 到达 `login` 阶段后，再在已配置的环境中登录或授权 Claude。
3. **版本更新检查：**`workflow.py` 每次运行会自动检查更新（24 小时缓存）；当 `update.status` 返回 `update_available` 时，先完成客户当前步骤回答，再在首个实质回答末尾单独一行展示 `update_notice`。客户同意后执行返回的 `update.apply_command` 并重读本文件。
4. **统一阶段顺序：**封禁经历（`intake`）→ 适用清理（`cleanup`）→ 设备搭配与 PDF 阅读版（`devices`）→ Google 账号（`google`）→ VPS（`vps`）→ 服务端（`server`）→ 电脑网络（`computer_network`）→ AdsPower（`browser`）→ 手机小火箭（`phone_proxy`）→ 电脑／手机时区与定位（`timezone`）→ 手机网络验收（`phone_network`）→ 支付准备（`payment_preparation`）→ 官方 App／安卓官网（`app`）→ 手机 Google 登录（`login`）→ 订阅与权益确认（`subscription`）。
5. **跨阶段提问与题外补充：**每轮读取控制层的 `task_scope_instruction` 和 `question_instruction`。优先按本教程对应章节和控制层说明直接用大白话正面回答；仅在外部软件菜单变化、实际页面报错或商家实时价格／库存核对时查看当前实际页面。客户提出疑问或犹豫（如“主要用电脑，手机一定要配吗”“时区对不上怎么办”）时，先按本教程原因简短正面说明，再接回当前阶段继续推进；完成字段逐项对应客户明确确认或工具结果。

## 每一轮怎么带

### 客户对话怎么说

- **先建议、再动作、给预期**：用简短大白话，直接沿用本项目推荐与既定顺序推进；遇到实际报错说明原因和下一步处理动作。三站分数达到参考值即继续下一步。
- **首次进阶段先展示说明与整组原图**：首次进入每个阶段，直接完整展示 `customer_message` 的用途解释与适用整组原图，配中文说明和当前起点；分支确定后立即补齐对应分支整套图。用户说不会、找不到或图没显示时，用 `guide --topic <主题ID>` 重发整组或 `--step <序号>` 定点重讲。
- **按阶段放提醒**：Apple 新号约两天等待、切换网络恢复方法、付款确认在对应步骤明确展示；已讲且情况未变的内容直接复用。

### 操作与关键配置（写死标准）

- **手动合并步进**：需要客户手动操作时，每轮合并给 2～3 个相连动作及应看到的结果。Mac 桌面控制首次启动异常时核对权限或重启一次，仍崩溃立即切手动合并步骤快速推进。
- **Google 账号准备**：先原样问「您有一个现在能正常登录的 Google／Gmail 账号吗？」。自有可用账号直接提交 `account_origin=self_used` 复用；明确缺号时提交 `google_account_status=unavailable`，同条回复给出首选 **[GmailBuy](https://gmailbuy.com/)「[【新号】全新美国谷歌账号(首登不弹二维码验证，推荐，不支持GV)](https://gmailbuy.com/home/goods.html?id=18&sid=18)」**、备选 **[出海91](https://chuhai91.cc/)** 与选购图，以现场页面实时价格与库存为准。选出海91时记录 `purchase_channel=chuhai91` 并给齐三步图（注册的是出海91网站账号）。收到商家账号资料后提交 `account_origin=purchased` 与 `google_account_status=available`，同条回复完整展示首登时机原因、2FA 科普、推荐取码入口 **[2FA 取码工具：https://2fa.run/](https://2fa.run/)**（手机本机身份验证器后面有条件再配）及三张原图，展示后提交 `materials_explained=true` 与 `materials_images_shown` 继续进入 VPS。
- **VPS 选型**：当前推荐按 `workflow.py policy` 的 `current_recommendation` 直接推进搬瓦工 USCA_9（2 GB、89.99 美元季付）及五张原图；恢复常规核对时按 DMIT 月付 → 搬瓦工季付顺序核对（`references/18-vps-stock.md`）。新购系统统一选 `Debian 12`，机房默认洛杉矶，`node_timezone` 取机房城市。
- **电脑网络（全流程仅测 1 次断线）**：新交付版本与 SNI 固定从 `workflow.py policy` 读取；Mac 用 `download_karing` 下载校验 Karing，Windows 用 v2rayN。保留旧 VPN 单独测通新节点后再切换为「系统代理关闭 + TUN 开启 + 全局代理」，并在 `computer_network` 阶段完成 1 次断线测试。Karing 握手报错按 `references/01-network.md` 第十节直接连续修复；Windows HTTP 通但开 TUN 回环按 `references/10-windows.md` 第 6.1 节排查。
- **AdsPower（写死免费版，不做断线测试）**：**免费版完全够用**，直接按免费版界面点左上角「新建环境」手动填写（无需付费 API）。点「确定」保存前一次配齐本机 HTTP 代理（并点检查代理）与全部指纹项（WebRTC 禁用、地理位置禁止、时区、噪音全关、WebGL 元数据／WebGPU／CPU／内存全部选真实）；打开后核对实际出口、IPv6／DNS／WebRTC 与三站评分即进入手机阶段。
- **手机、时区与 Apple 订阅（锁死小火箭，不做断线测试）**：iPhone／iPad 统一使用 **Shadowrocket（小火箭）**，全局路由选「代理」，配合全套图解推进；小火箭全局超时优先按 `references/02-browser-iphone.md` 2.2.1 试 `Chrome 140` TLS 指纹。连上后先按第 2.3 节统一电脑／手机／AdsPower 时区（推荐跟随节点，也可选台北）和定位设置，再做手机网络验收（实际出口、三站评分、IPv6／DNS、排除路由）。随后核对美区 Apple ID 与新号约两天等待，礼品卡首推支付宝（`guide --topic gift_alipay` 备忘录直达链接），保持节点开启下载官方 Claude App、Google 登录后直接订阅 Pro，确认订单与权益并展示收尾说明结束交付。

## 各阶段对应参考章节

| 阶段 | 读取章节 |
| --- | --- |
| 开场、设备搭配与阅读版 | `references/13-reader-guide.md`、`08-google-account.md` |
| 适用清理 | `references/04-recovery.md`、`15-mac-cleanup.md`、`16-windows-cleanup.md` |
| VPS、服务端与电脑网络 | `references/01-network.md`、`09-vps-purchase.md`、`14-scripted-execution.md`、`18-vps-stock.md`（Windows 加读 `10-windows.md`） |
| AdsPower、手机小火箭与时区定位 | `references/02-browser-iphone.md`、`06-before-login.md` |
| Apple 支付准备、App 与订阅 | `references/03-apple.md`、`07-apple-purchase-support.md` |
| 安卓官网分支 | `references/11-android-web-pay.md` |
| 售后（退款／申诉） | `references/04-recovery.md` |
