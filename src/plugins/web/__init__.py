from nonebot.plugin import PluginMetadata

from . import nslookup, send_ping, whois, wping

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
