from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_orm import get_session

from litebot_utils.models import get_or_create_group_config
from litebot_utils.rule import is_group_admin, this_is_group_admin
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

    if not len(arg_list) >= 1:
        await matcher.finish("请输入操作！")

    action: str = arg_list[0]
    group_id = event.group_id

    async with get_session() as session:
        try:
            config, _ = await get_or_create_group_config(event.group_id)
            session.add(config)
            if config.sub_admin_list is None:
                config.sub_admin_list = []
            match action:
                case "add" | "set" | "append":
                    for seg in arg:
                        if seg.type == "at":
                            who = int(seg.data["qq"])
                            break
                    else:
                        if len(arg_list) < 2:
                            await matcher.finish("⛔ 请输入要添加的成员！")
                        else:
                            who = int(arg_list[1])

                    if await this_is_group_admin(group_id, who, bot):
                        await matcher.finish(
                            "⛔ 该用户已经持有管理员权限，请勿重复添加！"
                        )
                    else:
                        config.sub_admin_list.append(who)
                        await session.commit()
                        await matcher.finish(f"✅ 已添加 {who} 为群组协管！")
                case "remove" | "delete" | "del" | "unset":
                    for seg in arg:
                        if seg.type == "at":
                            who = int(seg.data["qq"])
                            break
                    else:
                        if len(arg_list) < 2:
                            await matcher.finish("⛔ 请输入要操作的成员！")
                        else:
                            who = int(arg_list[1])
                    if not await this_is_group_admin(group_id, who, bot):
                        await matcher.finish("⛔ 该用户没有管理员权限，无法删除！")
                    elif who in config.sub_admin_list:
                        config.sub_admin_list.remove(who)
                        await session.commit()
                        await matcher.finish(f"✅ 已删除 {who} 的管理权限！")
                    else:
                        await matcher.finish("⛔ 该用户不持有管理权限！")
                case "has" | "query":
                    for seg in arg:
                        if seg.type == "at":
                            who = int(seg.data["qq"])
                            break
                    else:
                        if len(arg_list) < 2:
                            await matcher.finish("⛔ 请输入要操作的成员！")
                        else:
                            who = int(arg_list[1])
                    await matcher.finish(
                        f"该用户{'持有' if await this_is_group_admin(group_id, who, bot) else '未持有'}管理权限！"
                    )
                case "list":
                    await matcher.finish(
                        "当前群组协管列表："
                        + "\n".join(
                            f"{i}. {admin}"
                            for i, admin in enumerate(config.sub_admin_list, 1)
                        )
                    )
                case _:
                    await matcher.finish("⚠️ 请输入正确操作！add/remove/list/has")
        except Exception as e:
            logger.opt(exception=True).exception(str(e))
            await matcher.finish("过程发生了错误，请检查日志以获取详细信息。")
