# 本项目的 AI 入口

正式教程源为公开仓库 `ninedaywoo-web/claude-setup-guide`，后续更新发布到这里。公开版客户读取和下载不需要邀请码或申请权限。另有组织私有交付版 `ninedaywoo-course/claude-setup-guide`，按用户指定同步教程正文，保留其独立版本与鉴权更新机制；领取服务另行维护。

用户发公开仓库链接开始或恢复带做时，先读 references/12-latest-start.md，实时下载并校验最新完整包；成功前不推荐 VPS、不复用本地旧 Skill 或更新缓存。由 AI 使用本机终端／下载工具完成，不默认要求客户点击 Code → Download ZIP；失败按启动流程检查原因和官方备用通道。成功后只从返回的新目录读取资料，显示版本并保留原进度，明确完整包已包含程序／流程和给人看的 PDF；后续询问只针对 PDF 是否另存到方便阅读的位置。用户仅给本地文件夹时读取 SKILL.md 的日常规则。开始前必须完整阅读 references/01-network.md 和 references/02-browser-iphone.md，其余章节按阶段读。完成启动后的第一个实质问题是设备是否登录过被 Claude 封禁的账号，早于 VPS 询问；已有答案复用，有封禁经历按 references/04-recovery.md 的开场分支安排适用清理，详情见 references/13-reader-guide.md。

Mac 默认使用 Karing；连接故障无论是否已确认兼容性，都先按 references/01-network.md 第十节保留 Karing 排查与修复，必要时按历史案例回退。其他 Xray 客户端测通仅作对照，不自动首推换客户端。

维护项目时，Markdown 是正文源文件，图片使用仓库内相对路径。禁止加入在线文档依赖、原帖链接、用户私人 IP 或凭据。更新用户提供的文字时保留其表达，不大幅改写。

发布修改时同步 version.json 与 CHANGELOG.md，运行 python3 scripts/manifest.py，再运行 python3 -m unittest discover -s tests。更新只改课程和脚本；.local/ 是使用者的数据，不提交、不覆盖。
