# Vision 打分 + DOCX 生成详细指南

## Vision 打分策略

### 两轮 vision 方法（推荐，不丢内容）

**第一轮：按知识点分组**

```
Classify N lecture video frames by KNOWLEDGE POINT (not visual similarity).

CRITICAL RULE: Two frames that look visually similar but teach DIFFERENT concepts
should be in DIFFERENT groups. For example, if one frame defines "实体+协议" and
another defines "接口+服务", they are DIFFERENT knowledge points even if the
diagram layout is identical. Keep BOTH.

For each frame, assign a knowledge point label. Then for each knowledge point,
score each frame 1-10 for completeness.
```

**第二轮：每个知识点选最完整版**

```
For each knowledge point, pick the frame with highest completeness score.
Standard: more labels, arrows, annotations, definitions = more complete.
```

### 帧数 > 15 时：并行分批

用 delegate_task 分批打分，每批 10-15 帧。不要一次性打太多（会超时或 rate limit）。

### 打分 Prompt（两轮方法）

**第一轮 prompt（按知识点分组）：**

```
Classify N lecture video frames by KNOWLEDGE POINT (not visual similarity).

CRITICAL RULE: Two frames that look visually similar but teach DIFFERENT concepts
should be in DIFFERENT groups. Keep BOTH.

For each knowledge point: name, frames, best frame, score, description.
```

**第二轮 prompt（每组选最完整版）：**

```
For each knowledge point, pick the frame with highest completeness score.
Standard: more labels, arrows, annotations, definitions = more complete.
```

**为什么不按视觉相似分组：** 视觉相似的帧可能教完全不同的内容（如实体+协议 vs 接口+服务），按视觉分组会丢内容。

### 打分结果处理

1. 收集所有得分 ≥ 8 的帧
2. 检查是否有视觉相似的帧重复入选
3. 只保留每组最完整的一张

## DOCX 生成

### 核心原则（用户明确要求）

- **不是照搬字幕**，是"融会贯通"——字幕提供内容，截图提供视觉
- 以"顶级学者"标准追求**知识的完整性**
- 用户要的是"什么都能查到的电子词典"，不是大致概括
- 不要带时间戳

### python-docx 模板

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Microsoft YaHei'
style.font.size = Pt(11)

def add_image(fn, w=5.5, caption=''):
    p = os.path.join(FRAME_DIR, fn)
    if os.path.exists(p):
        par = doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.add_run().add_picture(p, width=Inches(w))
        if caption:
            c = doc.add_paragraph()
            c.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = c.add_run(caption)
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(128,128,128)
            r.italic = True

def h(t, l=1): doc.add_heading(t, level=l)
def p(t, b=False):
    par = doc.add_paragraph()
    r = par.add_run(t); r.bold = b; return par
def tbl(hdrs, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(hdrs))
    t.style = 'Light Grid Accent 1'
    for i,h_ in enumerate(hdrs): t.rows[0].cells[i].text = h_
    for r,row in enumerate(rows):
        for c,v in enumerate(row): t.rows[r+1].cells[c].text = v
```

### 内容组织（质量标杆：1.2.3_TCP-IP模型_智能版.docx）

每个知识点按以下顺序：
1. **概念定义**（加粗关键术语）
2. **相关截图**（嵌入 DOCX，加图注说明截图内容）
3. **对比表格**（用 tbl 函数，如 OSI vs TCP/IP 对照）
4. **公式**（加粗大字号 Pt 12-13）
5. **例题**（如有，包含完整解题过程）
6. **做题要点**（每个知识点末尾总结考试关键）
7. **解释 WHY**（不只是"是什么"，还要解释"为什么这样设计"）
8. **助记口诀**（老师教的记忆技巧一定要保留）

### 文件命名

`<章节号>_<标题>_智能版.docx`，**不覆盖已有文件**（用户要求）。

## 后处理清理（必须做）

- 删除视频 MP4（大文件，~30-50MB）
- 删除字幕 JSON（保留 TXT）
- 删除临时 gen_docx.py
- 删除 __pycache__
- 保留：字幕 TXT、帧截图（selected/）、脚本
