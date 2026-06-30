---
name: bilibili-video-notes
description: "B站视频智能笔记工具：下载视频+字幕→全覆盖抽帧→OCR去重→vision打分精选→融合生成DOCX。完整流程，不丢内容。"
tags: [bilibili, video, notes, OCR, vision, subtitles, docx, 考研]
triggers:
  - bilibili视频笔记
  - 视频笔记
  - 从视频做笔记
  - video notes
---

# B站视频智能笔记工具

从B站视频自动生成带截图的DOCX笔记。完整流程：下载→全覆盖抽帧→OCR去重→vision打分→融合字幕+截图生成DOCX。

## ⚠️ 笔记写作标准（最重要，必须遵守）

以顶级优秀学者的身份，把字幕内容和截图内容融会贯通，追求知识的完整性。用户要的是"什么都能查到的电子词典"，不是大致概括。

- 不是照搬字幕，不是只写要点
- 把老师讲的每一个知识点、每一张图的细节都完整保留并结构化整理
- 宁可多写不可遗漏
- 保留所有重要细节、公式、定义、例题、做题技巧
- 不带时间戳

### 排版规范

1. **分节用大标题**（一、二、三...），每节有明确主题
2. **开头写"考研要求"**，结尾写"本节要点总结"
3. **每个知识点配 1-2 张截图**，嵌在对应文字位置，加图注
4. **对比内容用表格**（如 OSI vs TCP/IP、各层功能对照）
5. **公式加粗大字号**（Pt 12-13），视觉突出
6. **关键术语加粗**，重要概念用红色或加粗标注
7. **解释 WHY**：不只是"是什么"，还解释"为什么这样设计"
8. **助记口诀**：如果有记忆技巧，一定要保留
9. **做题要点**：每个知识点末尾总结做题关键

### 质量标准

对截图数量、笔记行数不做硬性要求。核心标准：**把视频内容完整准确地总结好**。该多就多，该少就少，以内容完整性为准。

## 🤖 一键提示词（复制粘贴给 AI 即可使用）

以下提示词适用于任何支持视觉的 AI（Hermes Agent、Claude、GPT-4V、Gemini 等）。用户只需复制粘贴，替换视频链接即可。

---

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

---

**使用方法：**
1. 复制上面的提示词
2. 把【替换为B站视频链接】改成实际链接
3. 粘贴给 AI
4. AI 会自动完成所有步骤

**支持的 AI 平台：**
- Hermes Agent（读 SKILL.md）
- Claude Code（读 CLAUDE.md）
- Codex（读 AGENTS.md）
- GPT-4V / Gemini / 任何支持视觉的 AI（直接按提示词执行）

## 安装

### 方式一：Hermes Agent 用户（推荐）

```bash
# 克隆仓库
git clone https://github.com/你的用户名/bilibili-video-notes.git

# 复制到 Hermes skill 目录
# Windows:
xcopy /E /I bilibili-video-notes %USERPROFILE%\.hermes\skills\media\bilibili-video-notes
# macOS/Linux:
cp -r bilibili-video-notes ~/.hermes/skills/media/bilibili-video-notes

# 安装 Python 依赖
pip install -r ~/.hermes/skills/media/bilibili-video-notes/scripts/requirements.txt
```

安装后重启 Hermes，对 AI 说"帮我做这个视频的笔记"即可自动触发。

### 方式二：Claude Code / Codex 用户

```bash
git clone https://github.com/你的用户名/bilibili-video-notes.git
cd bilibili-video-notes
python install.py --claude  # 或 --codex
```

安装后 AI 会自动读取 CLAUDE.md（Claude Code）或 AGENTS.md（Codex）。

### 方式三：独立使用（不需要 AI 工具）

```bash
git clone https://github.com/你的用户名/bilibili-video-notes.git
cd bilibili-video-notes
pip install -r scripts/requirements.txt
# 按下方"脚本用法速查"手动运行
```

### 配置 Cookie

```bash
cp bilibili_cookies.txt.example bilibili_cookies.txt
# 编辑 bilibili_cookies.txt，填入你的 SESSDATA
```

获取 SESSDATA：Edge/Chrome 打开 bilibili.com → F12 → Application → Cookies → `SESSDATA`

## 依赖安装

```bash
pip install yt-dlp imagehash rapidocr-onnxruntime python-docx Pillow
```

需要 ffmpeg（系统已安装）。

## 文件结构

