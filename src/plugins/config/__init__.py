from nonebot.plugin import PluginMetadata

from . import config

__plugin_meta__ = PluginMetadata(
    "配置文件管理插件",
    "配置文件管理插件",
    "管理配置文件",
    "library",
)

__all__ = ["config"]

