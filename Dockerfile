FROM shenxianmq/video_scraper_env:v1.0.1

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY main.py .
COPY init.py
COPY entrypoint.sh .

# 创建必要的目录（使用绝对路径）
RUN mkdir -p /app/temp/telegram /app/temp/youtube \
    && mkdir -p /app/downloads/telegram \
    && mkdir -p /app/downloads/youtube

# 设置脚本权限
RUN chmod +x entrypoint.sh

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 使用启动脚本
ENTRYPOINT ["./entrypoint.sh"] 