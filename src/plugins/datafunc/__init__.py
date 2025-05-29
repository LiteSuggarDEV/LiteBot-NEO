from nonebot.plugin import PluginMetadata

from . import base64

__plugin_meta__ = PluginMetadata(
    name="数据插件",
    description="数据处理功能插件",
    usage="数据处理功能插件",
    type="application",
)

__all__ = [
    "base64"
]
