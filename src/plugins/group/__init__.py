from nonebot import get_driver, on_message, require
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
)
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata

from litebot_utils.models import get_or_create_group_config

from . import join_manager, kick, mute, notice, recall, subadmin, switch, welcome_switch

require("menu")
require("nonebot_plugin_orm")
__plugin_meta__ = PluginMetadata(
    name="群组插件",
    description="群组管理插件（群管可用）",
    usage="群组插件",
    type="application",
)


__all__ = [
    "join_manager",
    "kick",
    "mute",
    "notice",
    "recall",
    "subadmin",
    "switch",
    "welcome_switch",
]


command_start = get_driver().config.command_start


on_off_checker = on_message(priority=3, block=False)


@on_off_checker.handle()
async def checher(event: GroupMessageEvent, matcher: Matcher):
    config, _ = await get_or_create_group_config(group_id=event.group_id)
    if not config.switch:
        matcher.stop_propagation()
