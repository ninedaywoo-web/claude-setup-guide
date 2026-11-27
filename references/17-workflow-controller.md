# 统一交付控制层

适用：从零交付、接续本项目、恢复旧客户进度。阶段顺序与完成判定统一由 `scripts/workflow.py` 管理，各教程章节提供当前步骤的操作方法。

## 开始与连续执行

完成启动读取后运行：

```bash
python3 scripts/workflow.py init
python3 scripts/workflow.py next
```

`init` 可重复调用并保留已有状态（Windows 用已验证的 `py -3` 或 `python` 替换 `python3`）。`next` 返回当前阶段、阅读小节、所需观察字段、缺项、允许的脚本动作和本阶段 `ticket`。每取得一组实际结果即提交 `submit`，由程序合并观察并计算下一步；用户只接手本人验证、付款与工具无法代做的动作。

**跨阶段提问与题外补充：**每轮读取控制层的 `task_scope_instruction` 和 `question_instruction`。优先按本教程对应小节和控制层说明直接用大白话正面回答；仅在外部软件菜单变化、实际页面报错或商家实时价格／库存核对时查看当前实际页面。客户提出疑问或犹豫（如“主要用电脑，手机一定要配吗”“时区对不上怎么办”）时，先按本教程原因简短正面说明，再接回当前阶段继续推进；完成字段逐项对应客户明确确认或工具结果。

## 进入新阶段时先解释用途

控制层将每阶段的用途说明放入 `customer_message`，首次进入该阶段时直接完整展示给客户，再带做当前操作；同阶段连续操作复用已讲说明。

| 阶段 ID | 首次进入说明与完成内容 |
| --- | --- |
| `intake` | 询问电脑或手机是否登录过被 Claude 封禁的账号；已有答案直接复用。 |
| `cleanup` | 有封禁经历时进入，按设备执行适用清理并记录 `outcome` 与 `handled_scope`（桌面端清理须关联 `cleanup_audit`／`cleanup_apply` 回执；仅浏览器或手机可提交 `cleanup_mode=browser_only`／`phone_only`）。 |
| `devices` | 确认电脑与手机类型，展示设备搭配说明（`setup_explained=true`）与 PDF 阅读版说明（`pdf_explained=true`，另存选择可记 `yes`/`no`/`unanswered`）；安卓另记录路线说明与支付条件。 |
| `google` | 原样问是否有可用 Google／Gmail 账号；自有账号 `account_origin=self_used` 复用；缺号提交 `google_account_status=unavailable`，同条展示首选 GmailBuy 新号（`id=18&sid=18`）与备选出海91及选购图；收到资料后提交 `account_origin=purchased` 与 `available`，展示首登时机、2FA 科普、`https://2fa.run/` 与三张原图后提交 `materials_explained=true` 与 `materials_images_shown`。 |
| `vps` | 解释 VPS 是租来的远程服务器，系统默认 Debian 12、洛杉矶机房。当前按 `workflow.py policy` 的推荐直接推进搬瓦工及五张原图；恢复常规核对时按 `references/18-vps-stock.md` 采集并核对。开通且 SSH 就绪后提交 `access_ready=true`。 |
| `server` | 运行 `server_preflight`、`server_deploy`（或已有本脚本节点用 `server_export`），读回服务状态、Xray 版本与导出节点。 |
| `computer_network` | 保留旧 VPN 测通新节点（`probe_proxy`）后切换为系统代理关闭 + TUN + 全局并复验（`probe_system`）、确认 Codex 新回复，并在本阶段完成全流程唯一的 1 次断线测试。 |
| `browser` | 区分 Claude 桌面版、Claude Code 与 AdsPower。使用 **AdsPower 免费版**直接点「新建环境」手动填写，点确定前一次配齐本机 HTTP 代理和真实硬件指纹（WebRTC 禁用、定位禁止、时区、噪音全关、WebGL 元数据／WebGPU／CPU／内存均选真实），验收出口、DNS／IPv6／WebRTC 与三站评分（不做断线测试）。 |
| `phone_proxy` | 主动讲清“手机只用于首次登录和 Apple 礼品卡内购、日常回电脑用、下一步立刻统一三端时区”；iPhone／iPad 统一使用 **Shadowrocket（小火箭）**，导入同一节点、全局路由选「代理」并开启 VPN（安卓用官网分支）。 |
| `timezone` | 询问一次“跟随节点（推荐）／台北”，展示对应设备路径完成设置：Mac 关闭自动时区与系统服务“设定时区”（定位总开关保原状，禁止网页位置权限）；Windows 与手机关闭自动时区和定位总开关；核对电脑、手机与 AdsPower 时区一致。 |
| `phone_network` | 在手机独立验收实际出口、三站评分（NetCoffee／Ping0／Scamalytics）、DNS／IPv6、排除路由与所用 Wi-Fi／蜂窝网络（不做断线测试）。 |
| `payment_preparation` | Apple 路线核对美区 Apple ID 来源（`self_used`／`newly_registered`／`purchased`，后两者归为新号并展示约两天等待提醒与首次登录起点）；充值礼品卡首推支付宝（`guide --topic gift_alipay` 备忘录直达链接）。安卓记录官网支付条件与风险确认。 |
| `app` | 保持手机节点开启，下载 Anthropic 官方 Claude App 并核对请求路径（安卓打开官网）。 |
| `login` | 在手机官方 Claude App 用 Google 账号登录成功（需两步验证时再次给出 `https://2fa.run/` 与原取码回填图），记录本机账号代号。 |
| `subscription` | 确认手机 Pro 订单与当前账号权益后，展示收尾使用说明与经验，提交 `handoff_explained=true` 完成交付。 |

