#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOCX JSON 配置骨架生成器

功能：
  1. 读取 vision_extract.json（AI 对每帧的视觉提取结果）
  2. 读取字幕关键句（可选）
  3. 按 theme 自动聚类 → 生成 h1/h2 结构
  4. 自动填入 concepts、reasoning、tables、frames
  5. 输出 config_draft.json（可直接给 gen_docx_dynamic.py 使用）

用法：
    python scripts/generate_config_draft.py \
        --vision ./work/<内容名>/vision_extract_p01.json \
        --key-sentences ./work/<内容名>/<BV>_p01_subtitles.txt.key.json \
        --title "1.1 计算机网络的概念" \
        --source "王道考研计算机网络，B站 BVxxx P1" \
        --frames-dir ./frames/p01/final \
        --output ./work/<内容名>/config_p01_draft.json

设计目的：
  替代从零手写 SECTIONS 的低效模式。
  脚本生成骨架后，人工只需：调整顺序、补充细节、删减冗余。
  预计节省 50%+ 的 DOCX 编写时间。
"""

import argparse
import json
import os
import re
from difflib import SequenceMatcher


def text_similarity(a: str, b: str) -> float:
    """计算两段文本的相似度 (0~1)。"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def extract_keywords(theme: str) -> set:
    """从 theme 中提取关键词（过滤常见虚词）。"""
    # 去掉常见虚词和标点
    stopwords = {'的', '了', '和', '与', '在', '是', '对', '从', '等', '及',
                 '：', ':', '、', '/', '，', ',', '（', '）', '(', ')', '：', ':'}
    words = re.split(r'[\s\/：:；,.，、（）()]+', theme)
    return {w for w in words if len(w) >= 2 and w not in stopwords}


def cluster_frames(frames_data: dict, similarity_threshold: float = 0.35) -> list:
    """
    按 theme 相似度对帧进行聚类。
    返回: [(group_title, [frame_ids]), ...]
    """
    # 按 score 降序排列
    sorted_frames = sorted(frames_data.items(), key=lambda x: x[1].get('score', 0), reverse=True)
    
    groups = []  # [(title, [frame_ids], combined_data), ...]
    
    for frame_id, data in sorted_frames:
        theme = data.get('theme', '')
        if not theme:
            continue
        
        # 尝试归入现有组
        placed = False
        for i, (g_title, g_ids, g_data) in enumerate(groups):
            # 用关键词重叠 + 文本相似度判断
            kw_overlap = len(extract_keywords(theme) & extract_keywords(g_title))
            sim = text_similarity(theme, g_title)
            
            # 如果关键词重叠 >= 2 或相似度 >= threshold，归入该组
            if kw_overlap >= 2 or sim >= similarity_threshold:
                groups[i] = (g_title, g_ids + [frame_id], g_data + [data])
                placed = True
                break
        
        if not placed:
            groups.append((theme, [frame_id], [data]))
    
    return groups


def build_sections(groups: list, key_sentences: list = None) -> list:
    """
    根据聚类结果生成 SECTIONS 列表。
    
    每个组生成：
      h1/h2 标题
      body（concepts）
      why（reasoning）
      table（如果有）
      img（帧）
    """
    sections = []
    used_key_sentences = set()
    
    for g_title, g_ids, g_data in groups:
        # 标题
        sections.append(['h1', g_title])
        
        # 合并所有 concepts
        all_concepts = []
        all_reasonings = []
        all_tables = []
        
        for data in g_data:
            concepts = data.get('concepts', [])
            reasoning = data.get('reasoning', '')
            tables = data.get('tables', [])
            
            for c in concepts:
                if c and c not in all_concepts:
                    all_concepts.append(c)
            
            if reasoning and reasoning != 'None' and reasoning not in all_reasonings:
                all_reasonings.append(reasoning)
            
            for t in tables:
                if t not in all_tables:
                    all_tables.append(t)
        
        # 填入 concepts 作为 body
        for c in all_concepts[:3]:  # 每个组最多 3 个 concept，避免太长
            sections.append(['body', c])
        
        # 填入 reasoning 作为 why
        for r in all_reasonings[:1]:  # 每个组最多 1 个 reasoning
            sections.append(['why', r])
        
        # 填入表格
        for t in all_tables[:1]:  # 每个组最多 1 个表格
            headers = t.get('headers', [])
            rows = t.get('rows', [])
            if headers and rows:
                sections.append(['table', headers, rows])
        
        # 尝试匹配字幕关键句
        if key_sentences:
            matched = []
            for ks in key_sentences:
                # 简单匹配：如果关键句中的关键词与主题关键词有重叠
                ks_keywords = extract_keywords(ks)
                theme_keywords = extract_keywords(g_title)
                if len(ks_keywords & theme_keywords) >= 1 and ks not in used_key_sentences:
                    matched.append(ks)
                    used_key_sentences.add(ks)
            
            for m in matched[:2]:  # 每个组最多 2 条字幕关键句
                # 去掉时间戳前缀
                clean = re.sub(r'^\[\d+m\d+s\]\s*', '', m)
                if clean:
                    sections.append(['body', f'（字幕补充）{clean}'])
        
        # 图片（取该组最高分帧）
        best_frame = g_ids[0] if g_ids else None
        if best_frame:
            frame_num = re.search(r'(\d+)', best_frame)
            if frame_num:
                sections.append(['img', frame_num.group(1).zfill(4), g_title[:30]])
    
    return sections


