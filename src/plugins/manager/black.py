from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.matcher import Matcher

from litebot_utils.blacklist.black import bl_manager
from litebot_utils.utils import send_to_admin


@on_message(block=False, priority=1).handle()
async def handle_message(event: MessageEvent, matcher: Matcher, bot: Bot):
    if isinstance(event, GroupMessageEvent) and await bl_manager.is_group_black(
        str(event.group_id)
    ):
        await send_to_admin(f"尝试退出黑名单群组{event.group_id}.......")
        await bot.set_group_leave(group_id=event.group_id)
    if await bl_manager.is_private_black(str(event.user_id)):
        matcher.stop_propagation()
