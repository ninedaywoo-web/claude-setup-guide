# 本项目的 AI 入口

写代码、说明和执行任务都保持正向、高效。已授权的工作连续完成；故障出现就修复，日志和检测结果用于选择下一步及验收。将用户交接限定为缺失的访问方式、本人验证和工具无法代做的动作。

**统一流程入口：**完成项目启动与资料读取后，运行 `python3 scripts/workflow.py init`。每个阶段按 `next` 返回的任务操作，用当前票据提交实际结果，由控制层计算下一步。完整用法见 references/17-workflow-controller.md；具体教程负责当前动作的方法，阶段顺序以控制层为准。

正式教程源为公开仓库 `ninedaywoo-web/claude-setup-guide`，后续更新发布到这里。公开版客户读取和下载不需要邀请码或申请权限。另有组织私有交付版 `ninedaywoo-course/claude-setup-guide`，按用户指定同步教程正文，保留其独立版本与鉴权更新机制；领取服务另行维护。

用户发公开仓库链接开始或恢复带做时，先读 references/12-latest-start.md，实时下载并校验最新完整包；成功前不推荐 VPS、不复用本地旧 Skill 或更新缓存。由 AI 使用本机终端／下载工具完成，不默认要求客户点击 Code → Download ZIP；失败按启动流程检查原因和官方备用通道。成功后只从返回的新目录读取资料，显示版本并保留原进度，明确完整包已包含程序／流程和给人看的 PDF；后续询问只针对 PDF 是否另存到方便阅读的位置。用户仅给本地文件夹时读取 SKILL.md 的日常规则。开始前必须完整阅读 references/01-network.md 和 references/02-browser-iphone.md，其余章节按阶段读。完成启动后的第一个实质问题是设备是否登录过被 Claude 封禁的账号，早于 VPS 询问；已有答案复用，有封禁经历按 references/04-recovery.md 的开场分支安排适用清理，详情见 references/13-reader-guide.md。

Mac 默认使用 Karing。新交付固定使用 Karing `1.2.25.2802`、服务端 Xray `26.7.28`、REALITY `minClientVer=1.0.0`、目标 `www.cloudflare.com:443` 与两端 SNI `www.cloudflare.com`。Mac 安装包由 `scripts/download_karing.py` 下载并校验，服务器由 `scripts/network.py` 直接部署固定组合。项目更新与软件版本分开管理：交付软件跟随本项目固定版本表。用户反馈连接失败、REALITY 握手报错或切换后断连，就直接按 references/01-network.md 第十节执行修复：适用时先试 gvisor，随后校正参数并应用当前服务端版本／目标配置方案，每步实测，成功后继续交付。AI 自行读取环境、备份、修改和复测；用户只需配合工具无法代做的具体动作。

手机节点连接后，先按 references/02-browser-iphone.md 第 2.3 节主动展示并完成电脑／手机时区和定位设置，再做网络验收，将各阶段观察提交 scripts/workflow.py，由程序依次接到支付准备、App、登录与订阅。网络、时区、定位逐项记录，已完成结果复用；时区推荐跟随 VPS 出口，也可选台北；电脑、手机和 AdsPower 统一按所选方案设置。具体脚本输入见 references/06-before-login.md。环境设置完成后核对美区 Apple ID 与等待安排与客户选择记录，保持手机节点开启并下载官方 Claude App，Google 登录后直接订阅 Pro；订单和手机当前账号权益确认后，在对话展示收尾使用说明和个人经验，再记录 handoff_explained 后结束交付。

维护项目时，Markdown 是正文源文件，图片使用仓库内相对路径。禁止加入在线文档依赖、原帖链接、用户私人 IP 或凭据。更新用户提供的文字时保留其表达，不大幅改写。

发布修改时同步 version.json 与 CHANGELOG.md，运行 python3 scripts/manifest.py，再运行 python3 -m unittest discover -s tests。更新只改课程和脚本；.local/ 是使用者的数据，不提交、不覆盖。

确定性执行层见 references/14-scripted-execution.md；平台清理入口见 references/15-mac-cleanup.md 与 references/16-windows-cleanup.md。运行状态与凭据仅存 .local/。来源与许可保留 licenses/，客户界面只显示平台清理 Skill 名称。
