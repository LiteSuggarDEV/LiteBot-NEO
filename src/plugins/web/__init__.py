from nonebot import on_command
from nonebot.plugin import PluginMetadata

from .nslookup import nslookup_runner as ns

__plugin_meta__ = PluginMetadata(
    name="Web功能插件插件",
    description="Web功能插件插件",
    usage="Web功能插件",
    type="application",
)
__all__ = ["nslookup"]
