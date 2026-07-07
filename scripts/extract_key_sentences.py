#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从字幕 TXT 中提取含因果/解释/假设/阈值/代价等语义的关键句。

用法：
    python extract_key_sentences.py <subtitles.txt> [--output key_sentences.json]

输出 JSON 格式：
    {
      "key_sentences": [
        {
          "text": "原文句子",
          "reason": "匹配到的原因：包含'为什么/原因是/假设/如果...那么/阈值/代价/开销/重传'等关键词"
        }
      ]
    }

设计目的：
    生成 DOCX 前，先确认哪些因果解释句必须被保留；
    生成 DOCX 后，用 verify_docx.py --subtitle 检查这些句子是否已覆盖。
"""

import re
import json
import argparse
from pathlib import Path
from typing import List, Dict


# 关键模式：因果、解释、假设、阈值、代价、重传等
CAUSAL_KEYWORDS = [
    "为什么", "原因是", "因为", "所以", "因此", "于是", "从而",
    "假设", "如果", "那么", "假如", "一旦", "要是",
    "阈值", "大于", "小于", "超过", "低于",
    "代价", "开销", "成本", "浪费", "得不偿失",
    "重传", "冲突", "避免", "防止", "解决", "导致", "引起",
    "先", "再", "然后", "之后", "只有", "才", "只要", "就"
]


def split_sentences(text: str) -> List[str]:
    """按中文/英文句号、问号、感叹号、分号、换行分句。"""
    # 先统一换行
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 保留字幕中的时间戳过滤？这里假设输入已是纯文本字幕
    # 按常见分隔符切分
    parts = re.split(r'([。！？；;\n])', text)
    sentences = []
    i = 0
    while i < len(parts):
        s = parts[i]
        if i + 1 < len(parts):
            s += parts[i + 1]  # 把分隔符加回来
        s = s.strip()
        if s:
            sentences.append(s)
        i += 2
    return sentences


def is_key_sentence(sentence: str) -> (bool, str):
    """
    判断一个句子是否是关键解释句，返回 (是否关键, 命中原因)。
    """
    s = sentence.strip()
    if len(s) < 10:
        return False, ""

    matched = [kw for kw in CAUSAL_KEYWORDS if kw in s]
    if not matched:
        return False, ""

    # 必须有解释性结构，避免单纯列举
    has_explanation_structure = (
        "为什么" in s or "原因是" in s or "因为" in s or "所以" in s
        or "假设" in s or "如果" in s or "那么" in s or "假如" in s
        or "一旦" in s or "只有" in s or "才" in s or "就会" in s
        or "就不会" in s or "导致" in s or "引起" in s or "避免" in s
        or "防止" in s or "解决" in s or "为了" in s or "之所以" in s
    )
    if not has_explanation_structure:
        return False, ""

    return True, f"命中关键词: {', '.join(matched[:3])}"


def extract_key_sentences(text: str) -> List[str]:
    sentences = split_sentences(text)
    results = []
    seen = set()
    for s in sentences:
        ok, reason = is_key_sentence(s)
        if ok and s not in seen:
            seen.add(s)
            results.append(s)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="从字幕 TXT 中提取含因果/解释/假设/阈值/代价等语义的关键句"
    )
    parser.add_argument("subtitle", help="字幕 TXT 文件路径")
    parser.add_argument("--output", "-o", default=None, help="输出 JSON 路径（默认与字幕同名 .key.json)")
    args = parser.parse_args()

    subtitle_path = Path(args.subtitle)
    if not subtitle_path.exists():
        print(f"[ERROR] 字幕文件不存在: {subtitle_path}")
        return

    text = subtitle_path.read_text(encoding="utf-8")
    key_sentences = extract_key_sentences(text)

    output = {
        "source": str(subtitle_path),
        "total_chars": len(text),
        "key_sentences": key_sentences
    }

    output_path = args.output
    if not output_path:
        output_path = Path(str(subtitle_path) + '.key.json')
    else:
        output_path = Path(output_path)

    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] 共提取 {len(key_sentences)} 条关键句，已保存到: {output_path}")


if __name__ == "__main__":
    main()
