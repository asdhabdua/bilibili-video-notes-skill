#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vision 打分结果推荐脚本

功能：
  1. 读取 vision_scores.json，按 score 排序
  2. 输出 Top N 推荐帧（含分数、主题、完整性）
  3. 可选：自动复制推荐帧到 final/ 目录

用法：
    # 只看推荐列表
    python scripts/recommend_frames.py \
        --scores ./work/<内容名>/vision_scores_p01.json \
        --top 10

    # 推荐并自动复制到 final/
    python scripts/recommend_frames.py \
        --scores ./work/<内容名>/vision_scores_p01.json \
        --frames ./frames/p01/selected \
        --output ./frames/p01/final \
        --top 10

设计目的：
  替代"人工看全部 30 帧再选"的低效模式，
  先让 AI 打分排序，人工只看 Top 10 做最终确认。
"""

import argparse
import json
import os
import shutil
import sys


def load_scores(scores_path: str) -> dict:
    """加载 vision_scores.json。"""
    with open(scores_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def recommend(scores: dict, top_n: int = 10, min_score: int = 5) -> list:
    """
    按 score 排序，返回 Top N 推荐帧。
    过滤掉失败帧和低分帧。
    
    返回: [(frame_name, score_data), ...] 按 score 降序
    """
    valid = []
    for name, data in scores.items():
        if data.get('error'):
            continue
        score = data.get('score', 0)
        if score < min_score:
            continue
        valid.append((name, data))
    
    # 按 score 降序，分数相同按名字排序
    valid.sort(key=lambda x: (-x[1]['score'], x[0]))
    return valid[:top_n]


def copy_frames(recommended: list, frames_dir: str, output_dir: str):
    """将推荐帧复制到 final/ 目录。"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 清理旧文件
    for f in os.listdir(output_dir):
        if f.endswith('.jpg'):
            os.remove(os.path.join(output_dir, f))
    
    copied = 0
    for name, _ in recommended:
        src = os.path.join(frames_dir, name)
        if not os.path.exists(src):
            # 尝试加前缀匹配
            candidates = [f for f in os.listdir(frames_dir) if f.endswith(name) or name in f]
            if candidates:
                src = os.path.join(frames_dir, candidates[0])
            else:
                print(f"  [WARN] 找不到源文件: {name}")
                continue
        
        dst = os.path.join(output_dir, f"frame_{copied+1:04d}.jpg")
        shutil.copy2(src, dst)
        copied += 1
    
    print(f"\n[INFO] 已复制 {copied} 帧到 {output_dir}")
    return copied


def main():
    parser = argparse.ArgumentParser(description='Vision 打分结果推荐')
    parser.add_argument('--scores', '-s', required=True, help='vision_scores.json 路径')
    parser.add_argument('--frames', '-f', default=None, help='selected 帧目录路径（用于复制）')
    parser.add_argument('--output', '-o', default=None, help='final 输出目录路径')
    parser.add_argument('--top', '-n', type=int, default=10, help='推荐数量（默认 10）')
    parser.add_argument('--min-score', type=int, default=5, help='最低分数门槛（默认 5）')
    parser.add_argument('--auto-copy', action='store_true', help='自动复制到 output 目录')
    args = parser.parse_args()

    if not os.path.exists(args.scores):
        print(f"[ERROR] scores 文件不存在: {args.scores}")
        sys.exit(1)

    scores = load_scores(args.scores)
    total = len(scores)
    success = sum(1 for d in scores.values() if not d.get('error'))
    
    print(f"=== Vision Scores Summary ===")
    print(f"Total frames scored: {total}")
    print(f"Successful: {success} | Failed: {total - success}")
    print()

    recommended = recommend(scores, top_n=args.top, min_score=args.min_score)
    
    if not recommended:
        print("[WARN] 没有符合条件的帧（请检查 --min-score 是否过高）")
        sys.exit(1)

    print(f"=== Top {len(recommended)} Recommended Frames ===\n")
    for i, (name, data) in enumerate(recommended, 1):
        score = data.get('score', 0)
        theme = data.get('theme', 'N/A')
        complete = "✓" if data.get('complete', True) else "✗"
        print(f"{i:2d}. {name}")
        print(f"    Score: {score}/10 | Complete: {complete}")
        print(f"    Theme: {theme[:60]}{'...' if len(theme) > 60 else ''}")
        print()

    # 如果指定了 frames 和 output，自动复制
    if args.auto_copy or (args.frames and args.output):
        if not args.frames:
            print("[ERROR] --auto-copy 需要同时指定 --frames")
            sys.exit(1)
        if not args.output:
            print("[ERROR] --auto-copy 需要同时指定 --output")
            sys.exit(1)
        if not os.path.exists(args.frames):
            print(f"[ERROR] frames 目录不存在: {args.frames}")
            sys.exit(1)
        
        copy_frames(recommended, args.frames, args.output)


if __name__ == '__main__':
    main()
