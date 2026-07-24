# 使用Python官方镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制所有项目文件到app目录
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "backend/app.py"]
