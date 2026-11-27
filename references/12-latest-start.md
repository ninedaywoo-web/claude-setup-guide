# 收到公开仓库链接后，下载最新版再开始

适用：用户发来 `https://github.com/ninedaywoo-web/claude-setup-guide` 要求开始或恢复带做（含仅发链接的情况）。由 AI 使用本机终端或下载工具自动完成完整包（程序／流程＋配图＋PDF）的下载与校验。

## 执行顺序

0. **启动前上下文自检**：当前对话若已有其他无关任务记录，先暂停并请客户新建空白对话再粘贴原指令；全新空白对话或恢复本项目带做时静默通过，直接进入第 1 步。客户明确回复「继续当前对话」后直接从第 1 步继续。
1. **实时获取 `main` 最新提交**：读取 `https://api.github.com/repos/ninedaywoo-web/claude-setup-guide/git/ref/heads/main` 取得 40 位 `object.sha`；API 限流或超时时改用 `git -c credential.helper= ls-remote https://github.com/ninedaywoo-web/claude-setup-guide.git refs/heads/main`。
2. **获取同提交的 `update.py`**：从 `https://raw.githubusercontent.com/ninedaywoo-web/claude-setup-guide/<提交号>/scripts/update.py` 保存到临时目录（raw 不可达时改用 GitHub Contents API 或本机 Git 取得），核对后运行。
3. **运行启动命令下载并校验完整包**：确认本机 Python 3.9+（Mac 用 `python3`，Windows 用 `py -3` 或 `python`），指定一个新的独立目录执行：
   ```text
   python3 <临时脚本绝对路径> start --destination <新目录绝对路径>
   ```
   恢复已有客户进度时追加 `--progress-from <原教程目录绝对路径>`，只迁移 `.local/` 个人进度并保留原目录完好。
4. **验收启动结果**：退出码为 0 且返回 `status: ready` 后，向客户说明“已下载并校验项目完整包 vX.X.X，包含供 Codex 执行的程序／流程和给您阅读的 PDF 图文教程”，附实际项目目录与 `reader_directory` 链接，并将目录和提交记录到本机进度。
5. **从新目录开始带做**：从返回的新目录重新读取 `SKILL.md` 与 `references/17-workflow-controller.md`，运行 `python3 scripts/workflow.py init`，直接按当前阶段带做（首次带做先问设备封禁经历）。本次启动完成后不再重复下载。

## 失败与备用通道

- **按实际环节排查**：先区分缺少 Python、网络超时、API 限流还是本机写入权限问题；保留当前可用 VPN，逐项处理后重试。
- **官方备用通道**：脚本自动重试临时网络错误；ZIP 备用地址为 `https://codeload.github.com/ninedaywoo-web/claude-setup-guide/zip/<提交号>`，下载后照常按远端 manifest 逐文件校验并复核 `main`。
- **无本机下载／写入能力时**：说明具体限制并直接提供固定提交 ZIP 链接（尚未取得提交时给 `https://github.com/ninedaywoo-web/claude-setup-guide/archive/refs/heads/main.zip`），请客户解压后把完整文件夹交给 Codex，再补齐校验后带做。用户明确要求离线使用指定旧版时，说明版本号后按其要求继续。