```
workspace/（如 D:\新建文件夹\hermes workspace\）
├── extract_frames.py      # 视频下载+字幕+抽帧
├── smart_select.py        # OCR预筛+哈希去重+文本拆分
├── bilibili_cookies.txt   # B站Cookie（SESSDATA）
├── *.mp4                  # 下载的视频（处理后删除）
├── *_subtitles.json       # 字幕原始数据（处理后可删）
└── *_subtitles.txt        # 字幕带时间戳文本（保留）

frames_output/（如 D:\hermes test\video summary\，必须纯英文路径）
├── fixed/                 # 全覆盖帧（每10秒一帧）
└── selected/              # 智能筛选后的帧

notes_output/
└── *.docx                 # 最终笔记
```

## 完整流程（6步）

### 第一步：下载视频+字幕+全覆盖抽帧

```bash
python extract_frames.py BV19E411D78Q --page 9 --mode cover --subtitle
```

参数：
- `--mode cover`：每10秒截一帧（全覆盖，不丢内容）
- `--mode scene`：场景检测（快但可能漏内容，不推荐）
- `--mode fixed --interval 20`：自定义间隔
- `--subtitle`：同时下载AI字幕
- `--start 5:00 --end 10:00`：只处理指定时间段

输出：视频MP4 + 字幕TXT + 129帧（21分钟视频）

### 第二步：智能筛选（去重）

```bash
python smart_select.py <frames_dir> --skip-clustering
```

流程：
1. **OCR预筛**：RapidOCR逐帧识别文字量，去掉空白/面部帧
2. **哈希去重**：pHash聚类，视觉结构相似的帧归为一组（129→20-30组）
3. **文本拆分**：组内OCR文字相似度<70%的帧拆开保留
   - 解决"长得像但内容不同"的问题（如同一张PPT上不同定义）
4. `--skip-clustering`：跳过知识点聚类，保留所有去重后的帧供vision二次筛选

输出：`selected/`目录，20-30帧

**⚠️ 脚本运行完后必须继续执行步骤3和4，不能停！**

### 第三步：两轮 Vision 打分

对`selected/`里的帧做两轮 vision 处理：

**第一轮：按知识点分组（不是按视觉相似）**

CRITICAL RULE: Two frames that look visually similar but teach DIFFERENT concepts should be in DIFFERENT groups. For example, if one frame defines "实体+协议" and another defines "接口+服务", they are DIFFERENT knowledge points even if the diagram layout is identical. Keep BOTH.

prompt: "按知识点分组，不是按视觉相似。两张图结构一样但定义不同→不同知识点→都保留"
输出：{帧号 → 知识点标签}，约 10-15 个知识点

**第二轮：每个知识点选最完整版**

对每个知识点内的所有帧打分（1-10），选最完整的一张。标准：更多标签、箭头、标注、定义的那张胜出。

**两轮 vision 的关键区别**：
- 旧方法（一轮）：按"视觉相似"分组 → "长得像"的帧合并 → 丢内容
- 新方法（两轮）：第一轮按"知识点"分组 → "长得像但教不同内容"的帧分开保留 → 不丢内容

- 输出：6-12张精选帧（全部≥8分）
- 如果帧数多（>15），用delegate_task并行分批打分

### 第四步：融合字幕+截图写DOCX

**核心原则**：
- **不是照搬字幕**，而是融会贯通——字幕提供"老师讲了什么"，截图提供"PPT/板书画了什么"
- 以顶级学者的标准追求**知识的完整性**
- 保留所有重要细节，不概括不删减
- 结构化：标题→概念定义→图表→公式→例题→总结

### 第五步：嵌入截图

将精选帧嵌入DOCX对应知识点位置，每张加图注。

### 第六步：清理

- 删除视频MP4（大文件）
- 删除临时脚本、JSON字幕
- 保留字幕TXT（参考用）

## Cookie管理

**当 Cookie 缺少或过期时，AI 必须提醒用户：**

> 需要你从浏览器获取 B站 Cookie 才能下载字幕：
> 1. 用 Edge/Chrome 打开 bilibili.com（确保已登录）
> 2. 按 F12 打开开发者工具
> 3. 点击 Application（应用程序）标签
> 4. 左侧 Cookies → https://www.bilibili.com
> 5. 找到 SESSDATA，复制它的值发给我
>
> 字幕下载失败不影响视频和截图，可以先跳过字幕继续。

**判断 Cookie 问题：** download_subtitles 返回空 / API 返回 No subtitles / 字幕文件无内容

**处理策略：**
1. 先尝试下载字幕，失败则提醒用户获取 SESSDATA
2. 用户提供新 SESSDATA → 写入 bilibili_cookies.txt → 重新下载
3. 用户跳过 → 继续用截图做笔记，字幕后面补

Cookie有时效，过期需重新获取：
1. Edge打开B站（已登录）
2. F12 → Application → Cookies → `https://www.bilibili.com`
3. 复制`SESSDATA`的值
4. 更新`bilibili_cookies.txt`

