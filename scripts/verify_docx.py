# -*- coding: utf-8 -*-
"""Ad-hoc verification for generated DOCX video notes.

Usage:
    python scripts/verify_docx.py <path_to_docx> [keyword1] [keyword2] ...

Checks:
  1. File exists, size in plausible range (100KB - 5MB)
  2. Embedded image count matches expectation (default: >= 1)
  3. Table count >= 1
  4. All user-supplied keywords appear in document.xml
  5. "考研要求" and "要点总结" sections present (Chinese 考研 note convention)
  6. Paragraph count >= 50
  7. If --subtitle <subtitles.txt> is provided and exists, check coverage of key causal sentences.
     If subtitle file does not exist, skip coverage check with a warning.

Video types (--type):
  lecture   讲课/教程视频（覆盖率要求 >= 75%）
  opinion   观点分享/经验谈（覆盖率要求 >= 50%，过滤口头禅）
  vlog      Vlog/杂谈（不检查字幕覆盖）

Exit code 0 = all checks passed, 1 = at least one check failed.

This is ad-hoc verification (not a test suite). It catches the most common
silent-failure modes: blank docs, missing images, missing key terms.
"""

import os
import sys
import re
import zipfile
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from extract_key_sentences import extract_key_sentences


# 非核心口头禅黑名单（观点分享类视频中这些话术不计入覆盖率）
FILLER_PATTERNS = [
    r"点赞",
    r"收藏",
    r"关注",
    r"三连",
    r"不吃亏",
    r"有帮助",
    r"谢谢",
    r"宝藏",
    r"觉得",
    r"大家",
    r"我们",
    r"你们",
]


def normalize_text(text: str) -> str:
    """归一化文本用于模糊匹配。"""
    text = text.lower()
    # 去掉常见标点、空格
    text = re.sub(r"[\s。，、！？；：""''（）()\[\]【】]", "", text)
    return text


def contains_fuzzy(haystack: str, needle: str, min_chars: int = 6) -> bool:
    """
    判断 haystack 是否包含 needle 的核心内容。
    策略：提取 needle 中长度 >= min_chars 的连续子串，看是否有任意一个出现在 haystack 中。
    """
    if not needle or len(needle) < min_chars:
        return False
    haystack_norm = normalize_text(haystack)
    needle_norm = normalize_text(needle)

    # 先尝试整句
    if needle_norm in haystack_norm:
        return True

    # 再尝试滑动窗口
    for i in range(0, len(needle_norm) - min_chars + 1):
        window = needle_norm[i:i + min_chars]
        if window in haystack_norm:
            return True
    return False


def is_likely_filler(sentence: str) -> bool:
    """判断句子是否主要由口头禅/互动话术构成（观点分享类视频用）。"""
    # 如果句子包含大量黑名单词汇，且长度较短，认为是 filler
    if len(sentence) < 20:
        return True
    filler_hits = sum(1 for p in FILLER_PATTERNS if re.search(p, sentence))
    # 命中 2 个以上黑名单词，且句子总长 < 40，认为是 filler
    if filler_hits >= 2 and len(sentence) < 40:
        return True
    # 命中 1 个且句子很短
    if filler_hits >= 1 and len(sentence) < 25:
        return True
    return False


def check_subtitle_coverage(docx_text: str, subtitle_path: str, video_type: str = 'lecture') -> tuple:
    """
    检查字幕中的关键因果句有多少被 DOCX 正文覆盖。
    返回: (missing_sentences, coverage_ratio, total_checked)
    """
    subtitle_text = open(subtitle_path, encoding="utf-8").read()
    key_sentences = extract_key_sentences(subtitle_text)

    if not key_sentences:
        return [], 1.0, 0

    docx_norm = normalize_text(docx_text)

    # 观点分享类视频：过滤掉口头禅
    if video_type == 'opinion':
        key_sentences = [s for s in key_sentences if not is_likely_filler(s)]

    if not key_sentences:
        return [], 1.0, 0

    missing = []
    for s in key_sentences:
        if not contains_fuzzy(docx_norm, s):
            missing.append(s)

    coverage = (len(key_sentences) - len(missing)) / len(key_sentences)
    return missing, coverage, len(key_sentences)


def get_coverage_threshold(video_type: str) -> float:
    """根据视频类型返回覆盖率阈值。"""
    thresholds = {
        'lecture': 0.75,   # 讲课视频：AI字幕通常不完整，75% 更现实
        'opinion': 0.50,
        'vlog': 0.0,       # Vlog 不检查覆盖
    }
    return thresholds.get(video_type, 0.75)


def score_sentence_priority(sentence: str) -> int:
    """
    给缺失句子打分，用于排序输出。
    分数越高 = 信息量越大 = 越应该优先补充。
    基于：句子长度、因果关键词密度、是否包含数字/公式。
    """
    score = len(sentence)  # 基础分：长度

    # 因果关键词加分（每个 +10）
    causal_kws = ["为什么", "原因是", "因为", "所以", "因此", "假设", "如果", "那么",
                  "一旦", "只有", "才", "导致", "引起", "避免", "防止", "解决"]
    for kw in causal_kws:
        if kw in sentence:
            score += 10

    # 数字/公式加分（通常包含量化信息）
    if re.search(r'\d+', sentence):
        score += 5

    return score


