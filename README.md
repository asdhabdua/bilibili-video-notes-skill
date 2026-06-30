# Bilibili Video Notes 📝

> **B站视频笔记生成Skill** — 从B站教育视频自动生成带截图的DOCX学习笔记

> 从B站教育视频自动生成带截图的DOCX学习笔记
>
> 全流程自动化：下载视频+字幕 → 全覆盖抽帧 → OCR去重 → AI视觉打分精选 → 融合生成DOCX

<p align="center">
  <img src="https://img.shields.io/badge/bilibili-1eabc9.svg?logo=bilibili&logoColor=white&style=flat-square" alt="Bilibili">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg?logo=python&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License">
</p>

---

## 🤖 一键提示词（复制粘贴给 AI 即可使用）

复制以下提示词，替换视频链接，粘贴给任何支持视觉的 AI（Hermes、Claude、GPT-4V、Gemini 等），AI 会自动完成所有步骤。

<details>
<summary>点击展开提示词</summary>

```
请帮我做这个B站视频的笔记：【替换为B站视频链接】

请按以下步骤执行：

第0步：安装 skill（如果还没装的话）
git clone https://github.com/asdhabdua/bilibili-video-notes-skill.git
cd bilibili-video-notes-skill
python install.py
# install.py 会自动检测你的AI环境（Hermes/Claude/Codex），把文件放到正确位置

第1步：读取 SKILL.md 了解完整工作流程
# Hermes: 读 SKILL.md
# Claude Code: 读 CLAUDE.md
# Codex: 读 AGENTS.md

第2步：配置 Cookie（用于下载B站AI字幕）
# 让用户从浏览器获取 SESSDATA：
# Edge/Chrome 打开 bilibili.com → F12 → Application → Cookies → SESSDATA
# 复制值后写入 bilibili_cookies.txt
# 如果用户暂时不想配置，可以跳过字幕，先用截图做笔记

第3步：运行脚本
python scripts/extract_frames.py <BV号> --page <页码> --mode cover --subtitle
python scripts/smart_select.py <frames_dir>/fixed --skip-clustering

第4步：两轮 Vision 打分（关键步骤，不能跳过）
第一轮：按知识点分组（不是按视觉相似）
  - 两张图结构一样但定义不同 → 不同知识点 → 都保留
  - 例：frame_A 定义"实体+协议"，frame_B 定义"接口+服务" → 两张都要
第二轮：每个知识点选最完整版
  - 更多标签、箭头、标注、定义的那张胜出

第5步：生成 DOCX 笔记
# 写作标准（最重要）：
# - 以顶级学者标准，融会贯通字幕+截图内容
# - 追求知识完整性，宁可多写不可遗漏
# - 不是照搬字幕，不是只写要点
# - 分节用大标题，开头写考研要求，结尾写要点总结
# - 每个知识点配截图+表格+公式+做题要点
# - 保留助记口诀，解释 WHY（为什么这样设计）
# - 不带时间戳，不覆盖已有文件

第6步：清理
# 删除视频MP4、JSON字幕、临时脚本
# 保留字幕TXT（参考用）

请从第0步开始执行。
```

</details>

---

## ✨ 功能特点

- 🎬 **自动下载** B站视频（720p）和 AI 字幕
- 📸 **全覆盖抽帧**（每10秒一帧），不丢任何画面
- 🔍 **OCR + 感知哈希双重去重**，129帧 → 20-30帧，不丢有价值内容
- 🧠 **AI视觉打分**，自动选出每个知识点最完整的一帧
- 📝 **融合字幕+截图**生成结构化DOCX笔记（不是照搬字幕，是知识融合）
- 🧹 **自动清理**临时文件，不占多余空间

## 📊 效果对比

| 输入 | 输出 |
|------|------|
| 21分钟B站视频 | 6-12张精选截图 + 完整知识点DOCX |
| 129帧原始截图 | 20帧去重后 → 8帧AI精选 |
| 448条字幕 | 融合进结构化笔记，不照搬 |

## 🚀 快速开始

### 1. 一键安装（推荐）

```bash
git clone https://github.com/你的用户名/bilibili-video-notes.git
cd bilibili-video-notes
pip install -r scripts/requirements.txt
python install.py
```

脚本会自动检测环境（Hermes Agent / Claude Code），把文件复制到正确位置，并引导你配置 Cookie。

```bash
# 或手动指定目标
python install.py --hermes    # 安装到 Hermes Agent
python install.py --claude    # 安装到 Claude Code
python install.py --codex     # 安装到 Codex CLI
python install.py --standalone # 仅安装依赖，手动使用
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

还需要系统安装 [FFmpeg](https://ffmpeg.org/download.html)（视频处理用）。

### 2. 准备 Cookie

B站 AI 字幕需要登录态。从浏览器获取 `SESSDATA`：

1. 用 Edge/Chrome 打开 [bilibili.com](https://www.bilibili.com)（确保已登录）
2. 按 `F12` 打开开发者工具
3. 点击 **Application**（应用程序）标签
4. 左侧 **Cookies** → `https://www.bilibili.com`
5. 找到 `SESSDATA`，复制它的值

```bash
# 创建 cookie 文件
cp bilibili_cookies.txt.example bilibili_cookies.txt
# 编辑，把 YOUR_SESSDATA_HERE 替换为你复制的值
```

> ⚠️ Cookie 有时效（通常几天），过期后需重新获取。

### 3. 一键运行

```bash
# 第一步：下载视频 + 字幕 + 全覆盖抽帧
python extract_frames.py BV19E411D78Q --page 9 --mode cover --subtitle

# 第二步：智能筛选（OCR去重）
python smart_select.py frames/fixed --skip-clustering

# 第三步：对 selected/ 里的帧做 AI 视觉打分，生成 DOCX
# （需要多模态 AI 模型支持，如 GPT-4V、Claude Vision 等）
```

