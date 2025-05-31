from nonebot.plugin import PluginMetadata

from . import manager

__all__ = ["manager"]
__plugin_meta__ = PluginMetadata(
    name="菜单",
    description="菜单功能管理器",
    usage="菜单功能",
    type="application",
)
