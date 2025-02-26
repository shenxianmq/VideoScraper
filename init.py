import os
import yaml
import logging
from telethon import TelegramClient

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 获取程序所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")


def load_config():
    """加载配置文件"""
    config_file = os.path.join(CONFIG_DIR, "config.yaml")

    try:
        if not os.path.exists(config_file):
            raise ValueError(f"配置文件不存在: {config_file}")

        with open(config_file, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        if not config:
            raise ValueError("配置文件为空")

        # 验证必要的配置项
        if not config.get("api_id") or not config.get("api_hash"):
            raise ValueError("请在 config.yaml 中配置 api_id 和 api_hash")

        return config
    except Exception as e:
        logger.error(f"加载配置文件时出错: {str(e)}")
        raise


async def generate_session():
    """生成用户session文件"""
    try:
        # 加载配置
        config = load_config()

        # 获取用户配置
        user_config = config.get("user_account", {})
        if not user_config:
            raise ValueError("配置文件中缺少 user_account 配置")

        phone = user_config.get("phone", "")
        session_name = user_config.get("session_name", "user_session")

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
            logger.info(f"使用代理: {proxy_config['host']}:{proxy_config['port']}")

        # 确保配置目录存在
        os.makedirs(CONFIG_DIR, exist_ok=True)
        session_path = os.path.join(CONFIG_DIR, session_name)

        # 创建客户端
        client = TelegramClient(
            session_path, config["api_id"], config["api_hash"], proxy=proxy
        )

        logger.info("开始生成 session 文件...")
        logger.info("请按照提示输入验证码")

        # 启动客户端
        await client.start(phone=phone)

        # 如果成功连接，打印成功信息
        if await client.is_user_authorized():
            logger.info(f"✅ Session 文件生成成功！")
            logger.info(f"📁 文件保存在: {session_path}.session")
            logger.info("请重新启动容器.")

        # 断开连接
        await client.disconnect()

    except Exception as e:
        logger.error(f"生成 session 文件时出错: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(generate_session())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}")
