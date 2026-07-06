# Bilibili Video Notes 📝

> **B站视频笔记生成工具** — 从B站教育/讲课视频自动生成带截图的DOCX学习笔记
>
> 全流程：下载视频+字幕 → 全覆盖抽帧 → OCR去重 → AI视觉打分精选 → 提取图中内容 → 融合生成DOCX

<p align="center">
  <img src="https://img.shields.io/badge/bilibili-1eabc9.svg?logo=bilibili&logoColor=white&style=flat-square" alt="Bilibili">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg?logo=python&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License">
</p>

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

### 4. 配置 B 站 Cookie

```bash
cp bilibili_cookies.txt.example bilibili_cookies.txt
```

从浏览器 F12 复制 `SESSDATA` 字段，替换文件中的 `YOUR_SESSDATA_HERE`。

> ⚠️ Cookie 有时效（通常几天），过期后需重新获取。

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
