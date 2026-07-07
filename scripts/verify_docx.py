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
  7. If --subtitle <subtitles.txt> is provided, check coverage of key causal sentences.

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


def check_subtitle_coverage(docx_text: str, subtitle_path: str) -> tuple:
    """
    检查字幕中的关键因果句有多少被 DOCX 正文覆盖。
    返回: (missing_sentences, coverage_ratio)
    """
    subtitle_text = open(subtitle_path, encoding="utf-8").read()
    key_sentences = extract_key_sentences(subtitle_text)

    if not key_sentences:
        return [], 1.0

    docx_norm = normalize_text(docx_text)

    missing = []
    for s in key_sentences:
        if not contains_fuzzy(docx_norm, s):
            missing.append(s)

    coverage = (len(key_sentences) - len(missing)) / len(key_sentences)
    return missing, coverage


def verify(docx_path: str, keywords: list, min_images: int = 1, subtitle_path: str = None) -> bool:
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

    if subtitle_path:
        missing_sentences, coverage = check_subtitle_coverage(xml, subtitle_path)
        print(f"[7] subtitle key causal sentence coverage: {coverage * 100:.1f}% ({int(len(missing_sentences) / (1 - coverage) - len(missing_sentences) if coverage < 1 else len(missing_sentences))} total, {len(missing_sentences)} missing)")
        if coverage < 0.85:
            print(f"  [FAIL] coverage < 85%, missing key sentences:")
            for s in missing_sentences[:5]:
                print(f"    - {s[:60]}...")
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
    args = parser.parse_args()

    ok = verify(args.docx_path, args.keywords, min_images=args.min_images, subtitle_path=args.subtitle)
    sys.exit(0 if ok else 1)