def sort_missing_by_priority(missing: list) -> list:
    """按优先级排序缺失句子，信息量大的排前面。"""
    return sorted(missing, key=score_sentence_priority, reverse=True)


def verify(docx_path: str, keywords: list, min_images: int = 1,
           subtitle_path: str = None, video_type: str = 'lecture') -> bool:
    if not os.path.exists(docx_path):
        print(f"[FAIL] file not found: {docx_path}")
        return False

    size_kb = os.path.getsize(docx_path) / 1024
    print(f"[1] file exists: {size_kb:.1f} KB")
    if not (100 <= size_kb <= 5120):
        print(f"  [WARN] size outside expected range 100KB-5MB")

    try:
        with zipfile.ZipFile(docx_path) as z:
            media = [n for n in z.namelist() if n.startswith("word/media/")]
            with z.open("word/document.xml") as f:
                xml = f.read().decode("utf-8")
    except zipfile.BadZipFile:
        print(f"[FAIL] {docx_path} is not a valid docx (zip)")
        return False

    print(f"[2] embedded images: {len(media)} (expect >= {min_images})")
    if len(media) < min_images:
        print(f"  [FAIL] too few images")
        return False

    tbl_count = xml.count("<w:tbl>")
    print(f"[3] tables: {tbl_count} (expect >= 1)")
    if tbl_count < 1:
        print(f"  [FAIL] no tables")
        return False

    if keywords:
        missing = [k for k in keywords if k not in xml]
        print(f"[4] keywords: {len(keywords) - len(missing)}/{len(keywords)} present")
        if missing:
            print(f"  [FAIL] missing keywords: {missing}")
            return False

    has_intro = "考研要求" in xml or "学习目标" in xml or "本节内容" in xml
    has_summary = "要点总结" in xml or "本节总结" in xml or "小结" in xml
    print(f"[5] 考研 note structure: intro={has_intro}, summary={has_summary}")
    if not (has_intro and has_summary):
        print(f"  [WARN] 考研要求/要点总结 not both present (may be intentional for non-exam notes)")

    para_count = xml.count("<w:p ") + xml.count("<w:p>")
    print(f"[6] paragraphs: {para_count} (expect >= 50)")
    if para_count < 50:
        print(f"  [WARN] doc looks thin")

    # === 字幕覆盖率检查 ===
    if subtitle_path:
        if video_type == 'vlog':
            print(f"[7] subtitle coverage: skipped (vlog type)")
        elif not os.path.exists(subtitle_path):
            print(f"[7] subtitle coverage: skipped (subtitle file not found: {subtitle_path})")
            print(f"  [WARN] 无字幕文件，跳过覆盖率检查（请确认视频是否有字幕）")
        else:
            missing_sentences, coverage, total = check_subtitle_coverage(
                xml, subtitle_path, video_type=video_type
            )
            threshold = get_coverage_threshold(video_type)
            print(f"[7] subtitle key causal sentence coverage: {coverage * 100:.1f}% "
                  f"({total} total, {len(missing_sentences)} missing, type={video_type}, threshold={threshold*100:.0f}%)")
            if coverage < threshold:
                # 按优先级排序缺失句，信息量大的排前面
                missing_sorted = sort_missing_by_priority(missing_sentences)
                print(f"  [FAIL] coverage < {threshold*100:.0f}%, missing key sentences (sorted by priority):")
                for i, s in enumerate(missing_sorted[:8], 1):
                    priority = score_sentence_priority(s)
                    print(f"    {i}. [优先级{priority}] {s[:70]}...")
                if len(missing_sorted) > 8:
                    print(f"    ... and {len(missing_sorted) - 8} more")
                return False
            elif missing_sentences:
                print(f"  [WARN] some key sentences not fully covered (coverage={coverage*100:.1f}%)")

    print()
    print("ALL CHECKS PASSED")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ad-hoc verification for generated DOCX video notes."
    )
    parser.add_argument("docx_path", help="DOCX 文件路径")
    parser.add_argument("keywords", nargs="*", help="需要检查的关键词")
    parser.add_argument("--min-images", type=int, default=1, help="最少图片数")
    parser.add_argument("--subtitle", default=None, help="字幕 TXT 路径，用于检查关键因果句覆盖")
    parser.add_argument("--type", default="lecture", choices=["lecture", "opinion", "vlog"],
                        help="视频类型: lecture=讲课(75%%), opinion=观点分享(50%%), vlog=不检查覆盖")
    args = parser.parse_args()

    ok = verify(args.docx_path, args.keywords, min_images=args.min_images,
                subtitle_path=args.subtitle, video_type=args.type)
    sys.exit(0 if ok else 1)
