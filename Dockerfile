# 使用Python官方镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY backend/requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# 暴露端口
EXPOSE 5000

# 启动命令 - 使用绝对路径确保正确启动
CMD ["python", "/app/backend/app.py"]
