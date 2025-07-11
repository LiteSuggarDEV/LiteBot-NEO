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

switch = on_command(
    "switch",
    state=MatcherData(
        rm_name="切换LiteBot启用状态",
        rm_desc="切换LiteBot启用状态",
        rm_usage="switch on/off",
    ).model_dump(),
)


@switch.handle()
async def _(
    event: GroupMessageEvent, matcher: Matcher, bot: Bot, arg: Message = CommandArg()
):
    if not await is_event_group_admin(event, bot):
        await switch.finish("⛔ 你没有权限使用此命令！")
    """开关"""
    # 获取当前群组的开关状态
    group_id = event.group_id
    str_arg = arg.extract_plain_text().strip()

    async with get_session() as session:
        # 使用工具函数获取或创建配置
        config, _ = await get_or_create_group_config(group_id)
        session.add(config)
        if not str_arg:
            await matcher.send(
                f"✅ 该群LiteBot已经 {'开启' if config.switch else '关闭'} ！"
            )
        elif str_arg in ("on", "enable", "开启"):
            config.switch = True
            await session.commit()
            await matcher.finish("✅ 已开启本群LiteBot！")
        elif str_arg in ("off", "disable", "关闭"):
            config.switch = False
            await session.commit()
            await matcher.finish("✅ 已关闭本群LiteBot！")
        else:
            await matcher.finish("⚠️ 请输入正确参数！")
