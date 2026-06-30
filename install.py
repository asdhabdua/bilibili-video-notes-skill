#!/usr/bin/env python3
"""
Bilibili Video Notes - 一键安装脚本
支持 Hermes Agent / Claude Code / Codex / 独立使用

用法：
  python install.py              # 自动检测环境并安装
  python install.py --hermes     # 安装到 Hermes Agent
  python install.py --claude     # 安装到 Claude Code
  python install.py --codex      # 安装到 Codex
  python install.py --standalone # 仅安装依赖（不装到任何AI）
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_home():
    return Path.home()


def install_deps():
    """安装 Python 依赖"""
    print("[1/3] 安装 Python 依赖...")
    req = Path(__file__).parent / "scripts" / "requirements.txt"
    if not req.exists():
        print(f"  [warn] requirements.txt not found at {req}")
        return False
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  [ok] 依赖安装成功")
    else:
        print(f"  [error] {result.stderr[:200]}")
        return False

    # 检查 ffmpeg
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        print(f"  [ok] ffmpeg 已安装: {ffmpeg}")
    else:
        print("  [warn] ffmpeg 未安装，视频处理需要它")
        print("         下载: https://ffmpeg.org/download.html")
    return True


def install_hermes():
    """安装到 Hermes Agent skill 目录"""
    print("[2/3] 安装到 Hermes Agent...")
    home = get_home()
    
    # 检测 skill 目录
    if platform.system() == "Windows":
        skill_dir = home / "AppData" / "Local" / "hermes" / "skills" / "media" / "bilibili-video-notes"
    else:
        skill_dir = home / ".hermes" / "skills" / "media" / "bilibili-video-notes"

    src = Path(__file__).parent
    
    # 复制文件
    if skill_dir.exists():
        print(f"  [info] 目标目录已存在，更新中: {skill_dir}")
    else:
        skill_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制 SKILL.md
    shutil.copy2(src / "SKILL.md", skill_dir / "SKILL.md")
    
    # 复制 scripts/
    scripts_dst = skill_dir / "scripts"
    scripts_dst.mkdir(exist_ok=True)
    for f in (src / "scripts").iterdir():
        if f.is_file():
            shutil.copy2(f, scripts_dst / f.name)
    
    # 复制 references/
    if (src / "references").exists():
        ref_dst = skill_dir / "references"
        ref_dst.mkdir(exist_ok=True)
        for f in (src / "references").iterdir():
            if f.is_file():
                shutil.copy2(f, ref_dst / f.name)
    
    print(f"  [ok] 已安装到: {skill_dir}")
    print("  [info] 重启 Hermes 后生效")
    return str(skill_dir)


def install_claude():
    """安装到 Claude Code 项目目录"""
    print("[2/3] 安装到 Claude Code...")
    home = get_home()
    
    # Claude Code 通常在项目根目录找 CLAUDE.md
    # 把脚本复制到用户选择的工作目录
    src = Path(__file__).parent
    
    # 复制 CLAUDE.md 到当前目录
    if (src / "CLAUDE.md").exists():
        dst_claude = Path.cwd() / "CLAUDE.md"
        if dst_claude.exists():
            print(f"  [warn] CLAUDE.md 已存在，跳过（手动合并）")
        else:
            shutil.copy2(src / "CLAUDE.md", dst_claude)
            print(f"  [ok] CLAUDE.md -> {dst_claude}")
    
    # 复制 scripts/ 到当前目录
    scripts_dst = Path.cwd() / "scripts"
    scripts_dst.mkdir(exist_ok=True)
    for f in (src / "scripts").iterdir():
        if f.is_file():
            shutil.copy2(f, scripts_dst / f.name)
    print(f"  [ok] scripts/ -> {scripts_dst}")
    
    # 复制 cookie 模板
    cookie_tpl = src / "bilibili_cookies.txt.example"
    if cookie_tpl.exists():
        dst_cookie = Path.cwd() / "bilibili_cookies.txt.example"
        if not dst_cookie.exists():
            shutil.copy2(cookie_tpl, dst_cookie)
            print(f"  [ok] bilibili_cookies.txt.example -> {dst_cookie}")
    
    print(f"  [info] 工作目录: {Path.cwd()}")
    print(f"  [info] 复制 cookie: cp bilibili_cookies.txt.example bilibili_cookies.txt")
    return str(Path.cwd())


def setup_cookie(target_dir):
    """提示用户配置 Cookie"""
    print("[3/3] 配置 Cookie...")
    cookie_file = Path(target_dir) / "bilibili_cookies.txt"
    cookie_example = Path(target_dir) / "bilibili_cookies.txt.example"
    
    if cookie_file.exists():
        print(f"  [ok] Cookie 文件已存在: {cookie_file}")
        return
    
    if cookie_example.exists():
        shutil.copy2(cookie_example, cookie_file)
        print(f"  [ok] 已从模板创建: {cookie_file}")
    else:
        # 创建模板
        cookie_file.write_text(
            "# Netscape HTTP Cookie File\n"
            "# 从浏览器获取 SESSDATA：F12 → Application → Cookies → bilibili.com\n"
            ".bilibili.com\tTRUE\t/\tFALSE\t0\tSESSDATA\tYOUR_SESSDATA_HERE\n"
        )
        print(f"  [ok] 已创建: {cookie_file}")
    
    print()
    print("  === 配置 Cookie ===")
    print("  1. 用 Edge/Chrome 打开 bilibili.com（确保已登录）")
    print("  2. 按 F12 打开开发者工具")
    print("  3. 点击 Application（应用程序）标签")
    print("  4. 左侧 Cookies → https://www.bilibili.com")
    print("  5. 找到 SESSDATA，复制它的值")
    print(f"  6. 编辑 {cookie_file}")
    print("     把 YOUR_SESSDATA_HERE 替换为复制的值")
    print()



def install_codex():
    """安装到 Codex 项目目录"""
    print("[2/3] 安装到 Codex...")
    src = Path(__file__).parent
    
    # 复制 AGENTS.md 到当前目录
    if (src / "AGENTS.md").exists():
        dst_agents = Path.cwd() / "AGENTS.md"
        if dst_agents.exists():
            print(f"  [warn] AGENTS.md 已存在，跳过（手动合并）")
        else:
            shutil.copy2(src / "AGENTS.md", dst_agents)
            print(f"  [ok] AGENTS.md -> {dst_agents}")
    
    # 复制 scripts/
    scripts_dst = Path.cwd() / "scripts"
    scripts_dst.mkdir(exist_ok=True)
    for f in (src / "scripts").iterdir():
        if f.is_file():
            shutil.copy2(f, scripts_dst / f.name)
    print(f"  [ok] scripts/ -> {scripts_dst}")
    
    # 复制 cookie 模板
    cookie_tpl = src / "bilibili_cookies.txt.example"
    if cookie_tpl.exists():
        dst_cookie = Path.cwd() / "bilibili_cookies.txt.example"
        if not dst_cookie.exists():
            shutil.copy2(cookie_tpl, dst_cookie)
            print(f"  [ok] bilibili_cookies.txt.example -> {dst_cookie}")
    
    print(f"  [info] 工作目录: {Path.cwd()}")
    return str(Path.cwd())

def main():
    parser = argparse.ArgumentParser(description="Bilibili Video Notes 一键安装")
    parser.add_argument("--hermes", action="store_true", help="安装到 Hermes Agent")
    parser.add_argument("--claude", action="store_true", help="安装到 Claude Code")
    parser.add_argument("--codex", action="store_true", help="安装到 Codex")
    parser.add_argument("--standalone", action="store_true", help="仅安装依赖")
    args = parser.parse_args()

    print("=" * 50)
    print("  Bilibili Video Notes 安装程序")
    print("=" * 50)
    print()

    # 1. 安装依赖
    install_deps()
    print()

    # 2. 安装到目标
    target_dir = None
    if args.codex:
        target_dir = install_codex()
    elif args.hermes:
        target_dir = install_hermes()
    elif args.claude:
        target_dir = install_claude()
    elif args.standalone:
        print("[2/3] 独立模式，跳过 AI 工具安装")
        target_dir = str(Path(__file__).parent)
    else:
        # 自动检测
        print("[2/3] 自动检测环境...")
        hermes_dir = get_home() / ".hermes"
        if platform.system() == "Windows":
            hermes_dir = get_home() / "AppData" / "Local" / "hermes"
        
        # Check for git repo (Codex needs it)
        git_dir = Path.cwd() / ".git"
        codex_cmd = shutil.which("codex")
        
        if hermes_dir.exists():
            print("  [detect] 检测到 Hermes Agent")
            target_dir = install_hermes()
        elif codex_cmd:
            print("  [detect] 检测到 Codex CLI，安装到当前目录")
            target_dir = install_codex()
        elif git_dir.exists():
            print("  [detect] 检测到 Git 仓库，安装到当前目录（兼容 Codex）")
            target_dir = install_codex()
        else:
            print("  [detect] 未检测到特定环境，安装到当前目录")
            target_dir = install_claude()
    
    print()

    # 3. 配置 Cookie
    if target_dir:
        setup_cookie(target_dir)

    # 完成
    print("=" * 50)
    print("  安装完成！")
    print("=" * 50)
    print()
    print("使用方法：")
    print("  1. 配置好 Cookie（见上方说明）")
    print("  2. 对 AI 说：帮我做这个视频的笔记 <B站链接>")
    print("  3. 或手动运行：")
    print("     python scripts/extract_frames.py BV号 --page N --mode cover --subtitle")
    print("     python scripts/smart_select.py frames/fixed --skip-clustering")
    print()


if __name__ == "__main__":
    main()
