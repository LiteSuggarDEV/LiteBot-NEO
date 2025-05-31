from nonebot import get_driver

from litebot_utils.config import ConfigManager

config_manager = ConfigManager()

@get_driver().on_startup
async def load_config():
    config_manager.load_config()
