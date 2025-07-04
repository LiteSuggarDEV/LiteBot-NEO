from nonebot.plugin import PluginMetadata

from . import add, auto_clean, ban, black, leave, list_black, pardon, rate

__plugin_meta__ = PluginMetadata(
    name="机器人管理插件",
    description="管理器（TO超级管理员：您的每一个操作都会让用户发出尖锐的爆鸣声）",
    usage="管理器插件",
    type="application",
)

__all__ = [
    "add",
    "auto_clean",
    "ban",
    "black",
    "leave",
    "list_black",
    "pardon",
    "rate",
]
