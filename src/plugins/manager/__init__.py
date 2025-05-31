from nonebot import require
from nonebot.plugin import PluginMetadata

from . import rate

require("src.plugins.config")
__plugin_meta__ = PluginMetadata(
    name="管理插件",
    description="管理器",
    usage="管理器插件",
    type="application",
)

__all__ = ["rate"]
