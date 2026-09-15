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
#    ⚠️ 必须逐张「看图」确认，不能只信打分和 OCR，详见「选帧规则」
mkdir -p ./frames/pXX/final
cp ./frames/pXX/selected/frame_XXXX.jpg ./frames/pXX/final/

# 4b. 【动作/操作类视频必做】为每个动作补密集抽帧
#     cover 模式每 10 秒一帧，会漏掉动作的中间相；
#     对每个动作各自的时间段用 --start/--end + 小 interval 重抽
python scripts/extract_frames.py <BV号> --page <N> \
  --mode fixed --interval 2 --start MM:SS --end MM:SS \
  --workspace ./workspace --frames ./frames/pXX/fix_<动作名>

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

## 选帧规则

### 必须亲眼看图，不能只看打分

`smart_select.py` 的 OCR 预筛和 `score_frames_concurrent.py` 的视觉打分**都会把标题卡误判为高价值帧**——标题卡文字多、结构清晰，OCR 字符数高、模型也容易给 8~9 分。但标题卡对笔记的价值是**零**，因为那段文字你已经写进 Markdown 标题里了。

**定稿前必须逐张打开 `final/` 里的图确认。**

### 判定为「无效帧」，一律替换或删除

| 类型 | 特征 | 处理 |
| :--- | :--- | :--- |
| **章节标题卡** | 大字标题（如「〈阶段3〉举起胳膊…」「step3. 根据症状部位…」），纯色/虚化背景 | 回原片重抽该段的实拍画面 |
| **纯文字信息卡** | 满屏文字罗列（如「术后3个月以上/螺钉稳定/无骨质疏松」），内容与正文 bullet 完全重复 | 直接删除，不配图 |
| **纯说话镜头** | 只有人脸+字幕，无演示、无图示、无标注 | 直接删除，不配图 |
| **动画过渡帧** | 图示正在淡入淡出、被裁切或重影 | 重抽该段的稳定帧 |

> 宁可某一节**没有配图**，也不要塞一张零信息量的图。不是每一节都需要图。

### 图文必须对应

选图时要核对**图里画的到底是什么**，不能只看它属于哪个时间段。

- 反例：讲「深层肌肉（腹横肌/多裂肌）」的段落，配了一张**浅层肌肉（竖脊肌/腹直肌）**的解剖图——两者是对立概念，配反了会误导。
- 做法：解剖图要确认标注的肌肉名称；动作图要确认姿势与该节描述一致。

### 动作/操作类内容：每个动作配一组图，而不是一张

对健身、康复、手法、操作演示这类视频，**单张静态图无法表达动作过程**。每个动作按下列清单补齐：

1. **🧍 起始姿势** — 完整的准备位（含辅助物、手的位置、关节角度）
2. **① 动作至底/极限位** — 幅度最大的那一相
3. **② 回位/另一相** — 交替类动作要拍到对侧
4. **③ 判定时机** — 若原片讲了「什么时候该停 / 什么时候降级」，务必截到那一帧
5. **❌ 错误示范** — 原片若演示了错误做法，必须单独配图并标注

补图方法：从字幕定位该动作的起止时间，用 `--mode fixed --interval 2~3 --start/--end` 重抽，再逐张挑。

### 图注要写画面内容，不要复述标题

- ❌ `![[阶段3.jpg]]` 上面写「阶段 3：举起胳膊」（与标题重复）
- ✅ `**② 单腿下放——脚后跟轻触地面，骨盆不得前倾**`（描述这一帧在动作序列中的位置和要领）

### 图片文件命名

`<视频短名>-<序号><字母>-<画面内容>.jpg`，例如：

```
deadbug-09a-阶段2双手固定骨盆.jpg
deadbug-09b-阶段2脚跟轻触地面.jpg
deadbug-09d-阶段2半程判定时机.jpg
cervicogenic-11e-眼球追踪画八字.jpg
```

同一动作的序列用同一数字 + 递增字母，便于排序和后续插图。

### 收尾检查

- 笔记中所有 `![[...]]` 均可解析
- `_resource/` 中无因替换而残留的**孤儿图**（被换掉的旧图要删）

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
