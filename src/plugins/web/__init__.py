from nonebot.plugin import PluginMetadata, require

from . import nslookup, send_ping, whois, wping

require("menu")
__plugin_meta__ = PluginMetadata(
    name="Web功能插件插件",
    description="Web功能插件插件",
    usage="Web功能插件",
    type="application",
)
__all__ = [
    "nslookup",
    "send_ping",
    "whois",
    "wping",
]
