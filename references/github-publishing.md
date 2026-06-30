# GitHub 发布指南

## 仓库结构

```
bilibili-video-notes/
├── README.md
├── LICENSE (MIT)
├── requirements.txt
├── extract_frames.py
├── smart_select.py
├── bilibili_cookies.txt.example
├── .gitignore
└── docs/screenshots/
```

## .gitignore

```
bilibili_cookies.txt
*.mp4
*_subtitles.json
frames/
__pycache__/
*.docx
```

## 脚本改造：硬编码路径 → 环境变量

```python
WORKSPACE = os.environ.get("BILI_NOTES_WORKSPACE", "./workspace")
FRAMES_DIR = os.environ.get("BILI_NOTES_FRAMES", "./frames")
COOKIE_FILE = os.path.join(WORKSPACE, "bilibili_cookies.txt")
```

## README 关键要素

1. 一句话说明 + 效果对比图
2. 功能特点（emoji 列表）
3. 快速开始（3步：安装→Cookie→运行）
4. 参数表格
5. 工作流图（129→20→8帧→DOCX）
6. FAQ（限流/Cookie/中文路径/API成本）
7. License + 致谢

## 效果截图（README 用）

- 视频原始画面 vs DOCX 成品对比
- 129帧→8帧去重效果
