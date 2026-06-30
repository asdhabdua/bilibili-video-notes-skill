# B站视频智能笔记工具

从B站教育视频自动生成带截图的DOCX学习笔记。

## 工作流程

1. 下载视频（720p）+ AI字幕
2. 每10秒全覆盖抽帧（不丢任何画面）
3. OCR + 感知哈希双重去重（129帧 → 20-30帧）
4. AI视觉打分，选最完整的截图（→ 6-12帧）
5. 融合字幕+截图生成DOCX笔记

## 使用方法

当用户提供B站视频链接并要求做笔记时：

```bash
# 第一步：下载视频+字幕+抽帧
python scripts/extract_frames.py BV19E411D78Q --page 9 --mode cover --subtitle

# 第二步：智能筛选
python scripts/smart_select.py <frames_dir>/fixed --skip-clustering

# 第三步：对 selected/ 里的帧做视觉打分（1-10分）
# 第四步：融合字幕+截图写DOCX
# 第五步：清理临时文件
```

## 关键规则

- **抽帧用 `--mode cover`**（每10秒），不用 scene（讲课视频会漏内容）
- **Vision打分prompt必须强调**："Among visually similar frames, pick ONLY the MOST COMPLETE version"
- **笔记不是照搬字幕**，是融合字幕+截图的知识文档
- **帧输出目录必须纯英文路径**

## Cookie

B站AI字幕需要SESSDATA cookie，存在 `bilibili_cookies.txt`。
过期后用户需从浏览器F12重新复制。

## 依赖

```bash
pip install yt-dlp imagehash rapidocr-onnxruntime python-docx Pillow
```

需要系统安装 ffmpeg。
