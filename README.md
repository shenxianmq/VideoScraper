# Telegram 多功能助手

这是一个功能强大的 Telegram 助手程序，支持同时运行机器人和用户账号，具有媒体文件下载和定时消息发送功能。

## 功能特点

- 支持同时运行机器人和用户账号
- 机器人功能：
  - 自动下载 Telegram 媒体文件（视频、音频、图片等）
  - 下载 YouTube 视频（支持单个视频和播放列表）
  - 自动分类存储下载的文件
- 用户账号功能：
  - 定时发送消息到指定群组/频道
  - 支持多个定时任务
- 其他特性：
  - 支持代理配置
  - 会话文件统一管理
  - 详细的日志记录
  - 优雅的程序关闭处理

## 安装步骤

1. 安装 Python 3.7 或更高版本
2. 克隆项目并安装依赖：

```bash
git clone [项目地址]
cd VideoScraper
pip install -r requirements.txt
```

## 配置说明

1. 在项目根目录下创建 `config` 文件夹
2. 在 `config` 文件夹中创建 `config.yaml` 文件，配置示例：

```yaml
# API配置（必需）
api_id: "你的API ID"
api_hash: "你的API Hash"

# 机器人账号配置
bot_account:
  token: "你的机器人token" # 机器人的 token
  session_name: "bot_session" # 机器人的 session 文件名

# 用户账号配置
user_account:
  enabled: true # 是否启用用户账号
  phone: "+8613800138000" # 你的手机号（带国际区号）
  session_name: "user_session" # 用户的 session 文件名

# YouTube下载配置
youtube_download:
  format: "best"
  cookies: "" # YouTube cookies（可选）

# 定时消息配置
scheduled_messages:
  # 发送到群组的示例
  - chat_id: "@group_username" # 群组用户名
    message: "这是发送到群组的消息"
    time: "08:00" # 每天发送时间（24小时制）

  # 发送到机器人的示例
  - chat_id: "@bot_username" # 机器人用户名
    message: "这是发送给机器人的消息"
    time: "09:00"

  # 使用数字ID发送的示例
  - chat_id: "123456789" # 群组/频道/用户的数字ID
    message: "这是使用数字ID发送的消息"
    time: "10:00"

# 代理配置
proxy:
  enabled: false
  host: "127.0.0.1"
  port: 7890

# 日志级别
log_level: "INFO"
```

### 获取必要的配置信息

1. 获取 API ID 和 API Hash：

   - 访问 https://my.telegram.org/
   - 登录您的 Telegram 账号
   - 进入 "API development tools"
   - 创建一个新的应用程序，获取 API ID 和 API Hash

2. 获取机器人 Token：
   - 在 Telegram 中找到 @BotFather
   - 发送 /newbot 命令创建新机器人
   - 获取机器人的 API Token

## 使用方法

1. 启动程序：

```bash
python main.py
```

2. 首次运行：

   - 如果启用了用户账号，程序会要求输入手机号验证码
   - 验证通过后会在 `config` 目录下生成 session 文件
   - 后续运行无需重新验证

3. 机器人使用：

   - 将机器人添加到群组
   - 发送媒体文件给机器人，它会自动下载
   - 发送 YouTube 链接，机器人会下载视频

4. 定时消息：
   - 在配置文件中设置定时消息任务
   - 程序会按照设定的时间自动发送消息
   - 支持配置多个定时任务

## 文件结构

```
VideoScraper/
├── config/                 # 配置文件目录
│   ├── config.yaml        # 配置文件
│   ├── bot_session.session # 机器人会话文件
│   └── user_session.session # 用户会话文件
├── downloads/             # 下载文件目录
│   ├── telegram/         # Telegram 媒体文件
│   │   ├── videos/      # 视频文件
│   │   ├── audios/      # 音频文件
│   │   ├── photos/      # 图片文件
│   │   └── others/      # 其他文件
│   └── youtube/         # YouTube 下载文件
├── temp/                 # 临时文件目录
├── main.py              # 主程序
└── README.md            # 说明文档
```

## 注意事项

1. 安全性：

   - 请妥善保管配置文件和会话文件
   - 不要将包含敏感信息的文件上传到公开场所

2. 使用限制：

   - 遵守 Telegram 的使用政策
   - 避免频繁发送消息，可能触发限制
   - YouTube 下载需要遵守相关服务条款

3. 代理设置：
   - 如果无法直接访问 Telegram，请配置代理
   - 支持 SOCKS5 代理

## 常见问题

1. 程序无法连接 Telegram：

   - 检查网络连接
   - 确认代理配置是否正确
   - 验证 API ID 和 API Hash 是否正确

2. 机器人无法接收消息：

   - 确认 bot_token 是否正确
   - 检查机器人是否被禁用

3. 定时消息发送失败：
   - 确认用户账号是否正确登录
   - 检查群组/频道 ID 是否正确
   - 验证是否具有发送消息的权限

## 更新日志

### v1.0.0

- 初始版本发布
- 支持机器人和用户账号同时运行
- 实现媒体文件下载和定时消息功能

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目。

## 许可证

本项目采用 MIT 许可证。
