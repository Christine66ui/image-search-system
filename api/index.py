"""
Vercel Serverless Function for Image Search
适配Vercel的API路由格式
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights
import os
import json
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import cv2

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 配置路径
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
GALLERY_PATH = BASE_DIR.parent / '产品图库'
INDEX_FILE = BASE_DIR / 'api' / 'feature_index.json'
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print(f"BASE_DIR: {BASE_DIR}")
print(f"GALLERY_PATH: {GALLERY_PATH}")
print(f"INDEX_FILE: {INDEX_FILE}")

# 加载ResNet50模型
print("Loading ResNet50 model...")
try:
    model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
    model = nn.Sequential(*list(model.children())[:-1])
    model = model.to(DEVICE)
    model.eval()
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# 图像预处理
def preprocess_image(image_path):
    """图像预处理：转灰度、调整大小、标准化"""
    try:
        img = Image.open(image_path).convert('L')  # 转灰度
        img = img.convert('RGB')  # 转回RGB（三通道都是灰度值）
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        return transform(img).unsqueeze(0)
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

# 提取特征
def extract_features(image_tensor):
    """提取图像特征"""
    if model is None:
        return None
    try:
        with torch.no_grad():
            features = model(image_tensor.to(DEVICE))
        return features.cpu().numpy().flatten()
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None

# 扫描图库
def scan_gallery():
    """扫描图库并建立索引"""
    index = {}

    if not GALLERY_PATH.exists():
        print(f"Gallery path not found: {GALLERY_PATH}")
        return index

    for category_dir in GALLERY_PATH.iterdir():
        if category_dir.is_dir():
            category_name = category_dir.name
            for product_dir in category_dir.iterdir():
                if product_dir.is_dir():
                    product_id = product_dir.name
                    images = []
                    for img_file in product_dir.iterdir():
                        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                            tensor = preprocess_image(img_file)
                            if tensor is not None:
                                features = extract_features(tensor)
                                if features is not None:
                                    images.append({
                                        'path': str(img_file.relative_to(GALLERY_PATH)),
                                        'features': features.tolist()
                                    })
                    if images:
                        index[product_id] = {
                            'category': category_name,
                            'images': images
                        }

    return index

# 加载或创建索引
def get_or_create_index():
    """加载或创建特征索引"""
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    # 创建新索引
    print("Creating new index...")
    index = scan_gallery()

    # 保存索引
    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except:
        print("Could not save index file")

    return index

# Vercel要求的主处理函数
def handler(request):
    """Vercel Serverless Function主处理函数"""
    with app.request_context(request.environ):
        try:
            path = request.path

            # 处理预检请求
            if request.method == 'OPTIONS':
                response = jsonify({'status': 'ok'})
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                return response

            # 重建索引API
            if path == '/api/rebuild-index' and request.method == 'POST':
                index = scan_gallery()
                try:
                    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                        json.dump(index, f, ensure_ascii=False, indent=2)
                except:
                    pass
                return jsonify({'status': 'success', 'indexed': len(index)})

            # 图片搜索API
            elif path == '/api/search' and request.method == 'POST':
                if 'image' not in request.files:
                    return jsonify({'error': 'No image uploaded'}), 400

                file = request.files['image']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400

                # 保存上传的文件
                filename = f"upload_{file.filename}"
                filepath = UPLOAD_FOLDER / filename
                file.save(str(filepath))

                # 提取查询图片特征
                query_tensor = preprocess_image(filepath)
                if query_tensor is None:
                    return jsonify({'error': 'Failed to process image'}), 400

                query_features = extract_features(query_tensor)
                if query_features is None:
                    return jsonify({'error': 'Failed to extract features'}), 400

                # 加载图库索引
                gallery_index = get_or_create_index()

                # 搜索匹配
                results = []
                threshold = 0.5

                for product_id, product_data in gallery_index.items():
                    for img_data in product_data['images']:
                        gallery_features = np.array(img_data['features'])
                        similarity = cosine_similarity([query_features], [gallery_features])[0][0]

                        if similarity >= threshold:
                            results.append({
                                'path': f"/api/image/{img_data['path']}",
                                'similarity': float(similarity),
                                'category': product_data['category'],
                                'product_id': product_id
                            })

                # 按相似度排序
                results.sort(key=lambda x: x['similarity'], reverse=True)

                return jsonify({'results': results})

            # 获取图片API
            elif path.startswith('/api/image/') and request.method == 'GET':
                file_path = path.replace('/api/image/', '')
                full_path = GALLERY_PATH / file_path

                if not full_path.exists():
                    return jsonify({'error': 'Image not found'}), 404

                return send_file(str(full_path))

            # 健康检查
            elif path == '/api/health' and request.method == 'GET':
                return jsonify({'status': 'ok', 'model_loaded': model is not None})

            else:
                return jsonify({'error': 'Not found'}), 404

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': str(e)}), 500

# Vercel需要导出app对象
app.handler = handler

# 为本地测试保留原有路由
@app.route('/api/search', methods=['POST'])
def search():
    return handler(request)

@app.route('/api/rebuild-index', methods=['POST'])
def rebuild_index():
    return handler(request)

@app.route('/api/image/<path:filepath>', methods=['GET'])
def get_image(filepath):
    return handler(request)

@app.route('/api/health', methods=['GET'])
def health():
    return handler(request)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