## 📖 使用方法

### 基本用法（AI skill可以直接使用，如果没有agent可以按照这个流程使用）

```bash
# 完整视频：下载 + 字幕 + 每10秒抽帧
python extract_frames.py BV19E411D78Q --page 9 --mode cover --subtitle

# 只处理 5:00 到 10:00 片段
python extract_frames.py BV19E411D78Q --page 9 --start 5:00 --end 10:00 --mode cover --subtitle

# 只下载字幕，不下载视频
python extract_frames.py BV19E411D78Q --page 9 --subtitle --mode fixed --interval 9999 --no-download
```

### extract_frames.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `bvid` | B站视频 BV号 | 必填 |
| `--page N` | 分P号 | 1 |
| `--mode` | 抽帧模式：`cover`(每10秒) / `scene`(场景检测) / `fixed`(固定间隔) | scene |
| `--subtitle` | 同时下载AI字幕 | 否 |
| `--start MM:SS` | 起始时间 | 无 |
| `--end MM:SS` | 结束时间 | 无 |
| `--interval N` | 抽帧间隔秒数 | 30 |
| `--no-download` | 跳过下载，使用已有视频 | 否 |

### smart_select.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `frames_dir` | 输入帧目录 | 必填 |
| `--skip-clustering` | 跳过知识点聚类，保留所有去重帧 | 否 |
| `--ocr-threshold N` | OCR文字量阈值，低于此值视为无内容 | 20 |
| `--hash-threshold N` | 哈希距离阈值，低于此值视为相同帧 | 10 |
| `--text-threshold F` | OCR文本相似度阈值，低于此值拆分 | 0.7 |
| `--output-dir` | 输出目录 | 同级 selected/ |

## 🔧 完整工作流

```
129 帧（每10秒全覆盖）
  ↓ OCR 预筛：去掉空白/面部帧
  ↓ 哈希去重（视觉结构相似归为一组）→ 19 组
  ↓ 文本拆分（组内文字不同则拆开）→ 24 组
  ↓ [可选] 知识点聚类 → 15 个知识点
  ↓ AI 视觉打分（每帧 1-10 分）
  ↓ 选 ≥8 分 + 视觉去重（相似帧只保留最完整版）→ 6-12 帧
  ↓ 融合字幕+截图生成 DOCX
  ↓ 清理临时文件
```

### 为什么用"每10秒全覆盖"而不是"场景检测"？

| 方案 | 优点 | 缺点 |
|------|------|------|
| 场景检测 | 帧数少 | 讲课视频画面变化小，**会漏内容** |
| 每10秒全覆盖 | **绝对不漏** | 帧数多（129帧），但去重后只剩20帧 |

**结论：宁可多截再去重，也不能漏掉关键画面。**

## 🛠️ 自定义配置

### 修改工作目录

```bash
# 方式一：环境变量
export BILI_NOTES_WORKSPACE="/path/to/workspace"
export BILI_NOTES_FRAMES="/path/to/frames"  # 必须纯英文路径

# 方式二：直接修改脚本顶部的配置区
```

> ⚠️ 帧输出目录**必须是纯英文路径**，AI视觉工具可能无法识别中文路径。

### 使用不同的 AI 模型打分

脚本不绑定特定 AI 模型。`selected/` 目录里的帧可以交给任何支持视觉的模型打分：

- GPT-4V / GPT-4o
- Claude 3.5 Sonnet (Vision)
- Gemini Pro Vision
- 本地多模态模型（如 LLaVA）

**关键 Prompt：**
```
Score each frame 1-10 for educational content richness.
Among visually similar frames, pick ONLY the MOST COMPLETE version.
Never keep two versions of the same diagram.
```

## ❓ 常见问题

### B站限流（HTTP 412）

```bash
# 降级到 480p + 加 User-Agent
yt-dlp --user-agent "Mozilla/5.0 ..." -f "bestvideo[height<=480]+bestaudio/best[height<=480]" ...
```

### Cookie 过期

字幕下载失败但视频下载成功 → 先跳过字幕，后面补：
```bash
python extract_frames.py BV号 --page N --subtitle --no-download --mode fixed --interval 9999
```

### 帧太多 / API 调用太贵

129帧 → 用 `smart_select.py --skip-clustering` 压到 20-30 帧，再送 AI 打分，省 80% API 调用。

### Vision 选到了半成品截图

打分时必须在 prompt 里强调：**"Among visually similar frames, pick ONLY the MOST COMPLETE version"**，否则 AI 会随机选。

## 📁 输出文件说明

```
workspace/
├── bilibili_cookies.txt         # B站 Cookie
├── BV19E411D78Q_p9.mp4          # 下载的视频（处理后删除）
├── BV19E411D78Q_p9_subtitles.json  # 字幕原始数据
├── BV19E411D78Q_p9_subtitles.txt   # 字幕带时间戳文本（保留）
├── extract_frames.py
└── smart_select.py

frames/
├── fixed/                       # 全覆盖帧（129张）
└── selected/                    # 智能筛选后（20-30张）

notes/
└── 1.2.1_xxx_智能版.docx        # 最终笔记（内嵌截图）
```

## 📄 License

MIT License - 自由使用和修改。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载
- [RapidOCR](https://github.com/RapidAI/RapidOCR) - OCR 文字识别
- [ImageHash](https://github.com/JohannesBuchner/imagehash) - 感知哈希
- [python-docx](https://github.com/python-openxml/python-docx) - DOCX 生成
