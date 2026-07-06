"""
B站视频智能抽帧 + 字幕下载工具
功能：
  1. 下载B站视频（支持时间段裁剪）
  2. 场景检测 + 聚合去重抽帧（适合讲课视频）
  3. 固定间隔抽帧（对比用）
  4. 下载AI字幕（JSON + 带时间戳的TXT）

用法：
  python extract_frames.py <bvid> [--page N] [--start MM:SS] [--end MM:SS] [--mode scene|fixed|both] [--subtitle] [--interval 30] [--threshold 0.04] [--merge-gap 5]

示例：
  # 完整视频，场景检测 + 字幕
  python extract_frames.py BV1xx411c7mD --page 1 --mode scene --subtitle

  # 只处理 5:00-10:00 片段，固定 20s 间隔 + 字幕
  python extract_frames.py BV1xx411c7mD --page 1 --start 5:00 --end 10:00 --mode fixed --interval 20 --subtitle

  # 只下载字幕，不抽帧
  python extract_frames.py BV1xx411c7mD --page 1 --subtitle --mode fixed --interval 9999
"""

import argparse
import json
import os
import re
import subprocess
import sys
import glob
from pathlib import Path


# ============================================================
# 配置区 - 路径优先级：当前目录 > 环境变量 > 默认路径
# ============================================================
def _find_file(filename, env_var=None, default_dir=None):
    """在当前目录、环境变量目录、默认目录中查找文件"""
    # 1. 当前目录
    if os.path.exists(os.path.join(os.getcwd(), filename)):
        return os.getcwd()
    # 2. 环境变量目录
    if env_var and os.environ.get(env_var):
        d = os.environ[env_var]
        if os.path.exists(os.path.join(d, filename)):
            return d
    # 3. 脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, filename)):
        return script_dir
    # 4. 默认目录
    if default_dir:
        return default_dir
    return os.getcwd()

_default_workspace = os.path.join(os.path.expanduser("~"), "bilibili-notes", "workspace")
_default_frames = os.path.join(os.path.expanduser("~"), "bilibili-notes", "frames")

WORKSPACE = os.environ.get("BILI_NOTES_WORKSPACE",
    _find_file("bilibili_cookies.txt", "BILI_NOTES_WORKSPACE", _default_workspace))
COOKIE_FILE = os.path.join(WORKSPACE, "bilibili_cookies.txt")
# 帧输出目录（必须是纯英文路径，vision工具不能识别中文路径）
FRAMES_DIR = os.environ.get("BILI_NOTES_FRAMES",
    os.environ.get("BILI_NOTES_WORKSPACE", _default_frames))


def time_to_seconds(t: str) -> int:
    """Convert MM:SS or HH:MM:SS to seconds."""
    parts = t.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return int(t)


def seconds_to_time(s: float) -> str:
    """Convert seconds to MM-SS format (no colon, safe for filenames)."""
    m, sec = divmod(int(s), 60)
    return f"{m:02d}m{sec:02d}s"


def get_video_info(bvid: str) -> dict:
    """Get video metadata from Bilibili API."""
    import urllib.request
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if data["code"] != 0:
        raise RuntimeError(f"API error: {data}")
    return data["data"]


