from nonebot import require
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_htmlrender")

from . import manager

__all__ = ["manager"]
__plugin_meta__ = PluginMetadata(
    name="菜单",
    description="菜单功能管理器",
    usage="菜单功能",
)
