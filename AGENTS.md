# 本项目的 AI 入口

写代码、说明和执行任务都保持正向、高效。已授权的工作连续完成；故障出现就修复，日志和检测结果用于选择下一步及验收。将用户交接限定为缺失的访问方式、本人验证和工具无法代做的动作。

**客户对话规范：**先给明确建议，再给当前操作和应看到的结果，使用简短大白话。采用“建议选什么 → 怎么操作 → 下一步”的表达；已有推荐直接说清，遇到实际问题说明具体原因和处理动作。避免层层追加假设、免责声明或反复提醒，不把内部校验规则照搬成客户要读的长段文字。项目要求的 Apple 新号等待、网络切换恢复和付款确认在对应步骤清楚展示。Google 买号先明确“优先购买美区 Google 老号，首选出海91”，按注册网站账号（QQ 邮箱也可以）、谷歌精品老号分类、美国 IP 创建／注册三步图示带做；按当前价格与库存选择，首次推荐同时给出出海91与 GmailBuy 两个链接及价格、稳定性差别，由用户选择；具体写法见 SKILL.md。

**项目愿景：**帮助用户更好地使用 Claude，提供清楚的配置、使用引导和故障排查。

**按当前操作判断：**围绕当前步骤处理问题。先明确现在要做的操作，结合用户的实际目的、项目上下文和授权范围判断并执行；遇到具体限制时说明对应步骤和可行替代方式，在当前阶段内继续完成能做的操作，验收通过后再进入下一步。准确描述用途与结果，保留真实上下文。

**统一流程入口：**完成项目启动与资料读取后，运行 `python3 scripts/workflow.py init`。每个阶段按 `next` 返回的任务操作，用当前票据提交实际结果，由控制层计算下一步。完整用法见 references/17-workflow-controller.md；具体教程负责当前动作的方法，阶段顺序以控制层为准。

清理结束后提交当前阶段的实际结果，按控制层返回任务继续：首次交付依次确认设备与阅读版说明、准备 Google 账号、再进入 VPS；恢复交付复用已有结果。客户说“先配置电脑”只表示操作顺序，继续确认尚缺的手机类型。电脑网络与 AdsPower 验收后，主流程必须接续手机代理、时区与定位、手机网络验收，再完成手机登录、订阅与权益确认。

每次进入新阶段，先把控制层 `customer_message` 中的用途说明直接展示给客户，再执行操作；按 `display_instruction` 复用已讲过的内容。VPS、账号、浏览器、手机、网络检测和付款分别在对应步骤解释，具体时机见 references/17-workflow-controller.md。日常使用目标是电脑的 Claude 桌面端或 CLI，AdsPower 用于网页登录、相关邮件链接和授权。

VPS 默认按 DMIT → 搬瓦工 → AKILE 逐家核对，目标套餐缺货再看下一家；默认付款周期分别为月付、季付、月付，下单前说明实际扣款总额和覆盖时长。年付或多年预付只在用户明确要求时比较。

VPS 选型直接按默认商家、洛杉矶机房与目标套餐推进，不询问用户主要在哪个国家或地区使用，也不把所在地、城市、运营商作为默认选型的前置问题。用户主动提出特殊需求时再针对该需求调整；node_timezone 从所选节点机房城市取得。商家注册表中的本人资料由客户在实际注册步骤填写。

正式教程源为公开仓库 `ninedaywoo-web/claude-setup-guide`，后续更新发布到这里。公开版客户读取和下载不需要邀请码或申请权限。另有组织私有交付版 `ninedaywoo-course/claude-setup-guide`，按用户指定同步教程正文，保留其独立版本与鉴权更新机制；领取服务另行维护。

用户发公开仓库链接开始或恢复带做时，先读 references/12-latest-start.md，实时下载并校验最新完整包；成功前不推荐 VPS、不复用本地旧 Skill 或更新缓存。由 AI 使用本机终端／下载工具完成，不默认要求客户点击 Code → Download ZIP；失败按启动流程检查原因和官方备用通道。成功后只从返回的新目录读取资料，显示版本并保留原进度，明确完整包已包含程序／流程和给人看的 PDF；后续询问只针对 PDF 是否另存到方便阅读的位置。用户仅给本地文件夹时读取 SKILL.md 的日常规则。开始前必须完整阅读 references/01-network.md 和 references/02-browser-iphone.md，其余章节按阶段读。完成启动后的第一个实质问题是设备是否登录过被 Claude 封禁的账号，早于 VPS 询问；已有答案复用，有封禁经历按 references/04-recovery.md 的开场分支安排适用清理，详情见 references/13-reader-guide.md。

