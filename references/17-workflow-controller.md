# 统一交付控制层

适用：从零交付、接续本项目、恢复旧客户进度。阶段顺序和完成判定由 `scripts/workflow.py` 统一管理。各教程章节只提供当前步骤的操作方法；AI 依据控制层返回的当前阶段执行。

## 开始与连续执行

先按 SKILL 完成项目启动和资料读取，然后运行：

```bash
python3 scripts/workflow.py init
python3 scripts/workflow.py next
```

`init` 可重复调用，保留已有状态。Windows 使用已验证的 `py -3` 或 `python` 替换 `python3`。第一次返回 `intake`：先问设备是否登录过被 Claude 封禁的账号。已有明确答案直接提交，AI 连续完成可代做动作。

`next` 返回当前阶段、操作章节、所需观察字段、缺项、已记录结果、允许的脚本动作和本阶段 `ticket`。AI 按当前动作操作，每取得一组结果提交一次；程序合并部分结果并计算下一步。客户只接手本人验证、付款与工具无法代做的具体动作。`devices` 返回 `customer_message` 时，确认电脑和手机类型后将这段设备说明展示在客户对话里，再记录 `setup_explained=true`；接着按阅读版三段话术介绍 PDF，随后进入 Google 账号和 VPS。

## 在客户需要的时候解释用途

控制层把下列说明放入对应阶段的 `customer_message`，AI 首次进入该阶段时直接讲给客户，再执行当前动作。同一阶段连续操作复用已讲过的说明，客户追问时再展开；恢复带做时结合对话记录补上尚未讲过的部分。

| 进入阶段 | 当场解释 |
| --- | --- |
| google | Google 用于登录，Apple 用于 iOS 下载、充值与付款；已有账号复用，购买默认看美区及账号使用时间，商家规格随页面核对。安卓只解释适用的 Google 登录用途。 |
| vps | VPS 是租来的远程服务器，用来搭建自己的节点；客户购买，Codex 部署。家宽问题按网络篇解释搭配与最终出口。 |
| computer_network | 客户端连接节点，TUN 接管流量，全局走选定节点；保留旧 VPN 测通后再切换。 |
| browser | 指纹浏览器隔开登录记录与日常浏览器设置，用于网页登录、邮件链接与授权；日常使用电脑桌面端或 CLI。顺带解释三站检查用途。 |
| phone_proxy | iOS 手机负责首次登录与内购，Apple 处理订单及退款申请；安卓使用自己的官网付款路线。 |
| phone_network | 手机独立检查三站与实际出口，和电脑的目标线路核对后再登录订阅。 |
| payment_preparation | 说明礼品卡充值 → App Store 余额 → Claude Pro 内购；已有余额复用。先落实账号等待安排，等待或申诉期间展示当前安排，到期后继续充值步骤。 |
| subscription | 订单及权益确认后，说明回电脑桌面端或 CLI 使用同一账号，网页登录授权仍走 AdsPower。 |

## 手机验收对话与结果

`phone_network` 直接输出手机操作、实际出口对照要求和三站链接。Windows＋iPhone 用户先反馈手机 Ping0 页面和 Wi-Fi／蜂窝网络类型，再逐站提供 NetCoffee、Scamalytics 结果；Codex 按页面或用户明确反馈记录实际来源。电脑与手机的 `scores` 均须包含三站实际数值和结果说明，缺失／空值保留在当前阶段。出口不一致也须先解决。已有真实分数偏离参考值时，继续使用原有复查流程。

## Apple 账号来源与付款提醒

进入 Apple 支付准备时直接展示账户来源提问；没有小火箭、需要购买时提前在手机代理阶段展示。`account_origin` 记录 `self_used`／`newly_registered`／`purchased`；后两者自动归为 `account_type=new`，卖家“老号”仍按新接手提醒。新号先展示加粗的两天等待建议、购买限制和人工支持说明，再记录 `apple_reminder_shown=true`；来源和首次登录时间保存在同一账号的进度中，后续复用。

