#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制校验视频处理进度锁 (checklist_<vid>.json)。
未通过校验时退出非零状态码，阻止生成脚本跳步。
"""
import json, os, sys

def load_checklist(vid):
    path = f'checklist_{vid}.json'
    if not os.path.exists(path):
        raise RuntimeError(f'缺少进度锁: {path}')
    return json.load(open(path, encoding='utf-8'))

def assert_step(cl, key, expected, msg):
    actual = cl.get(key)
    if actual != expected:
        raise RuntimeError(f'{msg}: {actual} != {expected}')

def verify(vid, min_selected=4):
    cl = load_checklist(vid)
    assert_step(cl, 'subtitle_read', True, '字幕未读完')
    assert_step(cl, 'vision_scored', cl['frames_total'], 'vision 打分未完成')
    if len(cl.get('selected_frames', [])) < min_selected:
        raise RuntimeError(f'选帧不足 {min_selected} 帧: {len(cl.get("selected_frames", []))}')
    print(f'checklist_{vid}.json: PASS (frames={cl["frames_total"]}, scored={cl["vision_scored"]}, selected={len(cl["selected_frames"])})')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python verify_checklist.py <vid> [min_selected]')
        sys.exit(1)
    vid = sys.argv[1]
    min_sel = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    try:
        verify(vid, min_sel)
    except RuntimeError as e:
        print(f'FAIL: {e}')
        sys.exit(1)