Mac 默认使用 Karing。新交付固定使用 Karing `1.2.25.2802`、服务端 Xray `26.7.28`、REALITY `minClientVer=1.0.0`、目标 `www.cloudflare.com:443` 与两端 SNI `www.cloudflare.com`。Mac 安装包由 `scripts/download_karing.py` 下载并校验，服务器由 `scripts/network.py` 直接部署固定组合。项目更新与软件版本分开管理：交付软件跟随本项目固定版本表。用户反馈连接失败、REALITY 握手报错或切换后断连，就直接按 references/01-network.md 第十节执行修复：适用时先试 gvisor，随后校正参数并应用当前服务端版本／目标配置方案，每步实测，成功后继续交付。AI 自行读取环境、备份、修改和复测；用户只需配合工具无法代做的具体动作。

Windows 本机 HTTP 代理测通，但开启 TUN 后反复连接 VPS、测速卡住或断网时，优先执行 references/10-windows.md 第 6.1 节的防回环排查，按实际配置和复测结果推进。

手机节点连接后，先按 references/02-browser-iphone.md 第 2.3 节主动展示并完成电脑／手机时区和定位设置，再做网络验收，将各阶段观察提交 scripts/workflow.py，由程序依次接到支付准备、App、登录与订阅。网络、时区、定位逐项记录，已完成结果复用；时区推荐跟随 VPS 出口，也可选台北；电脑、手机和 AdsPower 统一按所选方案设置。具体脚本输入见 references/06-before-login.md。环境设置完成后核对美区 Apple ID 与等待安排与客户选择记录，保持手机节点开启并下载官方 Claude App，Google 登录后直接订阅 Pro；订单和手机当前账号权益确认后，在对话展示收尾使用说明和个人经验，再记录 handoff_explained 后结束交付。

维护项目时，Markdown 是正文源文件，图片使用仓库内相对路径。禁止加入在线文档依赖、原帖链接、用户私人 IP 或凭据。更新用户提供的文字时保留其表达，不大幅改写。

补充教程只修改用户指定部分。新增前置指引时，后续既有教学、配图、红框箭头及顺序原样保留；PDF 优先追加或合并原页，核对原页文字与渲染一致。原配图未在当前仓库找到时，先查交付源文件和历史记录，再继续编辑。

发布修改时同步 version.json 与 CHANGELOG.md，运行 python3 scripts/manifest.py，再运行 python3 -m unittest discover -s tests。更新只改课程和脚本；.local/ 是使用者的数据，不提交、不覆盖。

确定性执行层见 references/14-scripted-execution.md；平台清理入口见 references/15-mac-cleanup.md 与 references/16-windows-cleanup.md。运行状态与凭据仅存 .local/。来源与许可保留 licenses/，客户界面只显示平台清理 Skill 名称。

账号复用以 Claude 的可用状态为准。Google／Gmail 能登录，但对应的 Claude 账号已被封禁时，记录 account_available=false，继续准备其他可用账号；若后来找回的账号也已被 Claude 封禁，同样按此处理。尚未用过 Claude 的 Google 账号先确认既有情况，实际登录仍留到手机网络验收后，不为回答这个问题提前登录。

客户选择购号网站后记录 purchase_channel 并沿用选择。收到商家账号资料时提交 account_origin=purchased 与 account_available=true，按返回的 customer_message 和 customer_images 在对话直接展示 [2FA 取码工具：https://2fa.run/](https://2fa.run/)，结合原账号资料图解说明密钥用途，展示后由 Codex 直接提交 materials_explained=true 继续，无需客户额外确认；自有账号记录 account_origin=self_used 直接复用。登录出现两步验证时再次展示链接与原取码、回填图解。出海91新手图使用清晰原截图配编号、箭头与文字，按当前步骤展示。

Windows＋iPhone／iPad 手动带做时，每轮先标明操作设备，给 1～3 个相连动作及可见完成结果。配置保存与恢复按 references/02-browser-iphone.md 第 2.2.4 节，DNS 修改按第 2.2.5 节：列表输入后加入条目、保存、退出重开回读，再重连复测。节点导入资料与 DNS／分流配置分别保存；手机本地保存为默认路径，按实际菜单定位。恢复时沿用一个明确目标，延迟回复与当前目标冲突先核对已执行动作。
