"""
智能帧筛选工具
流程：OCR预筛 → 哈希去重 → 保留每组内容最丰富的帧
输出：筛选后的帧目录（供 vision 打分）

用法：
  python smart_select.py <frames_dir> [--ocr-threshold 20] [--hash-threshold 10] [--output-dir <path>]

示例：
  python smart_select.py "D:/hermes test/video summary/fixed"
"""

import argparse
import os
import sys
import glob
import shutil
from collections import defaultdict


def get_image_hash(img_path: str):
    """计算图片的感知哈希（pHash）"""
    import imagehash
    from PIL import Image
    try:
        img = Image.open(img_path)
        return imagehash.phash(img)
    except Exception as e:
        print(f"  [warn] Hash failed for {os.path.basename(img_path)}: {e}")
        return None


def get_ocr_text_count(img_path: str, ocr_engine) -> int:
    """OCR 识别，返回检测到的文字数量（字符数）"""
    try:
        result = ocr_engine(img_path)
        if result and result[0]:
            # result[0] 是列表，每项是 [bbox, text, confidence]
            total = sum(len(item[1]) for item in result[0])
            return total
        return 0
    except Exception as e:
        print(f"  [warn] OCR failed for {os.path.basename(img_path)}: {e}")
        return 0


def ocr_text_similarity(text1: str, text2: str) -> float:
    """计算两段 OCR 文本的相似度 (0~1)"""
    from difflib import SequenceMatcher
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()


