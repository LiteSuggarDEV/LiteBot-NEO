from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.models import SubAdmin
from litebot_utils.rule import check_group_admin, is_event_group_admin, is_sub_admin
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
    if not await is_event_group_admin(event, bot):
        await matcher.finish("⛔ 你没有权限使用此命令！")
    arg_list: list[str] = arg.extract_plain_text().strip().split()

    if not arg_list:
        await matcher.finish("请输入操作！")

    action: str = arg_list[0]
    group_id = event.group_id

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

            if await check_group_admin(group_id, who, bot):
                await matcher.finish("⛔ 该用户已经是群管理员或协管，请勿重复添加！")
            else:
                success = await SubAdmin.add(group_id, who)
                if success:
                    await matcher.finish(f"✅ 已添加 {who} 为群组协管！")
                else:
                    await matcher.finish("⛔ 该用户已经是协管，请勿重复添加！")
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
            if not await check_group_admin(group_id, who, bot):
                await matcher.finish("⛔ 该用户没有管理员权限，无法删除！")
            elif await is_sub_admin(group_id, who):
                success = await SubAdmin.remove(group_id, who)
                if success:
                    await matcher.finish(f"✅ 已删除 {who} 的管理权限！")
                else:
                    await matcher.finish("⛔ 该用户不持有协管权限！")
            else:
                await matcher.finish("⛔ 无法移除该用户管理权限（来自群组赋予）！")
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
                f"该用户{'持有' if await check_group_admin(group_id, who, bot) else '未持有'}管理权限！"
            )
        case "list":
            sub_admins = await SubAdmin.get_list(group_id)
            if not sub_admins:
                await matcher.finish("当前群组暂无协管")
            else:
                await matcher.finish(
                    "当前群组协管列表："
                    + "\n".join(
                        f"{i}. {admin}" for i, admin in enumerate(sub_admins, 1)
                    )
                )
        case _:
            await matcher.finish("⚠️ 请输入正确操作！add/remove/list/has")
