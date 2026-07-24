"""
测试脚本 - 验证系统配置
"""
import sys
import os
from pathlib import Path

print("=" * 50)
print("Image Search System - Configuration Check")
print("=" * 50)

# 1. 检查Python版本
print("\n[1/5] Python version...")
print(f"[OK] Python {sys.version}")

# 2. 检查关键依赖
print("\n[2/5] Checking dependencies...")
try:
    import torch
    print(f"[OK] PyTorch {torch.__version__}")
    print(f"     CUDA available: {torch.cuda.is_available()}")
except ImportError:
    print("[FAIL] PyTorch not installed")
    print("       Run: pip install torch torchvision")

try:
    import flask
    print(f"[OK] Flask {flask.__version__}")
except ImportError:
    print("[FAIL] Flask not installed")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    print("[OK] scikit-learn installed")
except ImportError:
    print("[FAIL] scikit-learn not installed")

# 3. 检查目录结构
print("\n[3/5] Checking directory structure...")
base_dir = Path(__file__).resolve().parent.parent
print(f"Project directory: {base_dir}")

backend_dir = base_dir / 'backend'
frontend_dir = base_dir / 'frontend'
gallery_dir = base_dir.parent / '产品图库'

if backend_dir.exists():
    print(f"[OK] backend directory exists")
else:
    print(f"[FAIL] backend directory not found")

if frontend_dir.exists():
    print(f"[OK] frontend directory exists")
else:
    print(f"[FAIL] frontend directory not found")

if gallery_dir.exists():
    print(f"[OK] Gallery exists: {gallery_dir}")
    # 统计图片数量
    image_count = 0
    for cat in ['草帽', '渔夫帽', '围巾']:
        cat_path = gallery_dir / cat
        if cat_path.exists():
            images = list(cat_path.rglob('*.jpg')) + list(cat_path.rglob('*.png'))
            image_count += len(images)
            print(f"     {cat}: {len(images)} images")
    print(f"     Total: {image_count} images")
else:
    print(f"[FAIL] Gallery not found: {gallery_dir}")

# 4. 检查app.py
print("\n[4/5] Checking app.py...")
app_file = backend_dir / 'app.py'
if app_file.exists():
    print(f"[OK] app.py exists")
else:
    print(f"[FAIL] app.py not found")

# 5. 测试图片加载
print("\n[5/5] Testing image loading...")
try:
    from PIL import Image
    test_images = list(gallery_dir.rglob('*.jpg'))[:3]
    if test_images:
        for img in test_images:
            try:
                Image.open(img)
                print(f"[OK] {img.name} loads correctly")
            except Exception as e:
                print(f"[FAIL] {img.name} failed to load: {e}")
    else:
        print("[WARN] No test images found")
except Exception as e:
    print(f"[FAIL] Image loading test failed: {e}")

print("\n" + "=" * 50)
if all([backend_dir.exists(), frontend_dir.exists(), gallery_dir.exists()]):
    print("[PASS] Configuration check passed!")
    print("\nStart command:")
    print(f"  cd {backend_dir}")
    print("  python app.py")
else:
    print("[FAIL] Configuration check failed, please fix issues above")
print("=" * 50)
