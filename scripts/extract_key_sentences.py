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

# 口头禅/非核心话术黑名单（观点分享类视频用，不计入覆盖率）
FILLER_KEYWORDS = [
    "点赞", "收藏", "关注", "三连", "投币", "转发",
    "不吃亏", "有帮助", "谢谢", "感谢", "宝藏", "宝藏up",
    "觉得不错", "记得", "别忘了", "麻烦", "求",
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


def is_filler_phrase(sentence: str) -> bool:
    """
    判断句子是否主要由口头禅/互动话术构成。
    用于观点分享类视频，过滤掉"点赞收藏关注"等非核心话术。
    """
    s = sentence.strip()
    if len(s) < 15:
        return True
    
    filler_hits = sum(1 for kw in FILLER_KEYWORDS if kw in s)
    # 命中 2 个以上黑名单词，且句子较短
    if filler_hits >= 2 and len(s) < 40:
        return True
    # 命中 1 个且句子很短
    if filler_hits >= 1 and len(s) < 25:
        return True
    # 纯互动请求（无实质内容）
    if any(s.startswith(kw) for kw in ["点赞", "收藏", "关注", "谢谢", "求"]):
        return True
    return False


def extract_key_sentences(text: str, skip_filler: bool = False) -> List[str]:
    """
    从文本中提取关键因果句。
    
    Args:
        text: 输入文本
        skip_filler: 是否跳过口头禅/非核心话术（观点分享类视频设为 True）
    """
    sentences = split_sentences(text)
    results = []
    seen = set()
    for s in sentences:
        ok, reason = is_key_sentence(s)
        if ok and s not in seen:
            if skip_filler and is_filler_phrase(s):
                continue
            seen.add(s)
            results.append(s)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="从字幕 TXT 中提取含因果/解释/假设/阈值/代价等语义的关键句"
    )
    parser.add_argument("subtitle", help="字幕 TXT 文件路径")
    parser.add_argument("--output", "-o", default=None, help="输出 JSON 路径（默认与字幕同名 .key.json)")
    parser.add_argument("--skip-filler", action="store_true",
                        help="跳过口头禅/互动话术（观点分享类视频建议开启）")
    args = parser.parse_args()

    subtitle_path = Path(args.subtitle)
    if not subtitle_path.exists():
        print(f"[ERROR] 字幕文件不存在: {subtitle_path}")
        return

    text = subtitle_path.read_text(encoding="utf-8")
    key_sentences = extract_key_sentences(text, skip_filler=args.skip_filler)

    output = {
        "source": str(subtitle_path),
        "total_chars": len(text),
        "key_sentences": key_sentences,
        "skipped_filler": args.skip_filler
    }

    output_path = args.output
    if not output_path:
        output_path = Path(str(subtitle_path) + '.key.json')
    else:
        output_path = Path(output_path)

    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] 共提取 {len(key_sentences)} 条关键句，已保存到: {output_path}")
    if args.skip_filler:
        print("[INFO] 已启用口头禅过滤（--skip-filler）")


if __name__ == "__main__":
    main()
