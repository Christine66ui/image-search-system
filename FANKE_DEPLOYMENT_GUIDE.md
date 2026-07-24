# 凡科建站 + Railway后端 部署方案

## 架构说明
- **前端**: 使用凡科建站创建展示页面
- **后端**: 在Railway运行深度学习图片检索API
- **连接**: 凡科页面通过JavaScript调用Railway API

## 第一步：部署后端到Railway

### 1. 确保代码已推送到GitHub
   - 仓库：Christine66ui/image-search-system
   - 分支：main

### 2. 在Railway部署
   - 访问 railway.app
   - 点击 "New Project" → "Deploy from GitHub repo"
   - 选择 image-search-system 仓库
   - 等待部署完成

### 3. 获取API地址
   - 部署成功后，Railway会提供一个URL
   - 格式类似：`https://你的项目名.railway.app`
   - 这个URL就是你的API基础地址

## 第二步：在凡科建站创建前端

### 1. 注册登录凡科建站
   - 访问凡科建站官网
   - 注册并登录账号

### 2. 创建新网站
   - 点击"创建网站"
   - 选择合适的模板（企业官网或产品展示类）

### 3. 添加图片检索功能

#### 方法A：使用自定义HTML模块

1. 在凡科建站编辑器中找到"添加模块"
2. 选择"自定义HTML"或"代码"模块
3. 插入以下HTML代码：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>产品图片检索系统</title>
    <style>
        .search-container {
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            text-align: center;
        }
        .upload-area {
            border: 2px dashed #ccc;
            padding: 30px;
            margin: 20px 0;
            cursor: pointer;
        }
        .upload-area:hover {
            border-color: #007bff;
        }
        .results-area {
            margin-top: 30px;
        }
        .result-item {
            border: 1px solid #ddd;
            margin: 10px 0;
            padding: 10px;
            display: flex;
            align-items: center;
        }
        .result-item img {
            max-width: 100px;
            margin-right: 15px;
        }
        .btn-upload {
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="search-container">
        <h1>产品图片检索系统</h1>
        <p>上传产品图片，自动匹配相似产品</p>

        <div class="upload-area" id="uploadArea">
            <p>点击上传图片或拖拽图片到此处</p>
            <input type="file" id="fileInput" accept="image/*" style="display: none;">
            <button class="btn-upload" onclick="document.getElementById('fileInput').click()">选择图片</button>
        </div>

        <div id="previewArea" style="margin-top: 20px;">
            <img id="previewImage" style="max-width: 300px; display: none;">
        </div>

        <button class="btn-upload" id="searchBtn" style="display: none;" onclick="searchProducts()">开始检索</button>

        <div class="results-area" id="resultsArea"></div>
    </div>

    <script>
        const API_BASE_URL = 'https://你的railway项目地址.railway.app'; // 替换为你的Railway地址
        let selectedFile = null;

        // 文件选择处理
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = function(event) {
                    document.getElementById('previewImage').src = event.target.result;
                    document.getElementById('previewImage').style.display = 'block';
                    document.getElementById('searchBtn').style.display = 'inline-block';
                };
                reader.readAsDataURL(file);
            }
        });

        // 图片检索函数
        async function searchProducts() {
            if (!selectedFile) {
                alert('请先选择图片');
                return;
            }

            const formData = new FormData();
            formData.append('image', selectedFile);

            const resultsArea = document.getElementById('resultsArea');
            resultsArea.innerHTML = '<p>正在检索中，请稍候...</p>';

            try {
                const response = await fetch(`${API_BASE_URL}/api/search`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error('检索失败');
                }

                const data = await response.json();
                displayResults(data.results);
            } catch (error) {
                resultsArea.innerHTML = `<p>检索失败: ${error.message}</p>`;
            }
        }

        // 显示结果
        function displayResults(results) {
            const resultsArea = document.getElementById('resultsArea');

            if (!results || results.length === 0) {
                resultsArea.innerHTML = '<p>未找到相似产品</p>';
                return;
            }

            let html = '<h3>检索结果：</h3>';
            results.forEach((item, index) => {
                html += `
                    <div class="result-item">
                        <img src="${API_BASE_URL}${item.path}" alt="匹配产品">
                        <div>
                            <p><strong>相似度:</strong> ${(item.similarity * 100).toFixed(1)}%</p>
                            <p><strong>类别:</strong> ${item.category}</p>
                            <p><strong>款号:</strong> ${item.product_id}</p>
                        </div>
                    </div>
                `;
            });

            resultsArea.innerHTML = html;
        }

        // 拖拽上传
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#007bff';
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#ccc';
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#ccc';

            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = function(event) {
                    document.getElementById('previewImage').src = event.target.result;
                    document.getElementById('previewImage').style.display = 'block';
                    document.getElementById('searchBtn').style.display = 'inline-block';
                };
                reader.readAsDataURL(file);
            }
        });
    </script>
</body>
</html>
```

#### 方法B：使用凡科建站的表单功能

1. 创建"文件上传"表单组件
2. 设置表单提交到你的Railway API
3. 在表单设置中配置POST请求

### 4. 修改API地址

在上面的代码中，将：
```javascript
const API_BASE_URL = 'https://你的railway项目地址.railway.app';
```

替换为你的实际Railway项目地址。

## 第三步：测试功能

1. 保存并发布凡科建站网站
2. 访问网站，测试图片上传和检索功能
3. 确保前后端能正常通信

## 注意事项

1. **CORS问题**: 确保Railway后端已配置CORS支持（已配置）
2. **图片显示**: 凡科页面通过Railway API获取图片
3. **性能优化**: 考虑添加加载动画和错误提示

## 优点和缺点

### 优点：
- 凡科建站提供美观的界面模板
- 不需要手动设计CSS样式
- 响应式设计自动适配移动端

### 缺点：
- 需要两个平台（凡科+Railway）
- 功能受限于凡科建站的代码执行能力
- 可能需要凡科建站的付费版才能使用自定义代码

## 简化方案：直接使用Railway

如果发现凡科建站集成复杂，建议：
1. 继续在Railway部署完整系统
2. 或使用简单的HTML托管服务配合Railway后端
