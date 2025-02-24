# VideoScraper

一个基于 Telegram Bot 的视频下载工具，支持下载 Telegram 视频消息和 YouTube 视频链接。

## 功能特性

- 支持下载 Telegram 视频消息
- 支持下载 YouTube 视频链接
- 支持代理配置
- 支持 YouTube cookies 配置
- 自动分类存储下载的视频
- Docker 部署支持

## 安装说明

### 方法 1：直接安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/VideoScraper.git
cd VideoScraper
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

### 方法 2：Docker 部署

#### 使用 Docker Compose（推荐）

1. 创建必要的目录和配置文件：

```bash
mkdir -p config downloads/telegram downloads/youtube
cp config.yaml.example config/config.yaml
```

2. 编辑 `docker-compose.yml`：

```yaml
version: "3"
services:
  video_scraper:
    image: shenxianmq/video_scraper:latest
    volumes:
      - ./config:/app/config
      - ./downloads/telegram:/app/downloads/telegram
      - ./downloads/youtube:/app/downloads/youtube
    restart: unless-stopped
    container_name: video_scraper
    environment:
      - TZ=Asia/Shanghai
```

3. 启动服务：

```bash
docker-compose up -d
```

4. 查看日志：

```bash
docker-compose logs -f
```

#### 使用 Docker CLI

1. 创建必要的目录和配置文件：

```bash
mkdir -p config downloads/telegram downloads/youtube
cp config.yaml.example config/config.yaml
```

2. 运行容器：

```bash
docker run -d \
  --name video_scraper \
  --restart unless-stopped \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/downloads/telegram:/app/downloads/telegram \
  -v $(pwd)/downloads/youtube:/app/downloads/youtube \
  -e TZ=Asia/Shanghai \
  shenxianmq/video_scraper:latest
```

3. 查看日志：

```bash
docker logs -f video_scraper
```

## 配置说明

1. 复制配置文件示例：

```bash
cp config.yaml.example config/config.yaml
```

2. 编辑配置文件 `config/config.yaml`：

```yaml
telegram_token: "" # 你的Telegram Bot Token
api_id: "" # Telegram API ID
api_hash: "" # Telegram API Hash
youtube_download:
  format: "best" # 视频下载质量
  cookies: "" # YouTube cookies，用于下载需要登录的视频
log_level: "INFO" # 日志级别
#代理仅支持socks5，不支持http
proxy:
  enabled: true # 是否启用代理
  host: "127.0.0.1" # 代理服务器地址
  port: 7890 # 代理服务器端口
```

## 使用说明

1. 启动机器人：

如果是直接安装：

```bash
python main.py
```

如果是使用 Docker，服务会自动启动。

2. 在 Telegram 中与机器人交互：
   - 发送 `/start` 开始使用
   - 转发视频消息给机器人进行下载
   - 发送 YouTube 视频链接给机器人进行下载

## 文件存储

- Telegram 视频将保存在 `downloads/telegram` 目录
- YouTube 视频将保存在 `downloads/youtube` 目录

## 注意事项

1. 确保有足够的磁盘空间用于存储下载的视频
2. YouTube 视频下载可能需要配置 cookies 才能下载某些受限制的视频
3. 如果使用代理，请确保代理服务器配置正确且可用
4. 使用 Docker 部署时，请确保挂载的目录权限正确
