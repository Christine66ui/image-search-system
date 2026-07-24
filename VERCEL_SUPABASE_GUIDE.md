# Vercel + Supabase 部署方案

## 方案概述

将图片检索系统部署到Vercel，使用Supabase作为数据存储，避开Railway的部署问题。

## 架构说明

- **Vercel**: 托管前端界面和API路由
- **Supabase Storage**: 存储42张产品图片
- **Supabase Database**: 存储产品元数据和预计算的特征向量
- **本地预处理**: 提前计算图片特征，避免在serverless函数中运行深度学习模型

## 实施步骤

### 第一步：本地预计算图片特征

1. **运行特征提取脚本**
```bash
cd C:\Users\Z1550\Desktop\垦特系统测试260721\image-search
python precompute_features.py
```

这会生成 `image_features.json` 文件，包含所有产品的特征向量。

### 第二步：设置Supabase项目

1. **创建Supabase项目**
   - 访问 [supabase.com](https://supabase.com)
   - 点击 "New Project"
   - 选择免费计划
   - 等待项目创建完成

2. **创建数据表**
   - 进入 SQL Editor
   - 执行以下SQL：

```sql
-- 创建产品表
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50),
    product_id VARCHAR(50),
    filename VARCHAR(255),
    image_url TEXT,
    feature_vector TEXT, -- 存储JSON格式的特征向量
    vector_length INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引以提高查询性能
CREATE INDEX idx_category ON products(category);
CREATE INDEX idx_product_id ON products(product_id);
```

3. **创建存储桶**
   - 进入 Storage
   - 创建名为 `product-images` 的存储桶
   - 设置为公开访问（Public bucket）

4. **获取API密钥**
   - 进入 Project Settings → API
   - 复制以下信息：
     - Project URL
     - anon public key
     - service_role key (用于上传)

### 第三步：上传数据到Supabase

1. **配置环境变量**
```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，填入你的Supabase信息
SUPABASE_URL=your_project_url
SUPABASE_SERVICE_KEY=your_service_role_key
```

2. **安装依赖**
```bash
pip install supabase python-dotenv
```

3. **运行上传脚本**
```bash
python upload_to_supabase.py
```

这会自动上传所有图片到Supabase Storage，并将特征数据插入数据库。

### 第四步：配置Vercel项目

1. **安装Node.js依赖**
```bash
cd C:\Users\Z1550\Desktop\垦特系统测试260721\image-search
npm init -y
npm install @supabase/supabase-js
```

2. **推送代码到GitHub**
```bash
git add .
git commit -m "Add Vercel + Supabase deployment"
git push origin main
```

3. **在Vercel导入项目**
   - 访问 [vercel.com](https://vercel.com)
   - 点击 "New Project"
   - 导入你的GitHub仓库
   - 配置项目设置

4. **设置环境变量**
   在Vercel项目设置中添加：
   - `SUPABASE_URL`: 你的Supabase项目URL
   - `SUPABASE_ANON_KEY`: 你的Supabase anon key

5. **部署**
   - 点击 "Deploy"
   - 等待构建完成

### 第五步：测试部署

1. **访问部署的URL**
   - Vercel会提供一个 `.vercel.app` 的访问地址

2. **测试图片上传功能**
   - 上传产品图片
   - 查看匹配结果

## 方案优势

### ✅ 优点：
1. **部署简单**: Vercel和Supabase都有很好的免费计划
2. **稳定可靠**: 两个平台都是成熟的云服务
3. **扩展性好**: Supabase可以轻松存储更多图片
4. **成本低**: 免费计划足够小型项目使用

### ⚠️ 注意事项：
1. **特征提取限制**: 当前方案需要在本地预计算特征
2. **实时特征提取**: 如需实时提取，需要配置外部AI服务
3. **查询性能**: 大量图片时可能需要优化相似度计算

## 后续优化方向

### 1. 实时特征提取
如果需要实时提取特征，可以集成：
- **Cloudinary AI**: 图片分析和特征提取
- **AWS Rekognition**: 图像识别服务
- **Azure Computer Vision**: 微软的视觉AI服务

### 2. 性能优化
- **向量化搜索**: 使用专门的向量数据库如Pinecone
- **缓存机制**: 添加Redis缓存热门查询
- **批量处理**: 优化数据库查询

### 3. 功能增强
- **用户上传**: 允许用户添加自己的产品
- **批量导入**: 支持批量图片上传
- **高级过滤**: 按类别、价格等条件筛选

## 故障排除

### Vercel构建失败
- 检查 `package.json` 是否正确
- 确认环境变量已设置
- 查看构建日志中的错误信息

### Supabase连接错误
- 验证API密钥是否正确
- 检查网络连接
- 确认Supabase项目状态正常

### 特征提取失败
- 确认PyTorch已正确安装
- 检查图片文件是否存在
- 验证图片格式是否支持

## 总结

这个方案通过预计算特征和分离存储，成功避开了在serverless环境中运行深度学习模型的问题，是一个稳定可靠的部署方案。
