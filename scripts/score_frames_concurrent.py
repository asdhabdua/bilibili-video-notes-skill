#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发视觉分析脚本 - bilibili-video-notes

用途：对 selected/ 目录下的所有帧一次性并发进行 vision 分析，
输出结构化 JSON 供后续选帧和写笔记使用。

使用示例：
    # 第一步：给所有 selected/ 帧打分（用于选出最终帧）
    python score_frames_concurrent.py \\
        --frames "./frames/pXX/selected" \\
        --output "./workspace/vision_scores_pXX.json" \\
        --workers 16

    # 第二步：对最终选定的帧提取图中文字/公式/表格（用于写正文）
    python score_frames_concurrent.py \\
        --frames "./frames/pXX/final" \\
        --output "./workspace/vision_extract_pXX.json" \\
        --mode extract \\
        --workers 16

输出 JSON 格式（--mode score）：
    {
      "frame_0001.jpg": {
        "theme": "Introduction",
        "keywords": ["concept", "diagram"],
        "score": 8,
        "complete": true
      },
      ...
    }

输出 JSON 格式（--mode extract）：
    {
      "frame_0001.jpg": {
        "theme": "Introduction",
        "score": 8,
        "text": "图中出现的所有文字...",
        "formulas": ["E = mc^2", "..."],
        "tables": [{"headers": [...], "rows": [...]}],
        "concepts": ["概念1: 定义", "概念2: 公式"],
        "complete": true
      },
      ...
    }
