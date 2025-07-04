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
from litebot_utils.rule import is_group_admin, this_is_admin
from src.plugins.menu.models import MatcherData

subadmin = on_command(
    "subadmin",
    state=MatcherData(
        rm_name="协管",
        rm_desc="添加群内的协管权限（赋予没有群管的用户使用LiteBot所有需要群管权限功能的权限）",
        rm_usage="subadmin [set|unset|has|list] @[用户]|[用户ID]",
    ).model_dump(),
)


@subadmin.handle()
async def _(
    event: GroupMessageEvent, matcher: Matcher, bot: Bot, arg: Message = CommandArg()
):
    if not await is_group_admin(event, bot):
        await matcher.finish("⛔ 你没有权限使用此命令！")
    arg_list: list[str] = arg.extract_plain_text().strip().split()
    action: str = arg_list[0]
    if not len(arg_list) > 1:
        try:
            who: int = int(
                next(seg.data["id"] for seg in event.message if seg.type == "at")
            )
        except StopIteration:
            await matcher.finish("⚠️ 请指定要操作的成员。")
    elif arg_list[1].isdigit():
        who: int = int(arg_list[1])
        if not who > 10000:
            await matcher.finish("⚠️ 请输入正确的QQ号！")
    else:
        await matcher.finish("⚠️ 请指定要操作的成员（at或者输入QQ号）。")

    async with get_session() as session:
        config, _ = await get_or_create_group_config(event.group_id)
        session.add(config)
        match action:
            case "add" | "set" | "append":
                if this_is_admin(who):
                    await matcher.finish("⛔ 该用户已经持有管理员权限，请勿重复添加！")
                else:
                    config.sub_admins.append(who)
                    await session.commit()
                    await matcher.finish(f"✅ 已添加 {who} 为群组协管！")
            case "remove" | "delete" | "del" | "unset":
                if not this_is_admin(who):
                    await matcher.finish("⛔ 该用户没有管理员权限，无法删除！")
                elif who in config.sub_admins:
                    config.sub_admins.remove(who)
                    await session.commit()
                    await matcher.finish(f"✅ 已删除 {who} 的管理权限！")
                else:
                    await matcher.finish("⛔ 该用户不持有管理权限！")
            case "has" | "query":
                await matcher.finish(
                    f"该用户{'持有' if await this_is_admin(who) else '未持有'}管理权限！"
                )
            case "list":
                await matcher.finish(
                    "当前群组协管列表："
                    + "\n".join(
                        f"{i}. {admin}" for i, admin in enumerate(config.sub_admins, 1)
                    )
                )
            case _:
                await matcher.finish("⚠️ 请输入正确操作！add/remove/list/has")
