# 本项目的 AI 入口

用户要照教程开始或继续配置时，读取 SKILL.md 并按其执行。开始前必须完整阅读 references/01-network.md 和 references/02-browser-iphone.md，其余章节按阶段读。

维护项目时，Markdown 是正文源文件，图片使用仓库内相对路径。禁止加入在线文档依赖、原帖链接、用户私人 IP 或凭据。更新用户提供的文字时保留其表达，不大幅改写。

发布修改时同步 version.json 与 CHANGELOG.md，运行 python3 scripts/manifest.py，再运行 python3 -m unittest discover -s tests。更新只改课程和脚本；.local/ 是使用者的数据，不提交、不覆盖。
