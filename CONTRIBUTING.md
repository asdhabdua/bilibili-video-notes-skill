# 贡献指南

感谢你对 Bilibili Video Notes 的关注！

## 提建议 / 报 Bug

1. 在 [Issues](https://github.com/asdhabdua/bilibili-video-notes-skill/issues) 页面创建新 Issue
2. 描述你的建议或遇到的问题
3. 如果是 Bug，请附上错误信息和复现步骤

## 提交代码

1. Fork 本仓库
2. 创建你的分支：`git checkout -b feature/你的功能名`
3. 提交更改：`git commit -m '添加了xxx功能'`
4. 推送：`git push origin feature/你的功能名`
5. 创建 Pull Request

## 代码风格

- 保持简洁，避免冗余
- 新增脚本请在顶部添加清晰的 docstring
- 不要在代码中硬编码个人 API key 或 Cookie
- 修改后运行 `python -m py_compile scripts/*.py` 确认语法正确

## 改进笔记质量

如果你发现了更好的截图选择策略、更清晰的排版方式，或者任何能让笔记质量更高的方法，欢迎提交 PR！

## 需要注意的事项

- 不要将 `.env` 或 `bilibili_cookies.txt` 提交到 Git
- 不要提交视频文件、帧图片、字幕文件等大文件
- 不要在文档中写入个人路径或隐私信息
- 更新 README 和相关 Agent 文件（SKILL.md / CLAUDE.md / AGENTS.md）保持一致

## 联系方式
- **提建议/报Bug**：[GitHub Issues](https://github.com/asdhabdua/bilibili-video-notes-skill/issues/new)
- **联系邮箱**：EugenegengU@outlook.com

欢迎提交 Issue 和 PR！
