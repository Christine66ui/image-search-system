# 产品图片检索系统

基于深度学习的图片检索系统，支持上传产品图片并自动匹配图库产品。

## 功能特点

- **智能匹配**：使用ResNet50深度学习模型提取图像特征
- **颜色弱化**：转换为灰度图进行特征提取，同款不同色可识别为同一款
- **角度容差**：允许拍摄角度和背景存在差异
- **相似度排序**：按匹配度从高到低展示结果
- **款号展示**：自动显示匹配产品的款号

## 技术栈

- **后端**：Python Flask + PyTorch + scikit-learn
- **前端**：HTML + JavaScript + CSS
- **模型**：ResNet50 (ImageNet预训练)

## 本地运行

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
cd backend
python app.py
```

### 3. 访问系统

打开浏览器访问：http://localhost:5000

## 部署

### 推荐平台

由于项目需要运行深度学习模型，推荐以下平台：

1. **Railway** - 最推荐，支持Python，免费额度充足
2. **Render** - 支持 Python 和 持久存储
3. **Heroku** - 经典选择

### Railway 部署步骤

1. 访问 https://railway.app
2. 连接GitHub账号
3. 点击"New Project" → "Deploy from GitHub repo"
4. 选择此仓库
5. Railway会自动检测Python项目并配置
6. 等待部署完成

### 环境变量（如需要）

- `PORT`: Railway自动设置
- `GALLERY_PATH`: 可配置图库路径

## 图库结构

产品图库应按以下结构组织：

```
产品图库/
├── 草帽/
│   ├── CS001/
│   │   ├── CS001-xxx-A.jpg
│   │   └── CS001-xxx-B.jpg
│   └── CS002/
├── 渔夫帽/
│   └── CS004/
└── 围巾/
    ├── CS007.png
    └── CS008.png
```

## 注意事项

- 首次运行需要下载ResNet50模型（约100MB）
- 建议图片清晰度 ≥ 720p
- 支持格式：JPG、PNG
- 如需重建索引，访问 POST /api/rebuild-index

## 许可证

MIT License
