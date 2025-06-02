from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from litebot_utils.config import ConfigManager

from . import add, auto_clean, ban, black, leave, pardon, rate


@get_driver().on_startup
async def load_config():
    await ConfigManager.instance().load_config()


__plugin_meta__ = PluginMetadata(
    name="管理插件",
    description="管理器",
    usage="管理器插件",
    type="application",
)

__all__ = ["add", "auto_clean", "ban", "black", "leave", "pardon", "rate"]
