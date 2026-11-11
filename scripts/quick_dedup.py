"""快速去重脚本 - 仅用感知哈希，跳过OCR（opinion类视频用）"""
import os
import sys
from pathlib import Path
from PIL import Image
import imagehash

def quick_dedup(input_dir, output_dir, threshold=5):
    """用感知哈希去重，threshold越小越严格"""
    os.makedirs(output_dir, exist_ok=True)
    
    files = sorted(Path(input_dir).glob("*.jpg"))
    if not files:
        print(f"[ERROR] No jpg files in {input_dir}")
        return
    
    hashes = []
    kept = []
    
    for f in files:
        try:
            img = Image.open(f)
            h = imagehash.average_hash(img)
            
            # 检查是否与已有帧重复
            is_dup = False
            for prev_h, prev_f in hashes:
                if h - prev_h <= threshold:
                    is_dup = True
                    break
            
            if not is_dup:
                hashes.append((h, f))
                kept.append(f)
        except Exception as e:
            print(f"[WARN] Error processing {f}: {e}")
    
    # 复制到 selected
    for f in kept:
        dst = Path(output_dir) / f.name
        import shutil
        shutil.copy2(f, dst)
    
    print(f"[INFO] {len(files)} frames → {len(kept)} unique (threshold={threshold})")
    return kept

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python quick_dedup.py <input_dir> <output_dir> [threshold]")
        sys.exit(1)
    
    quick_dedup(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 5)