支付准备与正式订阅前直接输出简短复查，不重复计时。同一阶段连续操作不重复播报同一提醒。新号等待和用户明确选择立即继续的规则保持不变；已购买受限进入人工支持流程。

## 更新检查与提醒

主流程每次向 AI 返回结果时自动执行更新检查，24 小时内复用缓存，到期后重新联网。`init`、`next`、`status`、`submit`、`change` 的结果含 `update`；`run` 在返回的 `workflow` 内包含相同信息。内部保存与计算不联网。

发现新版时，更新建议直接追加到 `customer_message`。先处理客户当前步骤，再在本次带做的首个实质回答末尾展示建议；同一段连续带做不重复提醒同一版本，恢复时再次提醒。用户同意后执行返回的 `update.apply_command`，更新保留 `.local` 进度，再重读 Skill 和变更章节。检查失败照常继续当前步骤并简短说明；立即重查使用 `python3 scripts/update.py check --force`。

## 唯一阶段顺序

| 阶段 ID | 当前任务与完成内容 |
| --- | --- |
| intake | 设备封禁经历；已有答案复用。 |
| cleanup | 有封禁经历才进入，记录适用范围及清理结果／客户暂缓选择。 |
| devices | Mac／Windows 与 iPhone／iPad／Android，完成设备搭配说明。 |
| google | 展示账号准备说明：已有可用 Google 账号就复用，没有则直接提供购买渠道；账号备妥后继续，实际登录留到手机网络验收后。 |
| vps | 读取或准备 VPS、SSH 访问、节点标签及节点所在城市时区；已有 VPS 直接复用。 |
| server | 部署或检查已有节点，读回服务状态与客户端参数。 |
| computer_network | 系统代理关闭、TUN＋全局、HTTP 入口、新出口及 HTTPS、旧 VPN 交接、Codex 新回复和断线检查。 |
| browser | AdsPower 环境已保存并打开，代理和指纹设置完成，在该环境实际检测出口、DNS／IPv6／WebRTC、断线行为及三站结果。 |
| phone_proxy | 手机导入同一节点，开启全局代理与 VPN。 |
| timezone | 手机代理完成后展示当前平台的时区与定位路径：Mac 关闭系统服务“设定时区”，保留定位总开关原状，禁止 Claude 网页位置权限；Windows 和手机按对应步骤关闭定位。各端时区与 AdsPower 一致；逐项记录完成后进入手机网络验收。 |
| phone_network | 在手机独立检测出口、HTTPS、DNS／IPv6、排除路由、实际网络类型、断线行为与三站结果。 |
| payment_preparation | Apple 路线核对美区 Apple ID、商店登录、养号起点与支付准备；Android 记录官网支付条件与路线说明。 |
| app | 保持手机节点开启，下载 Anthropic 官方 Claude App 并检查请求路径；Android 打开官网。 |
| login | 使用 Google 账号登录 Claude 成功，记录本机账号代号。 |
| subscription | 手机订单和同一账号 Pro 权益确认，结束交付。 |

Mac／iPhone 和 Windows／iPad 的具体字段由程序按设备选择生成；Android 采用官网支付字段。Mac 仅关闭时区定位、核对网页位置权限；手机定位和系统服务时区的操作沿用浏览器与 iPhone 章节，Windows 采用对应系统设置。`node_label`、`profile_ref`、`account_ref`、`apple_account_ref` 使用本机代号，不存 IP、节点链接、邮箱或凭据。

## 提交观察

AI 把当前结果写入 `.local/workflow/observation.json`。以开场用户明确回答“没有”为例，`ticket` 取当前 `next` 的实际值：

```json
{
  "stage": "intake",
  "ticket": "当前返回的票据",
  "source": {"kind": "user", "reference": "本轮用户明确回答没有封禁账号登录经历"},
  "data": {"banned_login": "no"}
}
```

```bash
python3 scripts/workflow.py submit --input .local/workflow/observation.json
```

每个阶段的 `required_fields` 和 `submission` 提供字段说明与空模板。只填写已经取得的观察；可分次提交，已取得的字段会合并。尚未取得的内容留到后续操作，程序返回具体缺项。直接填一个 `passed`／`complete` 标记不会推进流程。新阶段只能使用新票据；重复提交同一份结果不会重复推进。

