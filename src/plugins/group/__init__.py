from nonebot import get_driver, on_message, require
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
)
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata

from litebot_utils.models import get_or_create_group_config

require("menu")
require("nonebot_plugin_orm")

from nonebot_plugin_orm import get_session

from . import (
    bad_words,
    join_manager,
    join_msg,
    kick,
    mute,
    notice,
    recall,
    subadmin,
    switch,
    welcome_switch,
)

__plugin_meta__ = PluginMetadata(
    name="群组插件",
    description="群组管理插件（群管可用）",
    usage="群组插件",
    type="application",
)


__all__ = [
    "bad_words",
    "join_manager",
    "join_msg",
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
    async with get_session() as session:
        config, _ = await get_or_create_group_config(event.group_id)
        session.add(config)
        if not config.switch:
            matcher.stop_propagation()