Cookie文件格式（Netscape）：
```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	FALSE	0	SESSDATA	<你的SESSDATA值>
```

## 效果保证要点

| 环节 | 质量保证 |
|------|---------|
| 抽帧 | 用`--mode cover`（每10秒），不用scene（会漏） |
| 去重 | 哈希去重+OCR文本拆分，两层保障 |
| 选帧 | vision打分时必须强调"选最完整版"，否则会选到半成品 |
| 写笔记 | 要求"融会贯通"，不是照搬字幕；追求知识完整性 |
| 不丢内容 | 129帧→20-40帧→6-12帧，每步都不丢有价值内容 |

## 踩坑记录（按重要性排序）

1. **场景检测会漏内容**：讲课视频画面变化小，纯场景检测（`--mode scene`）会漏掉大量 PPT/板书。必须用 `--mode cover`（每10秒全覆盖）。
2. **OCR去重会丢"长得像但内容不同"的帧**：同一张PPT上不同定义（如"实体+协议" vs "接口+服务"），pHash 认为是重复帧。解决：哈希去重后加一步 OCR 文本拆分（相似度<70%则拆开）。
3. **Vision按视觉相似分组会丢内容**：同一张PPT上"实体+协议"和"接口+服务"两个定义，视觉结构一样但内容不同，按视觉分组只会保留一张。解决：用两轮vision，第一轮按知识点分组（不是视觉相似），第二轮每组选最完整版。
4. **Vision不能读中文路径**：帧输出目录必须纯英文路径。
5. **OCR文字量≠视觉完整度**：之前用"保留OCR文字量最多的帧"策略，会选到文字多但图不完整的帧。解决：放弃OCR聚类，改用 vision 直接判断完整度。
6. **B站限流HTTP 412**：降级到480p + 加 User-Agent 可绕过。
7. **Edge Cookie被锁**：Edge运行时Cookie文件被独占锁定。解决：用户手动从F12复制SESSDATA。
8. **Cookie过期时AI必须提醒用户**：见"Cookie管理"章节的提醒模板。
9. **步骤3/4不能跳过**：脚本运行完后必须继续执行vision打分和DOCX生成，不能停在"去重完成"。
10. **视频下载后要清理**：MP4 文件 30-50MB，处理完必须删除。
11. **帧截图选最完整版**：同一内容有完整版和不完整版→只保留最完整版。多张图视觉相似但内容不同→都要保留。
12. **不同视频的帧不要混放**：每次处理前清理 fixed/ 和 selected/ 目录。
13. **Cookie更新后要同步到所有位置**：workspace的cookie、skill目录的cookie、压缩包里的cookie模板，三处要一致。打包前检查。
14. **路径配置不直观**：脚本默认找 `~/bilibili-notes/workspace/`，用户clone后在当前目录运行找不到。解决：优先找当前目录→环境变量→脚本所在目录→默认路径。
15. **视频清晰度静默降级**：720p下载失败时yt-dlp自动降到480p，用户不知道。解决：下载后用ffprobe打印实际分辨率。

## 常见问题

**B站限流（HTTP 412）**：降级到480p + 加User-Agent重试
```bash
yt-dlp --user-agent "Mozilla/5.0 ..." -f "bestvideo[height<=480]+bestaudio/best[height<=480]" ...
```

**Vision不能读中文路径**：帧输出目录必须用纯英文路径（如`D:/hermes_frames/`）

**帧太多/API调用太多**：`--skip-clustering`模式保留20-40帧供vision筛选，比129帧全打分省80%

**Cookie过期**：字幕下载失败但视频下载成功 → 分开处理，字幕后面补

## GitHub 发布

见 `references/github-publishing.md`。

## Vision 打分 + DOCX 生成

详细的打分 prompt 模板、DOCX 代码模板、内容组织原则见 `references/vision-and-docx-guide.md`。

## 脚本用法速查

```bash
# 完整流程：视频+字幕+全覆盖抽帧
python extract_frames.py BV19E411D78Q --page 9 --mode cover --subtitle

# 只下载字幕，不下载视频
python extract_frames.py BV19E411D78Q --page 9 --subtitle --mode fixed --interval 9999 --no-download

# 只处理 5:00-10:00 片段
python extract_frames.py BV19E411D78Q --page 9 --start 5:00 --end 10:00 --mode cover --subtitle

# 智能筛选（跳过聚类，保留所有去重后的帧）
python smart_select.py <frames_dir> --skip-clustering

# 智能筛选（含知识点聚类，每个知识点只保留一帧）
python smart_select.py <frames_dir>
```