"""

import os
import sys
import base64
import json
import time
import argparse
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

# 尝试加载 skill 目录下的 .env 文件
try:
    from dotenv import load_dotenv
    skill_dir = Path(__file__).resolve().parent.parent
    dotenv_path = skill_dir / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
except ImportError:
    pass

# 默认从 .env 读取 API 配置
DEFAULT_BASE_URL = os.getenv('VISION_BASE_URL', os.getenv('SOPHNET_BASE_URL', "https://api.openai.com/v1"))
DEFAULT_MODEL = os.getenv('VISION_MODEL', os.getenv('SOPHNET_MODEL', "gpt-4o"))
DEFAULT_API_KEY = os.getenv('VISION_API_KEY', os.getenv('SOPHNET_API_KEY', ""))
DEFAULT_WORKERS = 16
DEFAULT_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 3

# 针对教育/讲课视频的 vision prompts

SCORE_PROMPT = """This is a screenshot from an educational video (likely a lecture or course).
Please answer strictly in the following JSON format, with no extra content:
{
  "theme": "A short title summarizing the frame (5-15 words)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "score": 8,
  "complete": true
}
'score' is content completeness from 1-10 (higher for more concepts/formulas/diagrams/handwritten notes).
'complete' means the screenshot is fully visible, not cropped or blocked.""".strip()

EXTRACT_PROMPT = """This is a screenshot from an educational video (likely a lecture or course).
Please extract all readable educational content from this image.
Answer strictly in the following JSON format, with no extra content:
{
  "theme": "A short title summarizing the frame (5-15 words)",
  "score": 8,
  "complete": true,
  "text": "All readable text in the image, transcribed faithfully. Include formulas, labels, and annotations.",
  "formulas": ["formula1", "formula2"],
  "tables": [
    {
      "caption": "table caption if any",
      "headers": ["col1", "col2"],
      "rows": [["a", "b"], ["c", "d"]]
    }
  ],
  "concepts": [
    "Concept name: its definition or explanation from the image",
    "Another concept: its explanation"
  ]
}
'score' is content completeness from 1-10.
'complete' means the screenshot is fully visible, not cropped or blocked.
If there are no formulas or tables, use empty arrays [] for those fields.""".strip()


def encode_image(path: Path) -> str:
    """将图片转为 base64 data URL。"""
    with open(path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def parse_json_response(text: str) -> dict:
    """尝试从模型返回中提取 JSON。"""
    text = text.strip()
    # 如果有代码块，去掉标记
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试从文本中提取第一个 JSON 对象
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end+1])
        raise


def process_one_frame(
    frame_path: Path,
    api_key: str,
    base_url: str,
    model: str,
    timeout: int,
    max_retries: int,
    prompt: str
) -> tuple:
    """
    对单帧进行 vision 分析，失败时自动重试。
    返回: (frame_name, result_dict)
    """
    frame_name = frame_path.name
    data_url = encode_image(frame_path)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 2048
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = parse_json_response(content)

            # 根据不同模式保留字段
            result = {
                "theme": str(parsed.get("theme", "")),
                "score": int(parsed.get("score", 0)),
                "complete": bool(parsed.get("complete", True)),
                "raw": content,
                "error": None,
                "attempts": attempt,
                "timestamp": datetime.now().isoformat()
            }
            return frame_name, result

        except Exception as e:
            last_error = f"{type(e).__name__}: {str(e)}"
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 指数退避

    # 全部重试失败
    error_result = {
        "theme": "",
        "score": 0,
        "complete": False,
        "raw": "",
        "error": last_error,
        "attempts": max_retries,
        "timestamp": datetime.now().isoformat()
    }
    return frame_name, error_result


def main():
    parser = argparse.ArgumentParser(
        description="bilibili-video-notes: 并发视觉分析"
    )
    parser.add_argument("--frames", required=True, help="selected/ 帧目录路径")
    parser.add_argument("--output", required=True, help="输出 JSON 路径")
    parser.add_argument("--mode", choices=["score", "extract"], default="score",
                        help="分析模式: score=打分选帧（默认）, extract=提取图中文字/公式/表格")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY,
                        help="API key，默认先从 .env 文件 VISION_API_KEY 获取，再从环境变量获取")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help=f"模型基础 URL，默认 {DEFAULT_BASE_URL}")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"模型 ID，默认 {DEFAULT_MODEL}")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"并发线程数，默认 {DEFAULT_WORKERS}")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"单请求超时秒数，默认 {DEFAULT_TIMEOUT}")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
                        help=f"单帧最大重试次数，默认 {DEFAULT_MAX_RETRIES}")
    parser.add_argument("--resume", action="store_true",
                        help="断点续传：跳过已存在于输出 JSON 中的帧")
    args = parser.parse_args()

    if not args.api_key:
        print("[ERROR] 缺少 API key。请设置环境变量 VISION_API_KEY 或使用 --api-key")
        sys.exit(1)

    frames_dir = Path(args.frames)
    if not frames_dir.exists():
        print(f"[ERROR] 帧目录不存在: {frames_dir}")
        sys.exit(1)

    frames = sorted(frames_dir.glob("frame_*.jpg"))
    if not frames:
        print(f"[ERROR] 目录中没有 frame_*.jpg: {frames_dir}")
        sys.exit(1)

    prompt = SCORE_PROMPT if args.mode == "score" else EXTRACT_PROMPT
    print(f"[INFO] 模式={args.mode}，发现 {len(frames)} 张帧，使用 {args.workers} 线程并发分析")
    print(f"[INFO] base_url={args.base_url}, model={args.model}")

    # 断点续传
    existing = {}
    if args.resume and Path(args.output).exists():
        existing = json.load(open(args.output, encoding="utf-8"))
        frames = [f for f in frames if f.name not in existing]
        print(f"[INFO] 断点续传: 已完成 {len(existing)} 帧，剩余 {len(frames)} 帧")

    results = dict(existing)
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_frame = {
            executor.submit(
                process_one_frame,
                frame,
                args.api_key,
                args.base_url,
                args.model,
                args.timeout,
                args.max_retries,
                prompt
            ): frame for frame in frames
        }

        completed = 0
        for future in as_completed(future_to_frame):
            frame = future_to_frame[future]
            try:
                frame_name, result = future.result()
                results[frame_name] = result
                completed += 1
                status = "✓" if not result["error"] else "✗"
                print(f"[{status}] {completed}/{len(frames)} {frame_name} "
                      f"score={result['score']} theme={result['theme'][:30]}...")
            except Exception as e:
                print(f"[✗] {frame.name} 异常: {e}")
                results[frame.name] = {
                    "theme": "", "score": 0,
                    "complete": False, "raw": "", "error": str(e),
                    "attempts": 0, "timestamp": datetime.now().isoformat()
                }

    elapsed = time.time() - start_time
    success = sum(1 for r in results.values() if not r["error"])
    failed = len(results) - success

    # 保存结果
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[INFO] 完成：成功 {success}/{len(results)} 帧，失败 {failed} 帧，"
          f"耗时 {elapsed:.1f}秒，平均 {elapsed/max(len(results),1):.1f}秒/帧")
    print(f"[INFO] 结果已保存到: {out_path}")

    if failed > 0:
        print("[WARN] 部分帧分析失败，请检查输出 JSON 中的 error 字段")
        sys.exit(2)


if __name__ == "__main__":
    main()