def build_frames_dict(groups: list) -> dict:
    """生成 FRAMES 字典: {frame_id: caption}。"""
    frames = {}
    for g_title, g_ids, g_data in groups:
        for frame_id in g_ids[:1]:  # 每组只取最高分的帧
            frame_num = re.search(r'(\d+)', frame_id)
            if frame_num:
                key = frame_num.group(1).zfill(4)
                if key not in frames:
                    frames[key] = g_title[:40]
    return frames


def build_summary(sections: list) -> list:
    """从 sections 中提取总结要点（取每个 h1 后面的第一条 body）。"""
    summary = []
    for i, item in enumerate(sections):
        if item[0] == 'h1' and i + 1 < len(sections):
            next_item = sections[i + 1]
            if next_item[0] == 'body':
                text = next_item[1]
                if len(text) > 10 and len(text) < 80:
                    summary.append(text)
    return summary[:5]  # 最多 5 条


def main():
    parser = argparse.ArgumentParser(description='DOCX JSON 配置骨架生成器')
    parser.add_argument('--vision', '-v', required=True, help='vision_extract.json 路径')
    parser.add_argument('--key-sentences', '-k', default=None, help='字幕关键句 JSON 路径（可选）')
    parser.add_argument('--title', '-t', required=True, help='文档标题')
    parser.add_argument('--source', '-s', required=True, help='视频来源说明')
    parser.add_argument('--frames-dir', '-f', required=True, help='final 帧目录路径')
    parser.add_argument('--output', '-o', required=True, help='输出 JSON 路径')
    parser.add_argument('--similarity', type=float, default=0.35, help='theme 聚类相似度阈值 (默认 0.35)')
    args = parser.parse_args()

    # 读取 vision_extract.json
    with open(args.vision, 'r', encoding='utf-8') as f:
        vision_data = json.load(f)
    
    print(f"[INFO] 加载 {len(vision_data)} 帧的视觉提取结果")
    
    # 读取字幕关键句（可选）
    key_sentences = None
    if args.key_sentences and os.path.exists(args.key_sentences):
        with open(args.key_sentences, 'r', encoding='utf-8') as f:
            ks_data = json.load(f)
        key_sentences = ks_data.get('key_sentences', [])
        print(f"[INFO] 加载 {len(key_sentences)} 条字幕关键句")
    
    # 聚类
    groups = cluster_frames(vision_data, similarity_threshold=args.similarity)
    print(f"[INFO] 聚类为 {len(groups)} 个主题组")
    for g_title, g_ids, _ in groups:
        print(f"  - {g_title} ({len(g_ids)} 帧)")
    
    # 生成 SECTIONS
    sections = build_sections(groups, key_sentences)
    print(f"[INFO] 生成 {len(sections)} 个内容块")
    
    # 生成 FRAMES 字典
    frames_dict = build_frames_dict(groups)
    
    # 生成 SUMMARY
    summary = build_summary(sections)
    
    # 构建完整配置
    config = {
        'TITLE': args.title,
        'SOURCE': args.source,
        'OUTPUT_PATH': args.output.replace('_draft.json', '.docx').replace('config_', ''),
        'FRAMES_DIR': args.frames_dir,
        'FRAMES': frames_dict,
        'SUMMARY': summary,
        'SECTIONS': sections
    }
    
    # 保存
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n[INFO] 骨架配置已保存到: {args.output}")
    print(f"[INFO] 包含 {len(sections)} 个内容块, {len(frames_dict)} 张图片, {len(summary)} 条总结")
    print(f"\n[下一步] 人工润色:")
    print(f"  1. 调整 SECTIONS 顺序和内容")
    print(f"  2. 补充删减细节")
    print(f"  3. 运行: python templates/gen_docx_dynamic.py --config {args.output}")


if __name__ == '__main__':
    main()
