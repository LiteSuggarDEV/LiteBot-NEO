from nonebot import require
from nonebot.plugin import PluginMetadata

from . import auto_clean, ban, black, leave, pardon, rate

require("src.plugins.config")
require("src.plugins.menu")

__plugin_meta__ = PluginMetadata(
    name="管理插件",
    description="管理器",
    usage="管理器插件",
    type="application",
)

__all__ = ["auto_clean", "ban", "black", "leave", "pardon", "rate"]
