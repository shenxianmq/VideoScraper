# Telegram 定时消息助手

这是一个 Telegram 定时消息助手程序，支持定时向群组、频道、机器人或用户发送消息。

## 功能特点

- 定时消息功能：
  - 支持发送消息到群组/频道
  - 支持发送消息给机器人
  - 支持多个定时任务
  - 灵活的时间配置
- 其他特性：
  - Docker 容器化部署
  - 支持代理配置
  - 会话文件统一管理
  - 详细的日志记录
  - 优雅的程序关闭处理

## Docker 部署

1. 构建 Docker 镜像：

```bash
docker build -t telegram-scheduler .
```

2. 运行容器：

```bash
docker run -d \
  --name telegram-scheduler \
  -v $(pwd)/config:/app/config \
  telegram-scheduler
```

3. 首次运行需要生成 session 文件：

```bash
# 进入容器
docker exec -it telegram-scheduler /bin/bash

# 运行 session 生成脚本
python init.py

# 按照提示输入手机号和验证码
# 完成后 session 文件会保存在 config 目录
```

4. 重启容器使配置生效：

```bash
docker restart telegram-scheduler
```

## 配置说明

1. 在项目根目录下创建 `config` 文件夹
2. 在 `config` 文件夹中创建 `config.yaml` 文件，配置示例：

```yaml
# API配置（必需）
api_id: "你的API ID"
api_hash: "你的API Hash"

# 用户账号配置
user_account:
  enabled: true # 是否启用用户账号
  phone: "+8613800138000" # 你的手机号（带国际区号）
  session_name: "user_session" # 用户的 session 文件名

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

# 代理配置（可选）
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

## 文件结构

```
VideoScraper/
├── config/                 # 配置文件目录
│   ├── config.yaml        # 配置文件
│   └── user_session.session # 用户会话文件
├── main.py                # 主程序
├── generate_session.py    # Session生成脚本
├── Dockerfile            # Docker构建文件
└── README.md             # 说明文档
```

## 注意事项

1. 安全性：

   - 请妥善保管配置文件和会话文件
   - 不要将包含敏感信息的文件上传到公开场所
   - 建议使用 Docker Secrets 或环境变量管理敏感信息

2. 使用限制：

   - 遵守 Telegram 的使用政策
   - 避免频繁发送消息，可能触发限制
   - 确保有权限向目标发送消息

3. Docker 相关：
   - 确保 config 目录正确挂载
   - 容器首次运行需要生成 session 文件
   - 修改配置后需要重启容器

## 常见问题

1. 容器无法连接 Telegram：

   - 检查网络连接
   - 确认代理配置是否正确
   - 验证 API ID 和 API Hash 是否正确

2. Session 生成失败：

   - 确认手机号格式正确（需要包含国际区号）
   - 检查验证码是否正确输入
   - 查看日志获取详细错误信息

3. 定时消息发送失败：
   - 确认 session 文件已正确生成
   - 检查目标 ID 或用户名是否正确
   - 验证是否具有发送消息的权限
   - 如果是给机器人发送消息，确保该机器人没有被停用

## 更新日志

### v1.0.0

- 初始版本发布
- 支持 Docker 部署
- 实现定时消息功能

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目。

## 许可证

本项目采用 MIT 许可证。
