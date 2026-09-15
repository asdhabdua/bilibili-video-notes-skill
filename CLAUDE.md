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
#    WARNING: you MUST visually open every frame. Scores and OCR both
#    rank chapter title cards highly, but they are worthless in a note.
#    See "Frame Selection Rules".
mkdir -p ./frames/pXX/final
cp ./frames/pXX/selected/frame_XXXX.jpg ./frames/pXX/final/
# ...

# 4b. [REQUIRED for exercise / procedure videos] dense re-extraction per movement
#     cover mode samples 1 frame / 10s and misses the mid-phases of a movement.
#     Locate each movement's time range from the subtitles, then re-extract.
python scripts/extract_frames.py <bvid> --page <n> \
  --mode fixed --interval 2 --start MM:SS --end MM:SS \
  --workspace ./workspace --frames ./frames/pXX/fix_<movement>

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
- Visually inspect every final frame before writing; scores and OCR both over-rank title cards

## Frame Selection Rules

### Always look at the images; never trust scores alone

Both the OCR pre-filter in `smart_select.py` and the vision scoring in
`score_frames_concurrent.py` **systematically over-rank chapter title cards** —
they contain lots of clean text, so OCR character counts are high and the model
often gives them 8-9. But a title card adds **zero** value to a note, because
that text already appears in your Markdown heading.

**Open every image in `final/` before finalizing.**

### Reject these frame types

| Type | Signature | Action |
| :--- | :--- | :--- |
| **Chapter title card** | Large heading text (e.g. "〈Stage 3〉Raise your arms…"), flat/blurred background | Re-extract real footage from that section |
| **Text-only info card** | Full-screen list of text duplicating your body bullets | Delete; use no image |
| **Talking head** | Face + subtitle only, no demo, no diagram, no annotation | Delete; use no image |
| **Animation transition** | Diagram mid fade-in, cropped, or ghosted | Re-extract a stable frame |

> A section with **no image** is better than a section with a zero-information image.
> Not every section needs a picture.

### Image must match the text

Verify **what the image actually depicts**, not just which section it came from.

- Bad: a paragraph about *deep* muscles (transversus abdominis / multifidus)
  illustrated with a diagram of *superficial* muscles (erector spinae / rectus
  abdominis). These are opposing concepts; the mismatch misleads the reader.
- Check anatomical labels in diagrams and body position in demo shots.

### Exercise / procedure content: one image SET per movement, not one image

A single static frame cannot convey a movement. For each movement, capture:

1. **Start position** — full setup (props, hand placement, joint angles)
2. **Bottom / end range** — the phase with maximum excursion
3. **Return / opposite side** — alternating movements need the contralateral phase
4. **Decision moment** — if the source explains "when to stop" or "when to regress", capture that frame
5. **Error demo** — if the source demonstrates the wrong form, give it its own image

### Captions describe the frame, not the heading

- Bad: caption "Stage 3: raise your arms" under a "Stage 3" heading (redundant)
- Good: caption "② Single leg lowers — heel lightly touches the floor, pelvis must not tilt forward"

### Image naming

`<video-short-name>-<index><letter>-<what-it-shows>.jpg`. Use the same number
with incrementing letters for frames belonging to one movement:

```
deadbug-09a-阶段2双手固定骨盆.jpg
deadbug-09b-阶段2脚跟轻触地面.jpg
deadbug-09d-阶段2半程判定时机.jpg
```

### Final checks

- Every image reference resolves
- No **orphan images** left behind after replacing frames — delete the old ones

## Note Quality Standards

- Write like a top scholar: fuse subtitles and screenshots
- Prefer completeness over brevity
- Keep all important details, formulas, definitions, examples, tips
- Explain WHY, not just WHAT
- No timestamps
- Screenshots should only supplement missing exam points, not copy non-essential details
