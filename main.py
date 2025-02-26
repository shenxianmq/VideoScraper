import os
import logging
from telethon import TelegramClient, events
import yaml
import yt_dlp
import re
import shutil
import asyncio
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 获取程序所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

# 在文件开头添加目录常量，所有路径都基于程序目录
TEMP_DIR = os.path.join(BASE_DIR, "temp")  # 临时下载目录
TELEGRAM_TEMP_DIR = os.path.join(TEMP_DIR, "telegram")
YOUTUBE_TEMP_DIR = os.path.join(TEMP_DIR, "youtube")

# Telegram媒体文件目录
TELEGRAM_DEST_DIR = os.path.join(BASE_DIR, "downloads/telegram")
TELEGRAM_VIDEOS_DIR = os.path.join(TELEGRAM_DEST_DIR, "videos")
TELEGRAM_AUDIOS_DIR = os.path.join(TELEGRAM_DEST_DIR, "audios")
TELEGRAM_PHOTOS_DIR = os.path.join(TELEGRAM_DEST_DIR, "photos")
TELEGRAM_OTHERS_DIR = os.path.join(TELEGRAM_DEST_DIR, "others")

YOUTUBE_DEST_DIR = os.path.join(BASE_DIR, "downloads/youtube")


# 加载配置文件
def load_config():
    config_file = os.path.join(CONFIG_DIR, "config.yaml")
    default_config = {
        "api_id": "",
        "api_hash": "",
        "user_account": {
            "phone": "",  # 用户的手机号
            "session_name": "user_session",  # 用户会话名称
        },
        "bot_account": {
            "token": "",  # 机器人 token
            "session_name": "bot_session",  # 机器人会话名称
        },
        "youtube_download": {
            "format": "best",
            "cookies": "",
        },
        "scheduled_messages": [
            {
                "chat_id": "",  # 目标群组/频道的ID或用户名
                "message": "",  # 要发送的消息
                "time": "08:00",  # 每天发送消息的时间，24小时制
            }
        ],
        "log_level": "INFO",
        "proxy": {
            "enabled": False,
            "host": "127.0.0.1",
            "port": 7890,
        },
    }

    try:
        # 确保配置目录存在
        os.makedirs(CONFIG_DIR, exist_ok=True)

        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
                if config is None:
                    config = {}
                # 合并默认配置和用户配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict) and isinstance(config[key], dict):
                        # 处理嵌套字典
                        for sub_key, sub_value in value.items():
                            if sub_key not in config[key]:
                                config[key][sub_key] = sub_value
        else:
            config = default_config
            # 创建默认配置文件
            with open(config_file, "w", encoding="utf-8") as file:
                yaml.dump(config, file, allow_unicode=True, default_flow_style=False)
            logger.warning(
                f"配置文件 {config_file} 不存在，已创建默认配置文件。\n"
                "请编辑配置文件，填入必要的信息：\n"
                "1. api_id: 你的API ID\n"
                "2. api_hash: 你的API Hash\n"
                "3. bot_account.token: 机器人Token\n"
                "4. youtube_download.cookies: YouTube cookies（可选）"
            )
            raise ValueError("请先配置 config/config.yaml 文件")

        # 验证必要的配置项
        if not config.get("api_id") or not config.get("api_hash"):
            raise ValueError("请在 config.yaml 中配置 api_id 和 api_hash")

        if not config.get("bot_account", {}).get("token"):
            raise ValueError("请在 config.yaml 中配置 bot_account.token")

        return config

    except Exception as e:
        logger.error(f"加载配置文件时出错: {str(e)}")
        raise


config = load_config()

# Telegram API 配置
API_ID = config.get("api_id", "")
API_HASH = config.get("api_hash", "")
BOT_TOKEN = config["bot_account"]["token"]

# 下载目录配置
BASE_DOWNLOAD_DIR = config.get("download_dir", "downloads")
TELEGRAM_DIR = os.path.join(BASE_DOWNLOAD_DIR, "telegram")
YOUTUBE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "youtube")
COOKIES_FILE = config.get("cookies_file", "cookies.txt")

