"""
预计算产品图片特征并导出为JSON
用于Vercel + Supabase部署方案
"""

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image
import numpy as np
from pathlib import Path
import json

# 配置
GALLERY_PATH = Path(__file__).parent.parent / '产品图库'
OUTPUT_FILE = Path(__file__).parent / 'image_features.json'
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print("Loading ResNet50 model...")
model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
model = nn.Sequential(*list(model.children())[:-1])
model = model.to(DEVICE)
model.eval()

def preprocess_image(image_path):
    """图像预处理"""
    img = Image.open(image_path).convert('L')  # 转灰度
    img = img.convert('RGB')

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return transform(img).unsqueeze(0)

def extract_features(image_path):
    """提取图像特征"""
    img_tensor = preprocess_image(image_path).to(DEVICE)

    with torch.no_grad():
        features = model(img_tensor)
        features = features.squeeze().cpu().numpy()

    # L2归一化
    features = features / np.linalg.norm(features)
    return features.tolist()

def main():
    """扫描图库并提取所有特征"""
    print(f"Scanning gallery: {GALLERY_PATH}")

    if not GALLERY_PATH.exists():
        print(f"Gallery path not found: {GALLERY_PATH}")
        return

    products = []

    for category_dir in GALLERY_PATH.iterdir():
        if not category_dir.is_dir():
            continue

        category = category_dir.name

        for product_dir in category_dir.iterdir():
            if not product_dir.is_dir():
                continue

            product_id = product_dir.name

            for img_file in product_dir.iterdir():
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    print(f"Processing: {category}/{product_id}/{img_file.name}")

                    try:
                        features = extract_features(str(img_file))

                        # 构建相对路径
                        relative_path = f"{category}/{product_id}/{img_file.name}"

                        products.append({
                            'category': category,
                            'product_id': product_id,
                            'filename': img_file.name,
                            'relative_path': relative_path,
                            'feature_vector': features,  # 2048维向量
                            'vector_length': len(features)
                        })
                    except Exception as e:
                        print(f"Error processing {img_file.name}: {e}")

    # 保存为JSON
    output_data = {
        'total_products': len(products),
        'vector_dimension': 2048,
        'created_at': str(Path(__file__).stat().st_mtime),
        'products': products
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Features computed and saved to {OUTPUT_FILE}")
    print(f"Total products: {len(products)}")
    print(f"Vector dimension: 2048")

if __name__ == '__main__':
    main()