def smart_select(frames_dir: str, ocr_threshold: int = 20, hash_threshold: int = 10,
                 text_threshold: float = 0.7, skip_clustering: bool = False,
                 output_dir: str = None) -> list:
    """
    智能帧筛选主流程
    1. OCR 预筛：去掉文字量 < ocr_threshold 的帧（空白/老师面部）
    2. 哈希去重：hamming distance < hash_threshold 的帧归为一组
    3. 组内 OCR 文本比对：文字相似度 < text_threshold 的拆成独立帧
    4. 每组保留 OCR 文字量最多的帧
    """

    # Step 0: 收集所有帧
    frames = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
    if not frames:
        print("[error] No .jpg files found")
        return []
    print(f"[input] {len(frames)} frames in {frames_dir}")

    # Step 1: OCR 预筛（同时保存文本用于后续比对）
    print(f"\n[step 1] OCR 预筛 (threshold={ocr_threshold} chars)...")
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()

    ocr_scores = {}
    ocr_texts = {}
    for i, f in enumerate(frames):
        try:
            result = ocr(f)
            if result and result[0]:
                text = ' '.join([item[1] for item in result[0]])
                score = len(text)
            else:
                text = ''
                score = 0
        except Exception as e:
            text = ''
            score = 0
            print(f"  [warn] OCR failed for {os.path.basename(f)}: {e}")
        ocr_scores[f] = score
        ocr_texts[f] = text
        if (i + 1) % 20 == 0:
            print(f"  OCR progress: {i+1}/{len(frames)}")

    # 统计
    text_frames = {f: s for f, s in ocr_scores.items() if s >= ocr_threshold}
    blank_frames = {f: s for f, s in ocr_scores.items() if s < ocr_threshold}
    print(f"  有文字的帧: {len(text_frames)}")
    print(f"  空白/面部帧: {len(blank_frames)} (筛除)")

    if not text_frames:
        print("[warn] 所有帧文字量都低于阈值，降低阈值重试...")
        text_frames = {f: s for f, s in ocr_scores.items() if s >= ocr_threshold // 2}
        print(f"  降低阈值后: {len(text_frames)} 帧")

    # Step 2: 哈希去重
    print(f"\n[step 2] 哈希去重 (hamming distance < {hash_threshold})...")
    hashes = {}
    for f in text_frames:
        h = get_image_hash(f)
        if h is not None:
            hashes[f] = h

    # 聚类：hamming distance < threshold 的帧归为一组
    groups = []
    used = set()
    frames_list = list(hashes.keys())

    for f in frames_list:
        if f in used:
            continue
        group = [f]
        used.add(f)
        for other in frames_list:
            if other in used:
                continue
            if hashes[f] - hashes[other] < hash_threshold:
                group.append(other)
                used.add(other)
        groups.append(group)

    print(f"  去重后: {len(groups)} 组 (从 {len(text_frames)} 帧)")

    # Step 3: 组内 OCR 文本比对（相似度 < text_threshold 的拆开）
    print(f"\n[step 3] 组内文本比对 (similarity < {text_threshold} 则拆分)...")
    refined_groups = []
    split_count = 0
    for group in groups:
        if len(group) == 1:
            refined_groups.append(group)
            continue
        # 以第一帧为基准，逐个比对文本
        subgroups = [[group[0]]]
        for f in group[1:]:
            placed = False
            for sg in subgroups:
                # 和子组的代表帧比对
                sim = ocr_text_similarity(ocr_texts.get(sg[0], ''), ocr_texts.get(f, ''))
                if sim >= text_threshold:
                    sg.append(f)
                    placed = True
                    break
            if not placed:
                subgroups.append([f])
                split_count += 1
        refined_groups.extend(subgroups)

    if split_count > 0:
        print(f"  文本差异拆分: {split_count} 帧被拆出独立成组")
    print(f"  最终: {len(refined_groups)} 组")

    if skip_clustering:
        # 跳过知识点聚类，保留所有去重后的帧（用于vision二次筛选）
        print(f"\n[step 4-5] 跳过知识点聚类 (--skip-clustering)")
        selected = [g[0] for g in refined_groups]
    else:
        # Step 4: 内容聚类（按知识点分组，每个知识点只保留最完整的一帧）
        print(f"\n[step 4] 内容聚类 (text_similarity >= {text_threshold} 归为同一知识点)...")
        content_clusters = []
        used_in_cluster = set()
        sorted_frames = sorted(refined_groups, key=lambda g: -ocr_scores.get(g[0], 0))

        for group in sorted_frames:
            rep = group[0]
            if rep in used_in_cluster:
                continue
            cluster = [rep]
            used_in_cluster.add(rep)
            for other_group in refined_groups:
                other_rep = other_group[0]
                if other_rep in used_in_cluster:
                    continue
                sim = ocr_text_similarity(ocr_texts.get(rep, ''), ocr_texts.get(other_rep, ''))
                if sim >= text_threshold:
                    cluster.append(other_rep)
                    used_in_cluster.add(other_rep)
            content_clusters.append(cluster)

        print(f"  知识点聚类: {len(content_clusters)} 个")

        # Step 5: 每个知识点保留文字量最多的一帧
        print(f"\n[step 5] 每个知识点选最完整的一帧...")
        selected = []
        for cluster in content_clusters:
            best = max(cluster, key=lambda f: ocr_scores.get(f, 0))
            selected.append(best)
            others = [f for f in cluster if f != best]
            if others:
                print(f"  保留 {os.path.basename(best)} ({ocr_scores[best]}字), 丢弃 {len(others)} 个不完整版")

    selected.sort(key=lambda f: frames.index(f))  # 按时间顺序排列
    print(f"  最终选出: {len(selected)} 帧")

    # Step 4: 输出
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for f in glob.glob(os.path.join(output_dir, "*.jpg")):
            os.remove(f)
        for i, f in enumerate(selected):
            dst = os.path.join(output_dir, f"frame_{i+1:04d}.jpg")
            shutil.copy2(f, dst)
        print(f"\n[output] {len(selected)} frames -> {output_dir}")

    # 打印摘要
    if skip_clustering:
        print(f"\n[summary] {len(frames)} -> {len(text_frames)} (OCR) -> {len(groups)} (哈希去重) -> {len(refined_groups)} (文本拆分) -> {len(selected)} (最终)")
    else:
        print(f"\n[summary] {len(frames)} -> {len(text_frames)} (OCR) -> {len(groups)} (哈希去重) -> {len(refined_groups)} (文本拆分) -> {len(content_clusters)} (知识点聚类) -> {len(selected)} (最终)")

    return selected


def main():
    parser = argparse.ArgumentParser(description="智能帧筛选：OCR预筛 + 哈希去重")
    parser.add_argument("frames_dir", help="输入帧目录")
    parser.add_argument("--ocr-threshold", type=int, default=20,
                        help="OCR 文字量阈值，低于此值视为无内容（默认 20）")
    parser.add_argument("--hash-threshold", type=int, default=10,
                        help="哈希距离阈值，低于此值视为相同帧（默认 10）")
    parser.add_argument("--text-threshold", type=float, default=0.7,
                        help="OCR文本相似度阈值，低于此值拆分为不同帧（默认 0.7）")
    parser.add_argument("--skip-clustering", action="store_true",
                        help="跳过知识点聚类，保留所有去重后的帧（用于vision二次筛选）")
    parser.add_argument("--output-dir", default=None,
                        help="输出目录（默认为 frames_dir 的同级 selected 子目录）")
    args = parser.parse_args()

    if not args.output_dir:
        parent = os.path.dirname(args.frames_dir.rstrip("/\\"))
        args.output_dir = os.path.join(parent, "selected")

    selected = smart_select(args.frames_dir, args.ocr_threshold,
                            args.hash_threshold, args.text_threshold,
                            args.skip_clustering, args.output_dir)

    if selected:
        print(f"\n下一步：用 vision 对 {args.output_dir} 中的帧打分")
        print(f"  然后选得分最高的 5-8 帧嵌入 DOCX")


if __name__ == "__main__":
    main()
