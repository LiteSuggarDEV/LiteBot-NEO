from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_orm import get_session

from litebot_utils.models import get_or_create_group_config
from litebot_utils.rule import is_event_group_admin
from src.plugins.menu.models import MatcherData


@on_command(
    "set_join_msg",
    aliases={"入群消息"},
    state=dict(
        MatcherData(
            rm_name="设置入群欢迎消息",
            rm_usage="set_join_msg <text>",
            rm_desc="设置入群欢迎消息",
        ),
    ),
).handle()
async def set_join_msg(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()
) -> None:
    if not await is_event_group_admin(event, bot):
        await matcher.finish("⛔ 您没有权限执行此操作")
    async with get_session() as session:
        config, _ = await get_or_create_group_config(event.group_id)
        session.add(config)
        arg = args.extract_plain_text().strip()
        if len(arg) > 512:
            await matcher.finish("⚠️ 消息过长!")
        config.welcome_message = arg
        await session.commit()
        await matcher.finish("✅ 入群消息已设置!")
