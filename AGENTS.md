# Bilibili Video Notes

从 B 站教育/讲课视频生成带截图的 DOCX 学习笔记。

## 工作流程

1. 下载视频 + AI 字幕
2. 每 10 秒全覆盖抽帧
3. OCR + 感知哈希去重
4. AI 并发视觉打分，人工选出最终 7-12 帧
5. AI 并发提取最终帧中的文字/公式/表格/概念
6. 融合字幕 + 图中内容生成 DOCX
7. 验证 + 清理临时文件

## 安装

```bash
pip install -r scripts/requirements.txt
```

需要系统安装 ffmpeg。

配置 API：

```bash
cp templates/env.example .env
# 填写 VISION_API_KEY / VISION_BASE_URL / VISION_MODEL
```

配置 B 站 Cookie：

```bash
cp bilibili_cookies.txt.example bilibili_cookies.txt
# 填写 SESSDATA
```

## 使用方法

当用户提供 B 站视频链接并要求做笔记时，按以下步骤执行：

```bash
# 1. 抽帧
python scripts/extract_frames.py <BV号> \
  --page <N> \
  --mode cover \
  --subtitle \
  --workspace ./workspace \
  --frames ./frames/pXX

# 2. 去重
python scripts/smart_select.py ./frames/pXX/fixed \
  --output-dir ./frames/pXX/selected \
  --skip-clustering

# 3. 并发打分
python scripts/score_frames_concurrent.py \
  --frames ./frames/pXX/selected \
  --output ./workspace/vision_scores_pXX.json \
  --workers 16

# 4. 人工选最终帧，复制到 final/
mkdir -p ./frames/pXX/final
cp ./frames/pXX/selected/frame_XXXX.jpg ./frames/pXX/final/

# 5. 提取图中内容
python scripts/score_frames_concurrent.py \\
  --frames ./frames/pXX/final \\
  --output ./workspace/vision_extract_pXX.json \\
  --mode extract \\
  --workers 16

# 6. 生成 DOCX 前，提取字幕关键因果句
python scripts/extract_key_sentences.py \\
  ./workspace/<BV>_p<N>_subtitles.txt

# 7. 生成 DOCX
cp templates/docx_note_v2.py ./workspace/gen_pXX_v1.py
# 编辑 TITLE/SOURCE/FRAMES/SECTIONS，参考 <BV>_p<N>_subtitles.key.json 覆盖因果句
python ./workspace/gen_pXX_v1.py

# 8. 验证（含字幕关键因果句覆盖检查）
python scripts/verify_docx.py ./workspace/<output>.docx --subtitle ./workspace/<BV>_p<N>_subtitles.txt

# 9. 清理
rm -f ./workspace/<BV>_p<N>.mp4
rm -f ./workspace/<BV>_p<N>_subtitles.json
rm -f ./workspace/gen_pXX_v1.py


## 关键规则

- **抽帧用 `--mode cover`**，不用 scene（讲课视频会漏内容）
- **每个视频必须有独立的 `frames/pXX/` 目录**，禁止多视频共用
- **最终帧放入独立的 `final/` 目录**
- **不要用任何平台的 `vision_analyze` 串行调用**，所有视觉分析都走 `score_frames_concurrent.py`
- **帧目录必须是纯英文路径**
- **笔记不是照搬字幕**，是融合字幕 + 截图的知识文档

## 笔记写作标准

- 以顶级学者身份，融会贯通字幕和截图
- 追求知识完整性，宁可多写不可遗漏
- 保留所有重要细节、公式、定义、例题、做题技巧
- 解释 WHY，不只是 WHAT
- 不带时间戳
- 截图只补充字幕没讲的考点，不抄非考点内容

## 依赖

```bash
pip install yt-dlp imagehash rapidocr-onnxruntime python-docx Pillow requests python-dotenv
```

需要 ffmpeg。
