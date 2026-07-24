"""
上传图片和特征到Supabase
需要安装: pip install supabase
"""

import json
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # 使用service key有写入权限

GALLERY_PATH = Path(__file__).parent.parent / '产品图库'
FEATURES_FILE = Path(__file__).parent / 'image_features.json'

def init_supabase():
    """初始化Supabase客户端"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase credentials")
        print("请设置环境变量: SUPABASE_URL 和 SUPABASE_SERVICE_KEY")
        return None

    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_images_to_storage(supabase: Client):
    """上传图片到Supabase Storage"""
    print("Uploading images to Supabase Storage...")

    # 创建存储桶（如果不存在）
    try:
        # 检查存储桶是否存在
        buckets = supabase.storage.list_buckets()
        bucket_exists = any(b['name'] == 'product-images' for b in buckets.data)

        if not bucket_exists:
            print("Creating storage bucket: product-images")
            supabase.storage.create_bucket('product-images', {'public': True})
    except Exception as e:
        print(f"Bucket check/create error: {e}")

    # 上传图片
    with open(FEATURES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    uploaded = []
    for product in data['products']:
        relative_path = product['relative_path']
        local_path = GALLERY_PATH / relative_path

        if not local_path.exists():
            print(f"❌ File not found: {local_path}")
            continue

        try:
            # Supabase存储路径
            storage_path = f"{relative_path.replace(os.sep, '/')}"

            # 读取文件并上传
            with open(local_path, 'rb') as f:
                file_data = f.read()

            supabase.storage.from_('product-images').upload(
                storage_path,
                file_data,
                {'content-type': 'image/jpeg'}
            )

            # 获取公开URL
            image_url = f"{SUPABASE_URL}/storage/v1/object/public/product-images/{storage_path}"
            uploaded.append({
                'relative_path': relative_path,
                'image_url': image_url
            })
            print(f"✅ Uploaded: {relative_path}")

        except Exception as e:
            print(f"❌ Upload failed for {relative_path}: {e}")

    return uploaded

def insert_features_to_database(supabase: Client, uploaded_images):
    """插入特征向量到数据库"""
    print("Inserting features into database...")

    with open(FEATURES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 创建图片URL映射
    url_map = {item['relative_path']: item['image_url'] for item in uploaded_images}

    success_count = 0
    for product in data['products']:
        relative_path = product['relative_path']

        if relative_path not in url_map:
            print(f"⚠️  Skipping {relative_path} (not uploaded)")
            continue

        try:
            # 插入数据库记录
            record = {
                'category': product['category'],
                'product_id': product['product_id'],
                'filename': product['filename'],
                'image_url': url_map[relative_path],
                'feature_vector': json.dumps(product['feature_vector']),
                'vector_length': product['vector_length']
            }

            result = supabase.table('products').insert(record).execute()
            success_count += 1
            print(f"✅ Inserted: {relative_path}")

        except Exception as e:
            print(f"❌ Database insert failed for {relative_path}: {e}")

    print(f"\n✅ Successfully inserted {success_count} products into database")

def main():
    """主函数"""
    print("=== Supabase Upload Script ===")

    # 1. 初始化Supabase
    supabase = init_supabase()
    if not supabase:
        return

    # 2. 检查特征文件
    if not FEATURES_FILE.exists():
        print(f"❌ Features file not found: {FEATURES_FILE}")
        print("请先运行 precompute_features.py 生成特征文件")
        return

    # 3. 上传图片
    uploaded_images = upload_images_to_storage(supabase)

    # 4. 插入数据库
    if uploaded_images:
        insert_features_to_database(supabase, uploaded_images)
    else:
        print("❌ No images were uploaded")

    print("\n=== Upload Complete ===")

if __name__ == '__main__':
    main()
