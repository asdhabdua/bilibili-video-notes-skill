# Bilibili Video Notes 📝

> **B站视频笔记生成工具** — 从B站教育/讲课视频自动生成带截图的DOCX学习笔记，如果觉得有用的话记得点一下星标哦
>
> 全流程：下载视频+字幕 → 全覆盖抽帧 → OCR去重 → AI视觉打分精选 → 提取图中内容 → 融合生成DOCX

<p align="center">
  <img src="https://img.shields.io/badge/bilibili-1eabc9.svg?logo=bilibili&logoColor=white&style=flat-square" alt="Bilibili">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg?logo=python&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License">
</p>

## 目录

- [一键安装（复制粘贴给 AI）](#-%E4%B8%80%E9%94%AE%E5%AE%89%E8%A3%85%E5%A4%8D%E5%88%B6%E7%B2%98%E8%B4%B4%E7%BB%99-ai)
- [功能特点](#-%E5%8A%9F%E8%83%BD%E7%89%B9%E7%82%B9)
- [快速开始](#-%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B)
- [详细使用教程](#-%E8%AF%A6%E7%BB%86%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B)
- [配置好之后如何使用](#-%E9%85%8D%E7%BD%AE%E5%A5%BD%E4%B9%8B%E5%90%8E%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A8)
- [完整工作流](#-%E5%AE%8C%E6%95%B4%E5%B7%A5%E4%BD%9C%E6%B5%81)
- [命令参考](#-%E5%91%BD%E4%BB%A4%E5%8F%82%E8%80%83)
- [常见问题](#-%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98)
- [Agent 使用](#-agent-%E4%BD%BF%E7%94%A8)
- [目录结构](#-%E7%9B%AE%E5%BD%95%E7%BB%93%E6%9E%84)
- [License / 反馈](#-license)

---

## ⚡ 一键安装（复制粘贴给 AI）

```
请帮我安装 bilibili-video-notes-skill：

git clone https://github.com/asdhabdua/bilibili-video-notes-skill.git
cd bilibili-video-notes-skill
pip install -r scripts/requirements.txt

安装完成后，配置 .env 和 bilibili_cookies.txt，然后读取 README.md 了解如何使用。
```

---

## ✨ 功能特点

- 🎬 **自动下载** B站视频和 AI 字幕
- 📸 **全覆盖抽帧**（每10秒一帧），不丢任何画面
- 🔍 **OCR + 感知哈希双重去重**，129帧 → 20-40帧，不丢有价值内容
- 🧠 **AI视觉打分**，选出每个知识点最完整的一帧
- 📝 **融合字幕+截图内容**生成结构化DOCX笔记
- 🧹 **自动清理**临时文件，不占多余空间
- 🤖 **多 Agent 支持**：Hermes / Claude Code / Codex CLI

## 📊 效果对比

| 输入 | 输出 |
|------|------|
| 21分钟B站视频 | 7-12张精选截图 + 完整知识点DOCX |
| 129帧原始截图 | 20-40帧去重后 → 7-12帧AI精选 |
| AI 字幕文本 | 融合进结构化笔记，不照搬 |

---

## 🚀 快速开始

### 1. 克隆安装

```bash
git clone https://github.com/asdhabdua/bilibili-video-notes-skill.git
cd bilibili-video-notes-skill
pip install -r scripts/requirements.txt
```

### 2. 安装 FFmpeg

系统环境变量中需要可直接调用 `ffmpeg`。

### 3. 配置 API

```bash
cp templates/env.example .env
```

编辑 `.env`：

```bash
VISION_API_KEY=your_api_key_here
VISION_BASE_URL=https://api.openai.com/v1
VISION_MODEL=gpt-4o
```

支持任何 OpenAI 兼容格式的多模态 API（OpenAI、Sophnet、本地 vLLM 等）。

### 4. 配置 B 站 Cookie（可以直接告诉AI让他代劳）

```bash
cp bilibili_cookies.txt.example bilibili_cookies.txt
```

从浏览器 F12 复制 `SESSDATA` 字段，替换文件中的 `YOUR_SESSDATA_HERE`。

> ⚠️ Cookie 有时效（通常几天），过期后需重新获取。

---

## 🚀 详细使用教程

### 第一步：准备环境

#### 1.1 克隆仓库

```bash
git clone https://github.com/asdhabdua/bilibili-video-notes-skill.git
cd bilibili-video-notes-skill
```

#### 1.2 安装 Python 依赖

```bash
pip install -r scripts/requirements.txt
```

如果使用 Anaconda：

```bash
conda create -n bili-notes python=3.11
conda activate bili-notes
pip install -r scripts/requirements.txt
```

#### 1.3 安装 FFmpeg

本工具需要 `ffmpeg` 处理视频。

**Windows 安装方法**：
1. 下载：https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
2. 解压到 `C:\\ffmpeg`
3. 把 `C:\\ffmpeg\\bin` 加到系统环境变量 PATH
4. 重新打开终端，验证：`ffmpeg -version`

**macOS**：
```bash
brew install ffmpeg
```

**Ubuntu/Debian**：
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

---

### 第二步：配置 API

复制示例文件：

```bash
cp templates/env.example .env
```

编辑 `.env`：

```bash
VISION_API_KEY=your_api_key_here
VISION_BASE_URL=https://api.openai.com/v1
VISION_MODEL=gpt-4o
```

#### 常用 API 配置示例

**OpenAI**：
```bash
VISION_API_KEY=sk-...
VISION_BASE_URL=https://api.openai.com/v1
VISION_MODEL=gpt-4o
```

**Sophnet**：
```bash
VISION_API_KEY=...
VISION_BASE_URL=https://www.sophnet.com/api/open-apis/v1
VISION_MODEL=qwen3-vl-plus
```

**本地 vLLM**：
```bash
VISION_API_KEY=not-needed
VISION_BASE_URL=http://localhost:8000/v1
VISION_MODEL=your-local-model
```

---

### 第三步：配置 B 站 Cookie

B 站 AI 字幕需要登录态才能下载。

复制示例文件：

```bash
cp bilibili_cookies.txt.example bilibili_cookies.txt
```

获取 SESSDATA 的方法：

1. 用 Edge/Chrome 打开 [bilibili.com](https://www.bilibili.com) （确保已登录）
2. 按 `F12` 打开开发者工具
3. 点击 **Application**（应用程序）标签
4. 左侧 **Cookies** → `https://www.bilibili.com`
5. 找到 `SESSDATA`，复制它的值
6. 替换 `bilibili_cookies.txt` 里的 `YOUR_SESSDATA_HERE`

文件格式如下：

```
.bilibili.com  TRUE  /  FALSE  0  SESSDATA  你的SESSDATA值
```

> ⚠️ Cookie 通常有效期几天，过期后字幕下载会失败，需要重新获取。

---

### 第四步：告诉 AI 让它代劳

你不需要自己动手配置。把下面的提示词复制粘贴给 AI，它会帮你完成安装、配置、以及后续抽帧、去重、打分、写笔记的全部流程。

#### Hermes Agent 版

```
请帮我做这个 B 站视频的笔记：https://www.bilibili.com/video/BV1xx411c7mD

请严格按照本项目 SKILL.md 中的流程执行，不要凭印象。

首先，帮我完成初始化配置：
1. 克隆本仓库到当前工作目录：git clone https://github.com/asdhabdua/bilibili-video-notes-skill.git
2. 进入项目目录并安装依赖：pip install -r scripts/requirements.txt
3. 确保系统可以调用 ffmpeg（如果没有，请帮我安装并加入 PATH）
4. 从 templates/env.example 复制出 .env，然后问我 API 配置（VISION_API_KEY、VISION_BASE_URL、VISION_MODEL），填入后给我确认
5. 从 bilibili_cookies.txt.example 复制出 bilibili_cookies.txt，然后问我要 B 站 SESSDATA，填入后给我确认

初始化完成后，再按 SKILL.md 执行笔记生成流程。

注意事项：
- 帧目录必须是纯英文路径
- 不要使用 vision_analyze 串行调用
- 笔记要融会贯通字幕和截图，宁可多写不可遗漏
```

#### Claude Code 版

```
请帮我完成从头到尾的 B 站视频笔记工作流。

视频链接：https://www.bilibili.com/video/BV1xx411c7mD

首先做初始化配置：
1. git clone https://github.com/asdhabdua/bilibili-video-notes-skill.git
2. cd bilibili-video-notes-skill
3. pip install -r scripts/requirements.txt
4. 检查 ffmpeg 是否存在，不存在则帮我安装
5. cp templates/env.example .env，然后问我要 VISION_API_KEY / VISION_BASE_URL / VISION_MODEL，填入后让我确认
6. cp bilibili_cookies.txt.example bilibili_cookies.txt，然后问我要 B 站 SESSDATA，填入后让我确认

初始化完成后，再按 CLAUDE.md 执行笔记生成流程。
```

#### Codex CLI 版

```
请帮我完成从头到尾的 B 站视频笔记工作流。

视频链接：https://www.bilibili.com/video/BV1xx411c7mD

首先完成初始化配置：
1. git clone https://github.com/asdhabdua/bilibili-video-notes-skill.git
2. cd bilibili-video-notes-skill
3. pip install -r scripts/requirements.txt
4. 确保 ffmpeg 可用
5. cp templates/env.example .env，然后问我要 VISION_API_KEY / VISION_BASE_URL / VISION_MODEL，填入后让我确认
6. cp bilibili_cookies.txt.example bilibili_cookies.txt，然后问我要 B 站 SESSDATA，填入后让我确认

初始化完成后，再按 AGENTS.md 执行笔记生成流程。
```

---

## 📖 配置好之后如何使用

当你已经完成以下配置：
- Python 依赖已安装
- `.env` 中已填入有效的 VISION_API_KEY / BASE_URL / MODEL
- `bilibili_cookies.txt` 中已填入有效的 SESSDATA
- ffmpeg 可在终端直接调用

只需要告诉 AI一句话，它就会跟踪完整流程：

### Hermes Agent 版

```
请帮我做这个视频的笔记：https://www.bilibili.com/video/BV1xx411c7mD

按照 SKILL.md 流程执行，不要凭印象。
```

### Claude Code 版

```
请帮我做这个视频的笔记：https://www.bilibili.com/video/BV1xx411c7mD

已配置好 .env 和 bilibili_cookies.txt，按照 CLAUDE.md 执行。
```

### Codex CLI 版

```
请帮我做这个视频的笔记：https://www.bilibili.com/video/BV1xx411c7mD

已配置好 .env 和 bilibili_cookies.txt，按照 AGENTS.md 执行。
```

### 笔记生成流程

AI 会自动执行以下步骤：

1. **抽帧**：`extract_frames.py` 下载视频、字幕、每10秒全覆盖抽帧
2. **去重**：`smart_select.py` 用 OCR + 哈希去重，129帧 → 20-40帧
3. **打分**：`score_frames_concurrent.py --mode score` 并发给所有帧打分
4. **选帧**：AI 根据 score/theme 选出最终 7-12 帧
5. **提取**：`score_frames_concurrent.py --mode extract` 并发提取图中文字/公式/表格/概念
6. **生成 DOCX**：基于字幕 + 图中内容生成笔记
7. **验证**：`verify_docx.py` 检查 DOCX 格式
8. **清理**：删除视频MP4、JSON字幕、临时脚本

### 查收结果

AI 执行完毕后，你应该在 `workspace/` 目录下看到：

```
workspace/
├── <BV>_p<N>_subtitles.txt      # 字幕文本（保留）
├── vision_scores_pXX.json       # 帧打分结果（保留）
├── vision_extract_pXX.json      # 图中内容提取结果（保留）
└── X.X_章节标题_v1.docx     # 最终笔记
```

如果一切正常，直接打开 DOCX 查看即可。

---

### 第六步：手动微调（如需要）

AI 生成的 DOCX 可能需要你微调：
- 某些帧可能选得不太好，可以替换
- 正文部分可能需要根据你的理解补充
- 排版风格可以在 `docx_note_v2.py` 中调整

---

## 📖 完整工作流

```
129 帧（每10秒全覆盖）
  ↓ OCR 预筛：去掉空白/面部帧
  ↓ 哈希去重（视觉结构相似归为一组）→ 20-40 帧
  ↓ AI 视觉打分（1-10 分）
  ↓ 人工选出最终 7-12 帧
  ↓ AI 提取图中文字/公式/表格/概念
  ↓ 融合字幕 + 图中内容生成 DOCX
  ↓ 验证 + 清理临时文件
```

### 为什么要分 score 和 extract 两步？

| 步骤 | 看的帧数 | AI 输出内容 | 目的 | token 成本 |
|------|----------|------------|------|-----------|
| score | 20-40 | theme/keywords/score/complete | 选帧 | 低 |
| extract | 7-12 | 图中完整文字/公式/表格/概念 | 写正文 | 高 |

分开可以最小化总 token 和 API 成本，同时避免用任何平台的 `vision_analyze` 串行调用。

---

## 🔧 命令参考

### 1. 抽帧

```bash
python scripts/extract_frames.py BV1xx411c7mD \
  --page 1 \
  --mode cover \
  --subtitle \
  --workspace ./workspace \
  --frames ./frames/pXX
```

### 2. 去重

```bash
python scripts/smart_select.py ./frames/pXX/fixed \
  --output-dir ./frames/pXX/selected \
  --skip-clustering
```

### 3. 并发打分

```bash
python scripts/score_frames_concurrent.py \
  --frames ./frames/pXX/selected \
  --output ./workspace/vision_scores_pXX.json \
  --workers 16
```

### 4. 人工选最终帧

根据 `vision_scores_pXX.json` 的 score 和 theme，人工决定最终使用哪几帧。

```bash
mkdir -p ./frames/pXX/final
cp ./frames/pXX/selected/frame_0003.jpg ./frames/pXX/final/
cp ./frames/pXX/selected/frame_0007.jpg ./frames/pXX/final/
# ...
```

### 5. 提取图中内容

```bash
python scripts/score_frames_concurrent.py \
  --frames ./frames/pXX/final \
  --output ./workspace/vision_extract_pXX.json \
  --mode extract \
  --workers 16
```

### 6. 生成 DOCX

```bash
cp templates/docx_note_v2.py ./workspace/gen_pXX_v1.py
# 编辑 gen_pXX_v1.py 填入 TITLE/SOURCE/FRAMES/SECTIONS
python ./workspace/gen_pXX_v1.py
```

### 7. 验证

```bash
python scripts/verify_docx.py ./workspace/<output>.docx
```

### 8. 清理

```bash
rm -f ./workspace/BV1xx411c7mD_p1.mp4
rm -f ./workspace/BV1xx411c7mD_p1_subtitles.json
rm -f ./workspace/gen_pXX_v1.py
```

保留：字幕.txt、笔记.docx、vision_scores_pXX.json、vision_extract_pXX.json、checklist_pXX.json

---

## ⚙️ 配置参数

| 环境变量 / 参数 | 说明 | 示例 |
|---|---|---|
| `.env` | API key / base_url / model | 见 templates/env.example |
| `--workspace` | 工作区目录 | `./workspace` |
| `--frames` | 帧输出目录 | `./frames/pXX` |
| `--page` | B 站分P页码 | `1` |
| `--mode cover` | 每10秒抽一帧 | - |
| `--skip-clustering` | 保留所有去重帧 | - |
| `--workers` | 并发线程数 | `16` |
| `--mode extract` | 从图中提取完整内容 | - |

---

## 🛠️ 常见问题

### B 站限流（HTTP 412）

```bash
# 降级到 480p + 加 User-Agent
yt-dlp --user-agent "Mozilla/5.0 ..." -f "bestvideo[height<=480]+bestaudio/best[height<=480]" ...
```

### Cookie 过期

字幕下载失败但视频下载成功 → 先跳过字幕，后面补：

```bash
python scripts/extract_frames.py BV号 --page N --subtitle --no-download --mode fixed --interval 9999
```

### 帧目录必须是纯英文路径

AI 视觉工具可能无法识别中文路径。

### 帧太多 / API 调用太贵

129帧 → 用 `smart_select.py --skip-clustering` 压到 20-40帧，再送 AI 打分，省 60%-80% API 调用。

### Vision 选到了半成品截图

打分时使用的 prompt 已内置强调：**"Among visually similar frames, pick ONLY the MOST COMPLETE version"**。

---

## 🤖 Agent 使用

### Hermes Agent

直接读取 `SKILL.md`，按里面的流程执行。

### Claude Code

`CLAUDE.md` 会被自动加载为项目指令。

### Codex CLI

`AGENTS.md` 会被自动加载为项目指令。

---

## 📁 目录结构

```
bilibili-video-notes/
├── README.md
├── SKILL.md                    # Hermes Agent
├── CLAUDE.md                   # Claude Code
├── AGENTS.md                   # Codex CLI
├── CONTRIBUTING.md             # 贡献指南
├── .gitignore
├── bilibili_cookies.txt.example
├── scripts/
│   ├── extract_frames.py
│   ├── smart_select.py
│   ├── score_frames_concurrent.py
│   ├── verify_docx.py
│   ├── verify_checklist.py
│   ├── clean_markdown_bold.py
│   └── requirements.txt
├── templates/
│   ├── docx_note_v2.py
│   ├── env.example
│   └── checklist.json
```

---

## 📄 License

MIT License - 自由使用和修改。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载
- [RapidOCR](https://github.com/RapidAI/RapidOCR) - OCR 文字识别
- [ImageHash](https://github.com/JohannesBuchner/imagehash) - 感知哈希
- [python-docx](https://github.com/python-openxml/python-docx) - DOCX 生成

## 📬 反馈与建议

- **提建议/报Bug**：[GitHub Issues](https://github.com/asdhabdua/bilibili-video-notes-skill/issues/new)
- **功能请求**：[GitHub Discussions](https://github.com/asdhabdua/bilibili-video-notes-skill/discussions)
- **邮箱**：EugenegengU@outlook.com

欢迎提交 Issue 和 PR！
