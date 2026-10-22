# Windows 端清理 Skill

开场确认 Windows 用过被封禁账号后，按实际使用的 Claude Code、Claude Desktop 或浏览器选择清理范围。对用户称“Windows 端清理 Skill”，链接本文件；已内置独立 Python 脚本。

当前文件处理已通过隔离样本测试，真实 Windows 的进程查询、NTFS 权限与安装路径待实机验证。先运行只读审计，按当前机器的结果继续。

## 审计与清理

使用可用的 Python 3.9+ 入口，例如：

```powershell
py -3 scripts/cleanup.py --audit --scope cache account credentials desktop
```

输出现存目标和会移除的 JSON 键名，凭据值留在本机。遇到权限或链接路径问题，先处理具体报错。

| 范围 | 做什么 | 保留什么 |
| --- | --- | --- |
| `cache` | 固定白名单内的缓存、日志、崩溃记录 | 登录配置、Skills、项目、会话 |
| `account` | `.claude.json` 中列出的账号缓存与本地 ID，及 `.claude/.user-id`、`.machine-id` | 项目映射、MCP 与未列出的配置键 |
| `credentials` | `.claude/.credentials.json` 中 `claudeAiOauth`、`trustedDeviceToken` | MCP、插件秘密及其他键 |
| `desktop` | 实际 AppData 中 Claude／Claude-3p 及已知商店版的登录／会话存储 | `claude_desktop_config.json`、安装程序及其他应用资料 |

处理登录存储后需要重新登录。只用 AdsPower／普通浏览器时，处理对应浏览器配置档的站点状态。Windows Credential Manager、系统硬件标识与浏览器指纹配置不在本脚本范围内。

沿用客户已确认的范围，在真实终端执行，例如清理缓存与 CLI 账号状态：

```powershell
py -3 scripts/cleanup.py --apply --scope cache account
```

客户在实际清单后输入一次 `CONFIRM`，由本人完成，AI 不管道代答。脚本检查 Claude 已退出、目标未改变，再备份并校验所有选中项目，随后执行清理。备份与移除项保存在 `%USERPROFILE%\ClaudeBackups\windows-cleanup\<批次>`，目录权限限定当前用户。原配置备份继续保留。

检查失败时按具体报错处理；部分完成的操作保存在批次 `manifest.json`，供续查或恢复。并发调用由执行锁阻止。

## 恢复

```powershell
py -3 scripts/cleanup.py --restore "实际备份批次的完整路径"
```

在终端确认本次恢复范围，退出 Claude 后执行。脚本校验备份；目标已经生成新数据时暂停该次恢复，保留双方数据供核对。

在 `.local/progress.md` 记录所选范围、批次路径、实际结果与待补项。对用户说明实际处理了哪些缓存、登录状态或本地标识。
