# Mac 端清理 Skill

开场确认这台 Mac 曾使用被封禁账号后，按实际使用的 Claude Code、Claude Desktop 或浏览器选择清理范围。对用户称“Mac 端清理 Skill”，链接本文件；脚本已内置。只用浏览器时，处理对应配置档的站点登录状态。

先运行只读审计：

```bash
python3 scripts/cleanup.py --audit
```

展示实际存在的缓存／日志、CLI 本地身份、钥匙串和 Desktop 登录态，沿用客户已确认的选择。实际清理在真实终端运行：

```bash
python3 scripts/vendor/mac_cleanup/claude_cleanup.py
```

客户在最终清单后输入一次 `CONFIRM`，由本人完成，AI 不管道代答。只在范围新增或变化时补问。CLI 身份、钥匙串、Desktop 数据／应用分别选择；精简模式与时区默认保持原值。网络配置阶段的时区按实际节点地区设置。

脚本先完整备份 `~/.claude` 与存在的 `~/.claude.json`，移除项存入时间戳废纸篓。Skills、Hooks、项目与会话按保护范围保留。用 Codex 或普通终端执行；正在运行的 Claude Code 只做只读审计。

当前脚本要求 `~/.claude` 存在才能执行完整备份。仅有 Desktop 的设备先记录审计结果，再按应用退出登录／重新安装流程处理。

完成后记录备份、废纸篓批次、所选范围与实际结果；中途失败按已完成项目续查或恢复。备份和含凭据的原始输出保存在本机。
