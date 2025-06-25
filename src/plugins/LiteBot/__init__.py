from nonebot.plugin import PluginMetadata, require

require("menu")
from . import status

__plugin_meta__ = PluginMetadata(
    name="LiteBot插件",
    description="LiteBot本体相关功能插件",
    usage="LiteBot插件",
    type="application",
)
__all__ = [
    "status",
]