def get_cookie_value(cookie_file: str, name: str) -> str:
    """Extract a specific cookie value from Netscape cookie file."""
    with open(cookie_file, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 7 and parts[5] == name:
                return parts[6]
    return ""


def download_subtitles(bvid: str, page: int, start: float = None, end: float = None) -> str:
    """Download AI subtitles from Bilibili. Returns path to saved subtitle file."""
    import urllib.request

    info = get_video_info(bvid)
    cid = info["pages"][page - 1]["cid"]
    title = info["pages"][page - 1]["part"]

    safe_name = re.sub(r'[<>:"/\\|?*]', '_', f"{bvid}_p{page}")
    sub_path = os.path.join(WORKSPACE, f"{safe_name}_subtitles.json")

    if os.path.exists(sub_path):
        print(f"[skip] Subtitles already exist: {sub_path}")
        with open(sub_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Get subtitle URL from player API
        sessdata = get_cookie_value(COOKIE_FILE, "SESSDATA")
        player_url = f"https://api.bilibili.com/x/player/wbi/v2?bvid={bvid}&cid={cid}"
        req = urllib.request.Request(player_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bilibili.com",
            "Cookie": f"SESSDATA={sessdata}",
        })
        with urllib.request.urlopen(req) as resp:
            player_data = json.loads(resp.read())

        subtitles = player_data.get("data", {}).get("subtitle", {}).get("subtitles", [])
        if not subtitles:
            print("[warn] No subtitles available (may need login)")
            return ""

        sub_url = subtitles[0]["subtitle_url"]
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url

        print(f"[subtitle] Downloading: {subtitles[0].get('lan_doc', 'unknown')}")
        req = urllib.request.Request(sub_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        with open(sub_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[subtitle] Saved: {sub_path}")

    # Filter by time range if specified
    body = data.get("body", [])
    if start is not None or end is not None:
        filtered = []
        for item in body:
            t = item["from"]
            if start is not None and t < start:
                continue
            if end is not None and t > end:
                continue
            filtered.append(item)
        body = filtered
        print(f"[subtitle] Filtered to {len(body)} entries ({start or 0}s - {end or 'end'}s)")

    # Save as readable text with timestamps
    txt_path = sub_path.replace(".json", ".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n")
        f.write(f"# 来源: {bvid} P{page}\n")
        if start or end:
            f.write(f"# 时间段: {start or 0}s - {end or 'end'}s\n")
        f.write(f"# 字幕条数: {len(body)}\n\n")
        for item in body:
            ts = seconds_to_time(item["from"])
            f.write(f"[{ts}] {item['content']}\n")
    print(f"[subtitle] Text: {txt_path} ({len(body)} entries)")

    return txt_path


def download_video(bvid: str, page: int, start: str = None, end: str = None) -> str:
    """Download video with yt-dlp, optionally trimming to a time range."""
    info = get_video_info(bvid)
    cid = info["pages"][page - 1]["cid"]
    title = info["pages"][page - 1]["part"]

    safe_name = re.sub(r'[<>:"/\\|?*]', '_', f"{bvid}_p{page}")
    output_path = os.path.join(WORKSPACE, f"{safe_name}.mp4")

    # If time range specified, use a different filename to avoid overwriting full video
    if start or end:
        range_tag = f"_{start or '0'}-{end or 'end'}".replace(":", "")
        range_path = os.path.join(WORKSPACE, f"{safe_name}{range_tag}.mp4")
        if os.path.exists(range_path):
            print(f"[skip] Trimmed video already exists: {range_path}")
            return range_path
        output_path = range_path
    elif os.path.exists(output_path):
        print(f"[skip] Video already exists: {output_path}")
        return output_path

    url = f"https://www.bilibili.com/video/{bvid}?p={page}"
    cmd = [
        "yt-dlp",
        "--cookies", COOKIE_FILE,
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "-o", output_path,
    ]

    if start or end:
        # yt-dlp --download-sections for time range trimming
        section = "*"
        if start:
            section += start
        section += "-"
        if end:
            section += end
        cmd.extend(["--download-sections", section])

    cmd.append(url)

    print(f"[download] {title}")
    print(f"[download] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # 打印实际分辨率
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", output_path],
            capture_output=True, text=True
        )
        if probe.stdout.strip():
            w, h = probe.stdout.strip().split(",")
            print(f"[info] 实际分辨率: {w}x{h}")
    except Exception:
        pass

    return output_path


def extract_fixed_frames(video_path: str, interval: int = 30) -> list:
    """Extract frames at fixed intervals."""
    out_dir = os.path.join(FRAMES_DIR, "fixed")
    os.makedirs(out_dir, exist_ok=True)

    # Clean old frames
    for f in glob.glob(os.path.join(out_dir, "*.jpg")):
        os.remove(f)

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"fps=1/{interval}",
        "-q:v", "2",
        os.path.join(out_dir, "frame_%04d.jpg"),
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    # Small delay to ensure filesystem flushes (especially on Windows with non-ASCII paths)
    import time; time.sleep(0.3)

    frames = sorted(glob.glob(os.path.join(out_dir, "frame_*.jpg")))
    print(f"[fixed] {len(frames)} frames @ {interval}s interval -> {out_dir}")
    return frames


def extract_scene_frames(video_path: str, threshold: float = 0.04, merge_gap: float = 5.0) -> list:
    """
    Extract frames using scene detection + clustering.
    - threshold: scene change sensitivity (lower = more sensitive)
    - merge_gap: merge scene changes within N seconds into one
    """
    out_dir = os.path.join(FRAMES_DIR, "scene")
    os.makedirs(out_dir, exist_ok=True)

    # Clean old frames
    for f in glob.glob(os.path.join(out_dir, "*.jpg")):
        os.remove(f)

    # Pass 1: detect scene change timestamps
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr",
        "-q:v", "2",
        os.path.join(out_dir, "raw_%04d.jpg"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    # Parse timestamps from showinfo output
    timestamps = []
    for line in result.stderr.split("\n"):
        m = re.search(r"pts_time:(\d+\.?\d*)", line)
        if m:
            timestamps.append(float(m.group(1)))

    print(f"[scene] Detected {len(timestamps)} raw scene changes")

    if not timestamps:
        # Fallback: if no scene changes, use fixed interval
        print("[scene] No scene changes detected, falling back to fixed 30s interval")
        return extract_fixed_frames(video_path, 30)

    # Pass 2: cluster nearby timestamps (within merge_gap seconds)
    clusters = []
    current_cluster = [timestamps[0]]
    for t in timestamps[1:]:
        if t - current_cluster[-1] <= merge_gap:
            current_cluster.append(t)
        else:
            clusters.append(current_cluster)
            current_cluster = [t]
    clusters.append(current_cluster)

    # Take the middle timestamp from each cluster
    key_timestamps = [c[len(c) // 2] for c in clusters]
    print(f"[scene] Merged into {len(key_timestamps)} clusters (gap={merge_gap}s)")

    # Clean raw frames
    for f in glob.glob(os.path.join(out_dir, "raw_*.jpg")):
        os.remove(f)

    # Pass 3: extract exact keyframes at cluster timestamps
    for i, ts in enumerate(key_timestamps):
        out_file = os.path.join(out_dir, f"frame_{i+1:04d}_{seconds_to_time(ts)}.jpg")
        cmd = [
            "ffmpeg", "-y", "-ss", str(ts),
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            out_file,
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    frames = sorted(glob.glob(os.path.join(out_dir, "frame_*.jpg")))
    print(f"[scene] {len(frames)} keyframes -> {out_dir}")
    return frames


def main():
    global WORKSPACE, COOKIE_FILE, FRAMES_DIR

    parser = argparse.ArgumentParser(description="B站视频智能抽帧工具")
    parser.add_argument("bvid", help="B站视频 BV号")
    parser.add_argument("--page", type=int, default=1, help="分P号 (默认 1)")
    parser.add_argument("--start", help="起始时间 MM:SS 或 HH:MM:SS")
    parser.add_argument("--end", help="结束时间 MM:SS 或 HH:MM:SS")
    parser.add_argument("--mode", choices=["scene", "fixed", "cover", "both"], default="scene",
                        help="抽帧模式: scene=场景检测, fixed=固定间隔, cover=全覆盖(每10秒,用于后续打分筛选)")
    parser.add_argument("--interval", type=int, default=30,
                        help="固定间隔秒数 (默认 30, cover模式默认10)")
    parser.add_argument("--threshold", type=float, default=0.04,
                        help="场景检测阈值 (默认 0.04)")
    parser.add_argument("--merge-gap", type=float, default=5.0,
                        help="场景聚合间隔秒数 (默认 5)")
    parser.add_argument("--no-download", action="store_true",
                        help="跳过下载，使用已有视频文件")
    parser.add_argument("--subtitle", action="store_true",
                        help="同时下载AI字幕")
    parser.add_argument("--workspace", default=os.environ.get("BILI_NOTES_WORKSPACE", WORKSPACE),
                        help="工作区目录（默认从环境变量 BILI_NOTES_WORKSPACE 获取）")
    parser.add_argument("--frames", default=os.environ.get("BILI_NOTES_FRAMES", FRAMES_DIR),
                        help="帧输出目录（默认从环境变量 BILI_NOTES_FRAMES 获取）")
    args = parser.parse_args()

    # 运行时覆盖全局路径
    WORKSPACE = args.workspace
    COOKIE_FILE = os.path.join(WORKSPACE, "bilibili_cookies.txt")
    FRAMES_DIR = args.frames

    os.makedirs(WORKSPACE, exist_ok=True)
    os.makedirs(FRAMES_DIR, exist_ok=True)

    # Step 0: Parse time range to seconds (for subtitle filtering)
    start_sec = time_to_seconds(args.start) if args.start else None
    end_sec = time_to_seconds(args.end) if args.end else None

    # Step 1: Download subtitles (independent of video)
    if args.subtitle:
        download_subtitles(args.bvid, args.page, start_sec, end_sec)

    # Step 2: Download video
    if args.no_download:
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', f"{args.bvid}_p{args.page}")
        if args.start or args.end:
            range_tag = f"_{args.start or '0'}-{args.end or 'end'}".replace(":", "")
            video_path = os.path.join(WORKSPACE, f"{safe_name}{range_tag}.mp4")
        else:
            video_path = os.path.join(WORKSPACE, f"{safe_name}.mp4")
        if not os.path.exists(video_path):
            print(f"[error] Video not found: {video_path}")
            sys.exit(1)
        print(f"[skip] Using existing: {video_path}")
    else:
        video_path = download_video(args.bvid, args.page, args.start, args.end)

    # Step 2: Extract frames
    if args.mode == "cover":
        # Cover mode: fixed interval, default 10s for full coverage
        cover_interval = args.interval if args.interval != 30 else 10
        extract_fixed_frames(video_path, cover_interval)
    elif args.mode in ("fixed", "both"):
        extract_fixed_frames(video_path, args.interval)

    if args.mode in ("scene", "both"):
        extract_scene_frames(video_path, args.threshold, args.merge_gap)

    print("\n[done] All frames extracted successfully!")


if __name__ == "__main__":
    main()
