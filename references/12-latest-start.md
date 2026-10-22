# 收到公开仓库链接后，下载最新版再开始

适用：用户把 `https://github.com/ninedaywoo-web/claude-setup-guide` 发给 AI，要求开始或恢复带做，包括只有链接而无其他任务的情况。审查、解释仓库等请求不触发安装。本流程优先于日常 24 小时更新检查。

## 谁来下载、下载的是什么

由 AI 使用本机终端或文件下载工具自动完成。GitHub 连接器只能读网页、不能保存 ZIP，不代表公开仓库不能下载；应继续使用可用的本机工具。默认不要求客户登录 GitHub、申请权限或点击 Code → Download ZIP，不把公开仓库误当成私有交付版。

下载的是**项目完整包：程序／AI 带做流程＋操作配图＋给人看的 PDF 教程**。PDF 已包含在包内；后面询问客户的只是要不要把 PDF 另外复制到方便阅读的位置。下载前可简短告知将获取这些内容，成功后再提供实际位置。

## 执行顺序

1. 使用 GitHub API 实时读取 `https://api.github.com/repos/ninedaywoo-web/claude-setup-guide/git/ref/heads/main`，取得 `object.sha`，确认是 40 位十六进制提交号。不能使用搜索摘要、旧对话中的提交或已安装 Skill 的版本号代替。API 被限流或不可达时，可用本机 `git -c credential.helper= ls-remote https://github.com/ninedaywoo-web/claude-setup-guide.git refs/heads/main` 获取同一分支提交；关闭交互式登录，不索要 token。
2. 从 `https://raw.githubusercontent.com/ninedaywoo-web/claude-setup-guide/<本次提交号>/scripts/update.py` 下载脚本到本机临时目录，读取检查后运行。不要使用旧目录里的脚本，不用 `curl | sh` 等边下载边执行方式。脚本只访问本公开仓库，不需 GitHub 登录、不索要 token。raw 地址不可达时，可用同一提交的 GitHub Contents API 获取脚本并解码保存，或用本机 Git 获取该提交后读取脚本；不能据此直接把下载任务推给客户。
3. 确认可用的 Python 3.9+。Mac 常用 `python3`，Windows 常用 `py -3` 或 `python`。指定一个尚不存在的新目录，例如用户工作目录下带时间后缀的 `claude-setup-guide-...`，执行：

   ```text
   python3 <刚保存并检查的脚本绝对路径> start --destination <新目录绝对路径>
   ```

   恢复已有客户时，确认原来实际使用的教程目录，再追加 `--progress-from <原教程目录绝对路径>`。脚本只复制 `.local/` 数据，排除旧更新缓存和启动记录，不覆盖旧目录。进度来源不明确时先下载新包，再确认进度来源，不猜目录。路径有空格时正确引用，命令占位符必须先替换，不照抄作者电脑路径。
4. `start` 每次实时读取 main，下载完整 ZIP，逐文件校验，并将包内版本和文件清单与同一远端提交核对。下载期间 main 变化会重新下载，最多尝试三次。它不会用 `check` 的缓存，也不会因本地版本号相同就跳过下载。
5. 只有退出码为 0 且结果为 `status: ready`，才开始带做。记录返回的 `version`、`commit`、`directory` 和 `read_next`。向客户说明“已下载并校验项目完整包 vX.X.X，包含供 Codex 执行的程序／流程和给您阅读的 PDF 图文教程”，提供实际项目目录与返回的 `reader_directory` 链接，将实际目录与提交写入本机进度；下载核对时的 main 为最新依据，不承诺未来发布后仍自动同步。
6. 从返回的目录重新读取 `SKILL.md`，完整读完 `references/01-network.md`、`references/02-browser-iphone.md`，再读首页和带做指南。旧对话和旧进度仅用于确认客户已完成的操作，不作为推荐规则来源。按新目录的开场规则先询问设备是否登录过被 Claude 封禁的账号；已有答案复用，适用时先安排本地登录残留处理。进入 VPS 购买前重新核对新目录的套餐对照，不沿用旧推荐名单。执行成功后本轮不再重复本流程。

## 失败与恢复

- 先区分失败环节：无法启动终端、缺少 Python、GitHub API 限流／网络超时、ZIP 下载失败、解压校验失败，还是本机写入权限不足。说明实际检查结果，不把它们统称为“仓库没权限”，不直接要求用户手动下载。
- 脚本对临时网络错误自动重试一次；API 不可用时，提交查询可回退官方 Git，版本／清单回退同一提交的 raw 地址，ZIP 回退 `https://codeload.github.com/ninedaywoo-web/claude-setup-guide/zip/<本次提交号>`。备用下载仍需完整校验并复查 main，不使用第三方镜像，不以分支 ZIP 代替固定提交。
- 保留当前 VPN，检查报错对应域名的访问和当前终端代理配置；有可用的本机工具就由 AI 重试，不为下载测试先断旧 VPN。连接器失败时换本机工具；工具权限被拒绝时说明权限问题，按正常授权流程处理。
- 只有当前环境确实没有本机下载／写入工具、工具权限受限，或用户主动选择手动下载时，才请客户接手。优先给直接 ZIP 链接，说明“下载的是程序／流程＋PDF 的完整包，请保存并解压后把文件夹交给 Codex”；已取得提交就给固定提交直链，尚未取得可给 `https://github.com/ninedaywoo-web/claude-setup-guide/archive/refs/heads/main.zip`，明确尚未校验。网页里的 Code → Download ZIP 只作为直链也无法使用时的备用指导。手动下载后仍按等价流程核对提交、远端清单与最新 main，再开始带做。
- 尚未取得并校验最新完整包时，暂停 VPS 推荐、购买及配置；不静默降级为旧文件或凭记忆继续。
- 没有 Python：先协助准备 Python，或用可信工具完成等价流程（实时固定 main 提交、完整下载、安全解压、对照远端 manifest 逐文件校验、复查 main 未变化）。不能只读取 version.json 就声称校验成功。
- 不删除旧教程，不覆盖现有目标目录；有同名目录时选择新的目录。原进度缺失或包含符号链接时先排查，不强制覆盖或清理。
- 用户明确要求离线使用指定旧版时，以用户要求为准，说明实际版本和未联网核对状态。这是明确例外，不作为默认交付。
- 此流程适用于公开仓库，不改变组织私有领取服务的鉴权或下载契约。

## 日常继续

本次已成功启动后，仅继续当前步骤，不重复下载。之后普通本地调用仍按 SKILL.md 检查更新；用户再次发仓库链接要求开始或恢复时，重新执行本流程。启动收据 `.local/startup.json` 记录本次结果，不可作为下一次发链接时跳过下载的依据。
