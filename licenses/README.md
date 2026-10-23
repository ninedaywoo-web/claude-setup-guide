# 清理模块来源（维护资料）

客户入口统一显示“Mac 端清理 Skill”“Windows 端清理 Skill”。原作者署名和许可保留在这里与对应许可文件，不要求客户安装原项目。

- Mac：`suyuan2022/suyuan-skill`，提交 `8babd4557a4774ca8e3d5b784d82f0ee5a4565e5`，`claude-cleanup/scripts/claude_cleanup.py` 及其测试。脚本内置于 `scripts/vendor/mac_cleanup/`，仅调整用户可见标题；平台入口与项目操作说明另行编写。来源：https://github.com/suyuan2022/suyuan-skill/tree/8babd4557a4774ca8e3d5b784d82f0ee5a4565e5/claude-cleanup 。许可见 [mac-cleanup-MIT.txt](mac-cleanup-MIT.txt)。
- Windows：`liseami/CCBaga`，提交 `bdfb90ceadfc5fae6772ffff597bddecb0b73cc3`。参考并改写 `src-tauri/src/cleaner_config.rs` 的账号／凭据键白名单与 `cleaner_targets.rs` 的 Windows 路径和桌面存储范围，独立实现 Python 审计、备份、可恢复清理。来源：https://github.com/liseami/CCBaga/tree/bdfb90ceadfc5fae6772ffff597bddecb0b73cc3/src-tauri/src 。许可见 [windows-cleanup-MIT.txt](windows-cleanup-MIT.txt)。未集成 Tauri UI、身份保险库、历史删除、系统设置或伴生浏览器指纹引擎。

交付软件在运行时从官方固定版本地址下载并校验，安装包独立保存：3x-ui https://github.com/MHSanaei/3x-ui/releases/tag/v3.10.2 、Xray https://github.com/XTLS/Xray-core/releases/tag/v26.7.28 、Karing https://github.com/KaringX/karing/releases/tag/v1.2.25.2802 。
