from nonebot.plugin import PluginMetadata
from nonebot import on_command
from .nslookup import nslookup_runner as ns

on_command("nslookup", aliases={"ns", "nsl"}, priority=10, block=True).append_handler(
    ns
)

__plugin_meta__ = PluginMetadata(
    name="Web功能插件插件",
    description="Web功能插件插件",
    usage="Web功能插件",
    type="application",
)
