# Bilibili Video Notes

从 B 站教育/讲课视频生成带截图的 DOCX 学习笔记。

## Workflow

1. Download video + AI subtitles
2. Extract frames every 10 seconds (cover mode)
3. OCR + perceptual hash deduplication
4. Concurrent AI vision scoring, then manually select 7-12 final frames
5. Concurrent AI extraction of text/formulas/tables/concepts from final frames
6. Fuse subtitles + extracted image content into DOCX notes
7. Verify + clean up temporary files

## Setup

```bash
pip install -r scripts/requirements.txt
```

System ffmpeg required.

Configure API:

```bash
cp templates/env.example .env
# fill VISION_API_KEY, VISION_BASE_URL, VISION_MODEL
```

Configure Bilibili cookie:

```bash
cp bilibili_cookies.txt.example bilibili_cookies.txt
# fill SESSDATA from browser F12
```

## Usage

When the user provides a Bilibili link and asks for notes, run:

```bash
# 1. extract
python scripts/extract_frames.py <bvid> \
  --page <n> \
  --mode cover \
  --subtitle \
  --workspace ./workspace \
  --frames ./frames/pXX

# 2. deduplicate
python scripts/smart_select.py ./frames/pXX/fixed \
  --output-dir ./frames/pXX/selected \
  --skip-clustering

# 3. score all selected frames
python scripts/score_frames_concurrent.py \
  --frames ./frames/pXX/selected \
  --output ./workspace/vision_scores_pXX.json \
  --workers 16

# 4. manually choose final frames and copy to final/
mkdir -p ./frames/pXX/final
cp ./frames/pXX/selected/frame_XXXX.jpg ./frames/pXX/final/
# ...

# 5. extract content from final frames
python scripts/score_frames_concurrent.py \
  --frames ./frames/pXX/final \
  --output ./workspace/vision_extract_pXX.json \
  --mode extract \
  --workers 16

# 6. extract key causal sentences from subtitles before writing DOCX
python scripts/extract_key_sentences.py \
  ./workspace/<bvid>_p<n>_subtitles.txt

# 7. generate DOCX
cp templates/docx_note_v2.py ./workspace/gen_pXX_v1.py
# edit TITLE, SOURCE, FRAMES, SECTIONS based on subtitles + vision_extract_pXX.json
# make sure causal sentences in <bvid>_p<n>_subtitles.key.json are covered
python ./workspace/gen_pXX_v1.py

# 8. verify (with subtitle key-sentence coverage check)
python scripts/verify_docx.py ./workspace/<output>.docx --subtitle ./workspace/<bvid>_p<n>_subtitles.txt

# 9. cleanup
rm -f ./workspace/<bvid>_p<n>.mp4
rm -f ./workspace/<bvid>_p<n>_subtitles.json
rm -f ./workspace/gen_pXX_v1.py
```

## Critical Rules

- Use `--mode cover` for extraction, not scene mode
- Each video MUST use its own `frames/pXX/` directory; never share across videos
- Final frames MUST go to a separate `final/` directory
- Do NOT use serial `vision_analyze` calls; all vision analysis goes through `score_frames_concurrent.py`
- Frame directories must be pure English paths
- Notes should fuse subtitle text with extracted image content, not just summarize subtitles
- Use `run.bold` and `run.font.color` for emphasis; never use markdown syntax like `**xxx**`

## Note Quality Standards

- Write like a top scholar: fuse subtitles and screenshots
- Prefer completeness over brevity
- Keep all important details, formulas, definitions, examples, tips
- Explain WHY, not just WHAT
- No timestamps
- Screenshots should only supplement missing exam points, not copy non-essential details
