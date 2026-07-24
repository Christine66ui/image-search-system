"""
检查后端返回的路径格式
"""
import json

# 读取索引文件
with open('feature_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

print("检查索引中的路径格式：")
print("\n前5个条目：")
for i, (key, item) in enumerate(list(index.items())[:5]):
    print(f"\n{i+1}. Key: {key}")
    print(f"   Category: {item['category']}")
    print(f"   Product ID: {item['product_id']}")
    print(f"   Filename: {item['filename']}")

    # 模拟后端构建路径的逻辑
    key_parts = key.split('/')
    if len(key_parts) == 3:
        rel_path = key
    else:
        rel_path = f"{item['category']}/{item['filename']}"

    api_path = f"/api/image/{rel_path}"
    print(f"   API Path: {api_path}")

    # 测试URL编码
    import urllib.parse
    encoded = '/'.join([urllib.parse.quote(part, safe='') for part in api_path.split('/')])
    print(f"   Encoded: {encoded}")