`source.kind` 可为 `tool`（页面／命令结果）、`user`（具体动作反馈）、`legacy`（本次客户的已有详细记录）；`reference` 写对应页面、回执或反馈位置。来源用于追溯，AI 应读取实际结果后提交。UI 事实仍由页面工具或用户反馈提供，控制层检查字段、关联对象和阶段依赖。

浏览器检测的 `checked_profile_ref` 必须对应当前保存的 `profile_ref`；阶段内更换 `profile_ref` 后，程序清空原环境的完成字段，重新收集新环境的结果。手机节点对应 VPS 的 `node_label`。时区采用 IANA 标识，台北为 `Asia/Taipei`，洛杉矶为 `America/Los_Angeles`；Windows 时区名称按规则换算。三站 `scores` 分别记录 `value` 与 `result`；网站暂不可读时保留空值和实际原因，不编造分数；评分建议仍按原三站规则处理。

## 调用现有脚本

先读取 `allowed_actions`，在当前阶段通过统一入口运行：

```bash
python3 scripts/workflow.py run --action server_preflight
python3 scripts/workflow.py run --action server_deploy
# 已有脚本管理的节点使用 server_export，已有其他面板按当前页面检查后提交观察。
python3 scripts/workflow.py run --action download_karing
python3 scripts/workflow.py run --action probe_proxy
python3 scripts/workflow.py run --action probe_system
python3 scripts/workflow.py run --action browser_scores --input .local/network/observations.json
```

以上是各阶段动作示例，实际每次执行当前 `allowed_actions` 中的一项。先准备原网络脚本需要的 `.local/network/input.json`，字段见确定性执行层。浏览器评分仅接受 AdsPower 观察，手机评分按实际 iPhone／Android 分支接收。

服务端部署／导出会读回验证，成功回执自动完成服务端阶段。使用了网络脚本的 `probe` 配置时，电脑网络阶段会同时核对当前网络代次和阶段检查批次的两种探针成功回执；更换电脑或重置检查会更新批次，旧回执仅保留为历史。手填通过字段不能覆盖失败回执。代理探针只填它实际测得的项目，TUN、旧 VPN 交接和 Codex 回复仍在设备上观察。下载 Karing 仅完成下载，后续安装和设置继续当前阶段。失败保留当前阶段与错误，按对应修复章节连续排查。

清理阶段可用 `cleanup_audit`／`cleanup_apply`；审计不会完成清理阶段。执行清理时仍由客户在终端完成现有脚本的范围选择和最终确认，控制层不代填确认。Windows 可通过 `--input` 提供 `{ "scope": ["cache", "account", "credentials", "desktop"] }` 中实际选定的范围，Mac 在原交互清单中选择。Windows 恢复使用 `cleanup_restore`，输入文件提供 `backup_directory`，按现有恢复校验和本人确认执行。实际结束后提交所选范围与结果。`cleanup_apply` 在 Mac 调用原交互流程，在 Windows 使用现有 `--apply` 流程。

统一状态存在时，网络部署／检测、Karing 下载、平台清理入口会验证控制层本次执行许可。直接调用这些入口会提示先运行 `workflow.py next`。`network.py status`、`invalidate` 保留诊断用途；失效状态会被控制层同步识别。旧 `login_readiness.py` 在统一流程启用后返回当前流程结果。

## 等待、恢复与变更

新 Apple ID 填写带时区的实际 `first_used_at`，例如 `2026-10-23T09:00:00-07:00`。默认按正常使用约两天（48 小时）计算 `resume_at`。`waiting` 时保存原起点，到期再次运行 `next` 后继续补齐当前缺项；付款准备已齐才进入 App 阶段；长期自用老号按账户实际状态继续。

