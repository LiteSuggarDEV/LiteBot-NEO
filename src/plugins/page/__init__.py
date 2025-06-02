from nonebot import require
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_htmlrender")
require("nonebot_plugin_localstore")

from . import page

__all__ = ["page"]

__plugin_meta__ = PluginMetadata(
    name="自定义页面",
    description="自定义 Markdown 页面渲染",
    usage="page <name|list> 或 md <markdown>",
    type="application",
)