# YouTube下载配置
YOUTUBE_CONFIG = config.get("youtube_download", {})
YT_FORMAT = YOUTUBE_CONFIG.get("format", "best")
YT_COOKIES = YOUTUBE_CONFIG.get("cookies", "")

# 创建必要的目录
os.makedirs(TELEGRAM_DIR, exist_ok=True)
os.makedirs(YOUTUBE_DIR, exist_ok=True)


# 在创建客户端之前添加代理配置
def get_proxy_config():
    proxy_config = config.get("proxy", {})
    if not proxy_config.get("enabled"):
        return None

    host = proxy_config.get("host", "127.0.0.1")
    port = proxy_config.get("port", 7890)

    return {
        "proxy_type": "socks5",
        "addr": host,
        "port": port,
    }


# 将事件处理器改为函数定义
def register_handlers(client):
    """注册所有事件处理器"""

    @client.on(events.NewMessage(pattern="/start"))
    async def start(event):
        """处理 /start 命令"""
        await event.reply("你好！请转发视频给我，我会自动下载到指定文件夹。")

    @client.on(events.NewMessage)
    async def download_video(event):
        """处理接收到的视频消息或YouTube链接"""
        status_message = None
        try:
            message_text = event.message.text if event.message.text else ""
            # 检查是否是YouTube链接
            youtube_pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.*"
            is_youtube = bool(re.match(youtube_pattern, message_text))

            if is_youtube:
                try:
                    status_message = await event.reply("开始解析youtube下载链接..")
                    ydl_opts = {
                        "format": YT_FORMAT,
                        "outtmpl": os.path.join(
                            YOUTUBE_TEMP_DIR, "%(title).100s-%(id)s.%(ext)s"
                        ),
                        "ignoreerrors": True,
                        "ignore_no_formats_error": True,
                        "restrictfilenames": True,  # 使用ASCII字符
                        "windowsfilenames": True,  # 确保Windows兼容性
                    }

                    # 添加代理配置
                    proxy_config = get_proxy_config()
                    if proxy_config:
                        ydl_opts["proxy"] = (
                            f"socks5://{proxy_config['addr']}:{proxy_config['port']}"
                        )

                    # 添加cookies配置
                    if YT_COOKIES:
                        # 创建临时cookies文件
                        import tempfile

                        with tempfile.NamedTemporaryFile(
                            mode="w", delete=False, suffix=".txt"
                        ) as f:
                            # 写入cookies文件头部
                            f.write("# Netscape HTTP Cookie File\n")
                            f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
                            f.write("# This is a generated file!  Do not edit.\n\n")

                            # 写入cookies
                            for cookie in YT_COOKIES.split(";"):
                                if cookie.strip():
                                    name_value = cookie.strip().split("=", 1)
                                    if len(name_value) == 2:
                                        name, value = name_value
                                        f.write(
                                            f".youtube.com\tTRUE\t/\tTRUE\t2999999999\t{name.strip()}\t{value.strip()}\n"
                                        )
                        temp_cookie_file = f.name
                        ydl_opts["cookiefile"] = temp_cookie_file

                    # 判断是否是播放列表
                    is_playlist = "list" in message_text or message_text.endswith(
                        "/videos"
                    )

                    if is_playlist:
                        # 首先获取视频信息
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(message_text, download=False)
                        total_videos = len(info["entries"])
                        success_count = 0
                        failed_videos = []
                        playlist_title = info.get("title", "未知播放列表")
                        await status_message.edit(
                            f"检测到播放列表：{playlist_title}\n"
                            f"共{total_videos}个视频，开始下载..."
                        )

                        # 下载播放列表中的每个视频
                        for index, entry in enumerate(info["entries"], 1):
                            if entry is None:
                                error_msg = f"视频 #{index} 无法访问（可能是私密视频）"
                                failed_videos.append(error_msg)
                                await status_message.edit(
                                    f"⚠️ 播放列表 {playlist_title} 中的视频无法访问\n"
                                    f"序号: {index}/{total_videos}\n"
                                    f"原因: 可能是私密视频"
                                )
                                continue

                            try:
                                video_url = entry.get("webpage_url") or entry.get("url")
                                video_title = entry.get("title", "未知标题")
                                if not video_url:
                                    error_msg = (
                                        f"视频 #{index} ({video_title}) URL获取失败"
                                    )
                                    failed_videos.append(error_msg)
                                    await status_message.edit(
                                        f"⚠️ 播放列表 {playlist_title} 中的视频URL获取失败\n"
                                        f"序号: {index}/{total_videos}\n"
                                        f"标题: {video_title}"
                                    )
                                    continue

                                # 下载单个视频
                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    # 更新下载开始的消息
                                    await event.reply(
                                        f"开始下载YouTube视频：{video_title}\n"
                                        f"序号: {index}/{total_videos}"
                                    )
                                    try:
                                        info = ydl.extract_info(
                                            video_url, download=True
                                        )
                                        video_id = info["id"]
                                        video_title = info["title"]

                                        # 查找并移动文件
                                        success, result = find_and_move_youtube_video(
                                            video_id, video_title, info
                                        )
                                        if success:
                                            success_count += 1
                                            await event.reply(
                                                f"✅ 播放列表 {playlist_title} 中的视频已下载并移动!\n"
                                                f"序号: {index}/{total_videos}\n"
                                                f"标题: {video_title}\n"
                                                f"位置: {result}\n"
                                                f"下载进度：{index}/{total_videos}\n"
                                                f"成功：{success_count} 失败：{len(failed_videos)}"
                                            )
                                        else:
                                            failed_videos.append(
                                                f"视频 #{index} ({video_title}) - {result}"
                                            )
                                            await event.reply(
                                                f"⚠️ 播放列表 {playlist_title} 中的视频下载完成但移动失败!\n"
                                                f"序号: {index}/{total_videos}\n"
                                                f"标题: {video_title}\n"
                                                f"错误: {result}\n"
                                                f"下载进度：{index}/{total_videos}\n"
                                                f"成功：{success_count} 失败：{len(failed_videos)}"
                                            )

                                    except Exception as download_error:
                                        error_msg = str(download_error)
                                        if "No video formats found" in error_msg:
                                            await status_message.edit(
                                                f"⚠️ 播放列表 {playlist_title} 中的视频格式不可用\n"
                                                f"序号: {index}/{total_videos}\n"
                                                f"标题: {video_title}"
                                            )
                                            failed_videos.append(
                                                f"视频 #{index} ({video_title}) - 格式不可用"
                                            )
                                        else:
                                            failed_videos.append(
                                                f"视频 #{index} ({video_title}) 下载失败: {error_msg[:100]}..."
                                            )
                                            await status_message.edit(
                                                f"❌ 播放列表 {playlist_title} 中的视频下载失败\n"
                                                f"序号: {index}/{total_videos}\n"
                                                f"标题: {video_title}\n"
                                                f"错误: {error_msg[:200]}..."
                                            )
                                        continue

                            except Exception as e:
                                error_msg = str(e)
                                if (
                                    "Video unavailable" in error_msg
                                    and "private" in error_msg
                                ):
                                    await status_message.edit(
                                        f"⚠️ 播放列表 {playlist_title} 中的视频为私密视频\n"
                                        f"序号: {index}/{total_videos}\n"
                                        f"标题: {video_title}"
                                    )
                                    failed_videos.append(
                                        f"视频 #{index} ({video_title}) - 私密视频"
                                    )
                                else:
                                    failed_videos.append(
                                        f"视频 #{index} ({video_title}) 下载失败: {error_msg[:100]}..."
                                    )
                                    await status_message.edit(
                                        f"❌ 播放列表 {playlist_title} 中的视频下载失败\n"
                                        f"序号: {index}/{total_videos}\n"
                                        f"标题: {video_title}\n"
                                        f"错误: {error_msg[:200]}..."
                                    )

                        # 播放列表下载完成后的总结
                        summary = (
                            f"📋 播放列表 {playlist_title} 下载完成！\n"
                            f"总计：{total_videos}个视频\n"
                            f"✅ 成功：{success_count}\n"
                            f"❌ 失败：{len(failed_videos)}"
                        )
                        if failed_videos:
                            summary += "\n\n失败视频列表："
                            for fail in failed_videos[:10]:  # 只显示前10个失败
                                summary += f"\n- {fail}"
                            if len(failed_videos) > 10:
                                summary += f"\n...等共{len(failed_videos)}个视频失败"
                        summary += f"\n\n📂 保存位置: {YOUTUBE_DEST_DIR}"

                        # 发送最终汇总消息
                        await status_message.edit(summary)

                    else:
                        # 单个视频的处理
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(message_text, download=True)
                            video_id = info["id"]
                            video_title = info["title"]

                            # 查找并移动文件
                            success, result = find_and_move_youtube_video(
                                video_id, video_title, info
                            )
                            if success:
                                await event.reply(
                                    f"✅ YouTube视频下载完成！\n"
                                    f"标题: {video_title}\n"
                                    f"位置: {result}"
                                )
                            else:
                                await event.reply(
                                    f"⚠️ YouTube视频下载完成但移动失败！\n"
                                    f"标题: {video_title}\n"
                                    f"错误: {result}"
                                )

                    # 删除临时cookies文件
                    if YT_COOKIES and os.path.exists(temp_cookie_file):
                        os.unlink(temp_cookie_file)

                    logger.info(
                        f"Successfully downloaded {'playlist' if is_playlist else 'video'}: {info.get('title', '')}"
                    )

                except Exception as e:
                    error_msg = str(e)
                    error_message = (
                        f"YouTube下载失败: 需要验证。\n"
                        f"请检查配置文件 config.yaml 中的 youtube_download.cookies 是否正确设置。"
                        if "Sign in to confirm you're not a bot" in error_msg
                        else f"YouTube视频下载失败: {error_msg}"
                    )
                    if status_message:
                        await event.reply(error_message)
                    else:
                        await event.reply(error_message)
                    logger.error(f"YouTube download error: {error_msg}")

            # 处理Telegram视频
            elif event.message.media:
                media = event.message.media

                # 获取文件名
                filename = None
                if hasattr(media, "document"):
                    # 从文档属性中获取文件名
                    for attr in media.document.attributes:
                        if hasattr(attr, "title") and attr.title:
                            filename = attr.title
                            break

                    # 如果属性中没有文件名，尝试从MIME类型生成
                    if not filename and hasattr(media.document, "mime_type"):
                        mime_type = media.document.mime_type
                        ext = mime_type.split("/")[-1] if mime_type else "unknown"
                        filename = f"未命名文件.{ext}"

                # 如果是照片，生成时间戳文件名
                elif hasattr(media, "photo"):
                    from datetime import datetime

                    filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

                # 如果以上都没有获取到文件名，使用消息文本或默认名称
                if not filename:
                    filename = event.message.message or "未命名文件"

                # 确定媒体类型和目标目录
                if hasattr(media, "document"):
                    mime_type = media.document.mime_type
                    if mime_type:
                        if mime_type.startswith("video/"):
                            media_type = "video"
                            target_dir = TELEGRAM_VIDEOS_DIR
                        elif mime_type.startswith("audio/"):
                            media_type = "audio"
                            target_dir = TELEGRAM_AUDIOS_DIR
                        else:
                            media_type = "other"
                            target_dir = TELEGRAM_OTHERS_DIR
                    else:
                        media_type = "other"
                        target_dir = TELEGRAM_OTHERS_DIR
                elif hasattr(media, "photo"):
                    media_type = "photo"
                    target_dir = TELEGRAM_PHOTOS_DIR
                else:
                    media_type = "other"
                    target_dir = TELEGRAM_OTHERS_DIR

                status_message = await event.reply(
                    f"开始下载 {media_type} 文件...{filename}"
                )

                try:
                    # 下载文件
                    downloaded_file = await event.message.download_media(
                        file=TELEGRAM_TEMP_DIR,
                        progress_callback=lambda received, total: logger.info(
                            f"下载进度: {filename} {received}/{total} bytes"
                        ),
                    )

                    if downloaded_file:
                        try:
                            os.makedirs(target_dir, exist_ok=True)
                            target_path = os.path.join(
                                target_dir, os.path.basename(downloaded_file)
                            )
                            shutil.move(downloaded_file, target_path)
                            logger.info(f"已将{media_type}文件移动到: {target_path}")
                            await event.reply(
                                f"Telegram {media_type} 文件下载完成！\n"
                                f"保存为: {os.path.basename(target_path)}\n"
                                f"位置: {target_path}"
                            )
                        except Exception as move_error:
                            error_msg = (
                                f"{media_type}文件已下载但移动失败: {str(move_error)}"
                            )
                            logger.error(error_msg)
                            await event.reply(
                                f"Telegram {media_type} 文件下载完成，但移动失败！\n"
                                f"文件名: {os.path.basename(downloaded_file)}\n"
                                f"当前位置: {downloaded_file}\n"
                                f"移动错误: {str(move_error)}"
                            )
                    else:
                        await event.reply("下载失败！文件为空")
                        logger.error("Download failed: Empty file received")

                except Exception as download_error:
                    error_msg = (
                        f"Telegram {media_type} 文件下载失败: {str(download_error)}"
                    )
                    if status_message:
                        await event.reply(error_msg)
                    else:
                        await event.reply(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            error_message = f"处理过程中出现错误: {str(e)}"
            if status_message:
                await event.reply(error_message)
            else:
                await event.reply(error_message)
            logger.error(error_message)


# 配置yt-dlp
def sanitize_filename(s):
    # 移除或替换不安全的字符
    s = re.sub(r'[<>:"/\\|?*]', "_", s)  # 替换Windows不允许的字符
    s = re.sub(r"\s+", " ", s)  # 将多个空格替换为单个空格
    s = s.strip()  # 移除首尾空格
    return s


def find_and_move_youtube_video(video_id, video_title, info):
    """
    在临时目录中查找并移动YouTube视频文件

    Args:
        video_id (str): YouTube视频ID
        video_title (str): 视频标题
        info (dict): 视频信息字典

    Returns:
        tuple: (是否成功, 目标路径或错误信息)
    """
    try:
        # 遍历临时目录
        for file in os.listdir(YOUTUBE_TEMP_DIR):
            # 检查文件名中是否包含视频ID
            if video_id in file and str(file).endswith(info["ext"]):
                source_path = os.path.join(YOUTUBE_TEMP_DIR, file)
                # 确保目标目录存在
                os.makedirs(YOUTUBE_DEST_DIR, exist_ok=True)
                # 构建目标路径
                target_path = os.path.join(
                    YOUTUBE_DEST_DIR, f"{sanitize_filename(video_title)}.{info['ext']}"
                )
                # 移动文件
                shutil.move(source_path, target_path)
                return True, target_path

        return False, f"未找到ID为{video_id}的视频文件"
    except Exception as e:
        return False, f"移动文件时出错: {str(e)}"


async def send_scheduled_message(client, chat_id, message):
    """发送定时消息"""
    try:
        await client.send_message(chat_id, message)
        logger.info(f"成功发送消息到 {chat_id}")
    except Exception as e:
        logger.error(f"发送消息到 {chat_id} 失败: {str(e)}")


def initialize_scheduler(client, scheduled_messages):
    """初始化定时任务"""
    scheduler = AsyncIOScheduler()

    if not scheduled_messages:
        logger.info("没有配置定时消息任务")
        return scheduler

    # 添加所有定时任务
    for idx, task in enumerate(scheduled_messages):
        try:
            chat_id = task.get("chat_id")
            message = task.get("message")
            schedule_time = task.get("time", "08:00")  # 默认早上8点

            if not chat_id or not message:
                logger.warning(f"定时任务 #{idx+1} 缺少必要的参数 (chat_id 或 message)")
                continue

            # 解析时间
            try:
                hour, minute = map(int, schedule_time.split(":"))
            except ValueError:
                logger.error(f"定时任务 #{idx+1} 的时间格式错误: {schedule_time}")
                continue

            # 创建定时任务
            scheduler.add_job(
                send_scheduled_message,
                CronTrigger(hour=hour, minute=minute),
                args=[client, chat_id, message],
                id=f"message_{idx}",
                replace_existing=True,
            )

            logger.info(
                f"已添加定时任务 #{idx+1}: 发送到 {chat_id}, 每天 {schedule_time}"
            )

        except Exception as e:
            logger.error(f"添加定时任务 #{idx+1} 失败: {str(e)}")

    return scheduler


async def main():
    """同时启动机器人和用户账号"""
    try:
        # 加载配置
        global config
        config = load_config()

        # 创建所有必要的目录
        os.makedirs(TELEGRAM_TEMP_DIR, exist_ok=True)
        os.makedirs(YOUTUBE_TEMP_DIR, exist_ok=True)
        os.makedirs(TELEGRAM_VIDEOS_DIR, exist_ok=True)
        os.makedirs(TELEGRAM_AUDIOS_DIR, exist_ok=True)
        os.makedirs(TELEGRAM_PHOTOS_DIR, exist_ok=True)
        os.makedirs(TELEGRAM_OTHERS_DIR, exist_ok=True)
        os.makedirs(YOUTUBE_DEST_DIR, exist_ok=True)

        # 设置日志级别
        logging.getLogger().setLevel(config.get("log_level", "INFO"))

        # 创建客户端列表
        global clients
        clients = []

        # 配置代理
        proxy = None
        proxy_config = config.get("proxy", {})
        if (
            proxy_config.get("enabled")
            and proxy_config.get("host")
            and proxy_config.get("port")
        ):
            proxy = {
                "proxy_type": "socks5",
                "addr": proxy_config["host"],
                "port": proxy_config["port"],
            }

        # 创建并启动用户客户端
        user_config = config.get("user_account", {})
        if user_config.get("enabled", False):
            logger.info("正在启动用户账号客户端...")
            session_name = user_config.get("session_name", "user_session")
            session_path = os.path.join(CONFIG_DIR, session_name)

            user_client = TelegramClient(
                session_path, config["api_id"], config["api_hash"], proxy=proxy
            )
            clients.append(user_client)

            # 启动用户客户端
            phone = user_config.get("phone", "")
            await user_client.start(phone=phone)
            logger.info(f"用户账号 {phone} 登录成功！")

            # 初始化定时任务
            scheduler = initialize_scheduler(
                user_client, config.get("scheduled_messages", [])
            )
            scheduler.start()

        # 创建并启动机器人客户端
        bot_config = config.get("bot_account", {})
        if bot_config.get("token"):
            logger.info("正在启动机器人客户端...")
            session_name = bot_config.get("session_name", "bot_session")
            session_path = os.path.join(CONFIG_DIR, session_name)

            bot_client = TelegramClient(
                session_path, config["api_id"], config["api_hash"], proxy=proxy
            )
            clients.append(bot_client)

            # 启动机器人客户端
            await bot_client.start(bot_token=bot_config["token"])
            logger.info("机器人启动成功！")

            # 为机器人注册下载处理器
            register_handlers(bot_client)

        if not clients:
            raise ValueError("未启用任何客户端，请在配置文件中至少启用一个客户端")

        # 设置信号处理
        loop = asyncio.get_event_loop()

        async def shutdown(signal_=None):
            """优雅关闭"""
            if signal_:
                logger.info(f"收到信号 {signal_.name}...")
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            [task.cancel() for task in tasks]
            logger.info(f"取消 {len(tasks)} 个待处理的任务")
            await asyncio.gather(*tasks, return_exceptions=True)

            # 关闭所有客户端
            for client in clients:
                await client.disconnect()

            # 关闭调度器
            if "scheduler" in locals() and scheduler.running:
                scheduler.shutdown()

            loop.stop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

        # 运行所有客户端
        await asyncio.gather(*[client.run_until_disconnected() for client in clients])

    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        raise
    finally:
        # 确保清理资源
        await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}")