Apple 准备阶段记录实际商店账号的本机代号 `apple_account_ref`，例如 `apple-main`。更换手机后重新核对商店登录、地区及支付状态；确认仍是同一账号并提交相同代号后，程序从 `account_history` 复用账号类型和首次使用时间。另一账号使用另一代号，按它自己的实际记录计算等待。阶段内切换账号会清除上一账号的设备检查字段；将新号纠正为老号时，程序自动移除当前记录中不再适用的等待字段。

所有正常继续和中断恢复都先运行 `next`。脚本调用失败／中断保持当前阶段，已提交的观察与执行回执保留。账号、养号时间和付款记录独立保存；重新检查网络时继续复用。

```bash
python3 scripts/workflow.py change --scope node --reason '本次改用新的 VPS 节点'
python3 scripts/workflow.py change --scope timezone --reason '用户选择台北'
```

变更范围包括 `intake`、`cleanup`、`devices`、`node`、`network`、`handoff`、`computer`、`browser`、`phone`、`timezone`、`google`、`apple`。更换平台搭配（如 iPhone 改 Android）使用 `devices` 重选平台；同平台更换硬件使用 `computer` 或 `phone`。程序只失效相应设置和检测；重新领取任务后按当前设备操作。网络输入内容或网络脚本检测代次变化在下次调用时自动识别。只有本机探针地址／端口或检测代次变化时复查客户端接管；服务端配置变化才复查服务器。更换手机或 Google 账号时重新核对登录与权益，并保留“已有付款记录”的提示，先处理已有订单归属与权益。

旧 `.local/progress.md` 保留，新的派生进度在 `.local/workflow/progress.md`。恢复旧客户时，AI 读取当前阶段所需的旧记录，能对应到具体实际结果的以 `legacy` 来源提交；只补缺失项目，不重新询问已有答案。笼统的“全部完成”不能自动变成各项观察。旧的 `login-readiness.json` 作为历史观察来源，不再独立决定下一步。

## 执行范围

统一控制层管理本项目阶段、状态和已接入脚本入口。浏览器与手机原生工具由 Codex 宿主提供，AI 将其操作限定在当前返回的阶段，并提交实际结果。该本地项目无法拦截独立宿主里的任意原生工具调用；宿主需要强制约束这些工具时，应在工具调用入口接入相同的阶段许可。


## 客户提示与分支（本轮更新）

- `devices`：设备说明后展示 PDF 用途，分别记录 `setup_explained`、`pdf_explained`。PDF 另存选择可为 yes／no／unanswered，不要求客户答复才能继续。安卓额外记录 `android_route_explained` 与 `payment_route_status`（available／needs_setup／unknown），开场先说明付款条件。
- `browser`：展示电脑使用浏览器提醒后记录 `usage_explained`；`login` 再提醒一次并记录 `browser_notice_shown`。
- `phone_proxy`：iOS 记录 `client_available`。已有小火箭直接复用；未购买时可先提交 false，再准备 Apple ID。在本阶段也可提交 `apple_account_ref`、`account_type`、`store_signed_in`、`first_used_at`、`apple_reminder_shown`，正式支付阶段复用同一账户的起点。
- 新号登录完成就返回建议时间；`wait_choice=wait` 或未选择时默认等待。客户明确选择立即继续，用 `source.kind=user` 记录 `wait_choice=continue`，再继续核对其他条件。首次时间须包含时区，不从买号时间算起。
- 在小火箭准备、Apple 付款准备或实际订阅阶段提交 `purchase_restricted=true`，直接返回人工支持章节。用 `support_case` 记录客服安排，有具体时间时记录 `support_retry_at`；处理完成后再提交实际的购买限制状态。
- 三站明显偏离时返回 `score_advice`，先复查。提交 `score_review=rechecked` 和实际复查说明，或在客户明确选择继续时用用户来源提交 `score_review=continue` 与说明。轻微偏离保留可继续；换检测结果后重新记录复查处理。
- 订阅订单与权益确认后直接展示收尾说明和使用经验，提交 `handoff_explained=true`。不增加 Claude Code 教学、重启验收或后续手机重装跟踪。
- `customer_message` 是需要原样或自然转述到客户对话的内容；工具输出本身不算已展示。已展示且对象未变的说明沿用记录。
