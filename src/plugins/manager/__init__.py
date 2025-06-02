from nonebot.plugin import PluginMetadata

from . import add, auto_clean, ban, black, leave, pardon, rate

__plugin_meta__ = PluginMetadata(
    name="管理插件",
    description="管理器",
    usage="管理器插件",
    type="application",
)

__all__ = ["add", "auto_clean", "ban", "black", "leave", "pardon", "rate"]
