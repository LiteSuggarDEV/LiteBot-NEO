from nonebot import on_command
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="群组插件",
    description="群组插件",
    usage="群组插件",
)


async def a():
    pass


on_command("group", state={"rm_name": "group", "rm_desc": "菜单"}).append_handler(a)
on_command(
    "group_switch",
    state={"rm_name": "group_switch", "rm_desc": "菜单开关", "rm_related": "group"},
).append_handler(a)
on_command(
    "dadadadsada",
    state={"rm_name": "dadadadsada", "rm_desc": "我是一个很乱的东西"},
).append_handler(a)