`node_label`、`profile_ref`、`account_ref`、`apple_account_ref` 均填本机代号，账号密码、完整 IP、密钥和节点链接仅保存在 `.local/`。

## 提交观察与调用脚本

可直接用标准输入提交观察（Windows PowerShell 可用 `@' ... '@` 管道输入）：

```bash
python3 scripts/workflow.py submit --input - <<'JSON'
{"stage":"当前阶段","ticket":"next 返回的票据","source":{"kind":"user","reference":"客户本轮具体反馈"},"data":{"观察字段":"实际值"}}
JSON
```

- 只填已取得的观察，支持分次合并提交；`source.kind` 可为 `tool`、`user`、`legacy`。
- 浏览器 `checked_profile_ref` 与 `profile_ref` 对应，手机 `node_label` 与 VPS 对应，时区用 IANA 标识（如 `America/Los_Angeles`、`Asia/Taipei`），三站 `scores` 含 `netcoffee`、`ping0`、`scamalytics` 实测值与说明；大幅偏离时复查并记录 `score_review`。
- 脚本动作统一经当前 `allowed_actions` 调用：
  ```bash
  python3 scripts/workflow.py run --action server_preflight
  python3 scripts/workflow.py run --action server_deploy
  python3 scripts/workflow.py run --action download_karing
  python3 scripts/workflow.py run --action probe_proxy
  python3 scripts/workflow.py run --action probe_system
  python3 scripts/workflow.py run --action browser_scores --input .local/network/scores-input.json
  ```
- 完整诊断用 `next --full`，固定版本与套餐推荐用 `policy`，变更范围用 `workflow.py change --scope <范围> --reason '<原因>'`（支持 `intake`/`cleanup`/`devices`/`node`/`network`/`handoff`/`computer`/`browser`/`phone`/`timezone`/`google`/`apple`）。

## 等待、受限与恢复

- **Apple 新号等待**：填写带时区的手机 App Store 首次登录时间 `first_used_at`，程序自动按 48 小时计算 `resume_at`；到期运行 `next` 继续，客户明确选择现在继续时以 `source.kind=user` 提交 `wait_choice=continue`。
- **购买受限**：在 `phone_proxy`、`payment_preparation` 或 `subscription` 提交 `purchase_restricted=true` 即切入 `references/07-apple-purchase-support.md` 人工支持流程，记录 `support_case` 与 `support_retry_at`。
- **更新检查**：`workflow.py` 自动附带 `update`（24 小时缓存）；新版提示在首个实质回答末尾展示，客户同意后执行 `update.apply_command` 保留 `.local/` 进度。

## 默认出图与重复求助

首次进入阶段，将 `customer_message` 中本阶段适用的全部原图按顺序展示齐全，配中文说明和当前起点；商家、账号来源或支付渠道确定后，立即补齐该分支整套图（搬瓦工 5 张、AdsPower 3 张、出海91 3 张、Google 资料 3 张等）。

`guide --topic <主题ID>` 返回该主题整组原图，`--step <序号>` 用于后续定位重讲；`guide` 只读、不改变当前阶段。客户说不会、找不到或图未显示时立即重发对应图及打开链接。

| 客户常见求助 | 对应 `guide` 主题 |
| --- | --- |
| 刚买好谷歌号、一串资料看不懂 | `google_materials`（字段、取码、回填三张原图） |
| 2FA 密钥／动态验证码怎么取 | `google_2fa`（附 `https://2fa.run/`；短信／备用码用 `google_other_verification`） |
| 出海91 注册、分类、挑号 / GmailBuy | `chuhai_register` / `chuhai_category` / `chuhai_product` / `gmailbuy` |
| VPS 注册与选套餐页面 | `vps_bandwagon` / `vps_dmit` |
| AdsPower 哪个框填什么 | `browser_profile` / `browser_proxy` / `browser_fingerprint` |
| 小火箭扫码、备份、DNS、分流配置 | `phone_node` / `phone_backup` / `phone_dns` / `phone_config` |
| Apple 登录、支付宝／官网礼品卡、兑换 | `apple_store` / `gift_alipay` / `gift_official` / `gift_redeem` |
| 下载 Claude App、升级 Pro、申诉支持 | `claude_app` / `claude_subscribe` / `apple_support` |

## 维护测试命令

- 离线单测：`python3 -m unittest discover -s tests`
- 真实模型演练：`python3 tests/model_replay.py --output .local/model-replay`
- 连续场景验收：`python3 tests/model_replay.py --journey gift --journey vps --journey google --journey server --journey network --model <模型> --output .local/journey-validation`
