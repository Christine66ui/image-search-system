"""
图像检索系统后端服务
- 使用ResNet50提取图像特征
- 转换灰度图弱化颜色特征
- 余弦相似度匹配产品
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
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

app = Flask(__name__)
CORS(app)

# 配置 - 使用绝对路径
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
GALLERY_PATH = BASE_DIR.parent / '产品图库'
INDEX_FILE = BASE_DIR / 'backend' / 'feature_index.json'
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print(f"BASE_DIR: {BASE_DIR}")
print(f"GALLERY_PATH: {GALLERY_PATH}")
print(f"INDEX_FILE: {INDEX_FILE}")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 加载ResNet50模型（移除最后的分类层，用于特征提取）
print("Loading ResNet50 model...")
model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
# 移除最后的分类层，获取2048维特征向量
model = nn.Sequential(*list(model.children())[:-1])
model = model.to(DEVICE)
model.eval()

# 图像预处理（重点：转换为灰度图弱化颜色）
def preprocess_image(image_path):
    """图像预处理：转灰度、调整大小、标准化"""
    img = Image.open(image_path).convert('L')  # 转灰度
    img = img.convert('RGB')  # 转回RGB（三通道相同）

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.485, 0.485], std=[0.229, 0.229, 0.229])
    ])

    return transform(img).unsqueeze(0)

def extract_features(image_path):
    """提取图像特征向量"""
    img_tensor = preprocess_image(image_path).to(DEVICE)

    with torch.no_grad():
        features = model(img_tensor)
        features = features.squeeze().cpu().numpy()

    # L2归一化
    features = features / np.linalg.norm(features)
    return features.tolist()

def scan_gallery():
    """扫描产品图库，建立特征索引"""
    gallery_path = Path(GALLERY_PATH)
    index = {}

    print(f"Scanning gallery: {gallery_path}")

    for category_dir in gallery_path.iterdir():
        if not category_dir.is_dir():
            continue

        category = category_dir.name

        # 遍历类别目录
        for item in category_dir.iterdir():
            if item.is_dir():
                # 子目录（如CS001/）
                product_id = item.name
                for img_file in item.glob('*'):  # 支持所有图片格式
                    if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        key = f"{category}/{product_id}/{img_file.name}"
                        try:
                            features = extract_features(str(img_file))
                            index[key] = {
                                'category': category,
                                'product_id': product_id,
                                'filename': img_file.name,
                                'features': features,
                                'path': str(img_file)
                            }
                            print(f"  Indexed: {key}")
                        except Exception as e:
                            print(f"  Error indexing {key}: {e}")

            elif item.suffix in ['.jpg', '.png', '.jpeg']:
                # 直接文件（如围巾目录下的文件）
                product_id = item.stem
                key = f"{category}/{item.name}"
                try:
                    features = extract_features(str(item))
                    index[key] = {
                        'category': category,
                        'product_id': product_id,
                        'filename': item.name,
                        'features': features,
                        'path': str(item)
                    }
                    print(f"  Indexed: {key}")
                except Exception as e:
                    print(f"  Error indexing {key}: {e}")

    # 保存索引
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Index saved: {len(index)} images")
    return index

def load_index():
    """加载已保存的特征索引"""
    if not os.path.exists(INDEX_FILE):
        return scan_gallery()

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# 启动时建立索引
feature_index = load_index()
print(f"Loaded index with {len(feature_index)} images")

@app.route('/test')
def test():
    """返回测试页面"""
    test_path = BASE_DIR / 'test.html'
    return send_file(str(test_path))

@app.route('/app')
def frontend():
    """返回前端页面"""
    frontend_path = BASE_DIR / 'frontend' / 'index.html'
    return send_file(str(frontend_path))

@app.route('/api/search', methods=['POST'])
def search():
    """图像检索接口"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # 保存上传的图片
    upload_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(upload_path)

    # 提取查询图片特征
    try:
        query_features = extract_features(upload_path)
    except Exception as e:
        return jsonify({'error': f'Feature extraction failed: {str(e)}'}), 500

    # 计算与所有图库图片的相似度
    results = []
    query_vec = np.array(query_features).reshape(1, -1)

    for key, item in feature_index.items():
        gallery_vec = np.array(item['features']).reshape(1, -1)
        similarity = cosine_similarity(query_vec, gallery_vec)[0][0]

        # 构建相对路径用于前端显示
        # 检查是否是子目录结构（key中包含三个部分：category/product_id/filename）
        key_parts = key.split('/')
        if len(key_parts) == 3:
            # 子目录结构：category/product_id/filename
            rel_path = key
        else:
            # 直接文件：category/filename
            rel_path = f"{item['category']}/{item['filename']}"

        results.append({
            'product_id': item['product_id'],
            'category': item['category'],
            'filename': item['filename'],
            'similarity': float(similarity),
            'path': f"/api/image/{rel_path}"
        })

    # 按相似度排序
    results.sort(key=lambda x: x['similarity'], reverse=True)

    # 返回前10个结果（或相似度>0.5的结果）
    threshold = 0.5
    filtered_results = [r for r in results if r['similarity'] > threshold]

    if not filtered_results:
        return jsonify({
            'found': False,
            'message': '未找到相似产品',
            'query_image': file.filename
        })

    # 按款号分组（同一款号只显示最相似的）
    seen_products = {}
    for r in filtered_results:
        pid = r['product_id']
        if pid not in seen_products or r['similarity'] > seen_products[pid]['similarity']:
            seen_products[pid] = r

    final_results = list(seen_products.values())[:10]

    return jsonify({
        'found': True,
        'results': final_results,
        'query_image': file.filename
    })

@app.route('/api/rebuild-index', methods=['POST'])
def rebuild_index():
    """重建特征索引"""
    global feature_index
    feature_index = scan_gallery()
    return jsonify({'message': f'Index rebuilt with {len(feature_index)} images'})

@app.route('/api/gallery/<category>/<product_id>/<filename>')
def get_gallery_image(category, product_id, filename):
    """获取图库图片（子目录结构）"""
    path = GALLERY_PATH / category / product_id / filename
    if not path.exists():
        # 尝试直接在类别目录下查找
        path = GALLERY_PATH / category / filename
    return send_file(str(path))

@app.route('/api/image/<path:filepath>')
def get_image(filepath):
    """通用图片获取路由"""
    path = GALLERY_PATH / filepath
    if not path.exists():
        return jsonify({'error': 'Image not found'}), 404
    return send_file(str(path))

@app.route('/static/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    return send_from_directory('static', filename)

# 根路由 - 直接返回HTTP 200，不做任何耗时操作
@app.route('/')
def health_check():
    """健康检查端点 - 直接返回200状态"""
    return 'OK', 200

if __name__ == '__main__':
    # 读取Railway动态分配的端口，默认5000
    port = int(os.environ.get('PORT', 5000))

    print("Starting Image Search Server...")
    print(f"Gallery path: {GALLERY_PATH}")
    print(f"Model loaded: {model is not None}")
    print(f"Server running on port: {port}")

    # 使用0.0.0.0让外部可以访问
    app.run(host='0.0.0.0', port=port, debug=False)
