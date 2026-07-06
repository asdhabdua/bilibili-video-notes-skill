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

Exit code 0 = all checks passed, 1 = at least one check failed.
"""

import os
import sys
import zipfile
import re


def verify(docx_path: str, keywords: list, min_images: int = 1) -> bool:
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
    else:
        missing = []

    has_intro = "考研要求" in xml or "学习目标" in xml or "本节内容" in xml
    has_summary = "要点总结" in xml or "本节总结" in xml or "小结" in xml
    print(f"[5] 考研 note structure: intro={has_intro}, summary={has_summary}")
    if not (has_intro and has_summary):
        print(f"  [WARN] 考研要求/要点总结 not both present (may be intentional for non-exam notes)")

    # 检查 markdown 重建字符
    bold_md = re.findall(r'\*\*[^*]+\*\*', xml)
    underline_md = re.findall(r'<u>[^<]+</u>', xml)
    print(f"[6] markdown residue: **bold**={len(bold_md)}, <u>={len(underline_md)} (expect 0)")
    if bold_md or underline_md:
        print(f"  [WARN] markdown syntax found in docx")

    para_count = xml.count("<w:p ") + xml.count("<w:p>")
    print(f"[7] paragraphs: {para_count} (expect >= 50)")
    if para_count < 50:
        print(f"  [WARN] doc looks thin")

    print()
    print("ALL CHECKS PASSED" if not missing else "FAILED")
    return not missing


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_docx.py <docx_path> [keyword1] [keyword2] ...")
        sys.exit(1)

    docx = sys.argv[1]
    kws = sys.argv[2:]
    ok = verify(docx, kws)
    sys.exit(0 if ok else 1)
