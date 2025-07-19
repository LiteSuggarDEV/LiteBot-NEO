"""
群协管管理模块

提供协管权限的添加、删除、查询和列表功能
协管是指没有群管理员权限但可以使用机器人管理功能的用户
"""

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
        rm_usage="subadmin [add|remove|has|list] @[用户]|[用户ID]",
    ).model_dump(),
)


def extract_user_id(arg: Message, arg_list: list[str]) -> int | None:
    """
    从消息中提取用户ID

    Args:
        arg: 命令参数消息
        arg_list: 分割后的参数列表

    Returns:
        用户ID，如果未找到返回None
    """
    for seg in arg:
        if seg.type == "at":
            return int(seg.data["qq"])

    if len(arg_list) >= 2:
        try:
            return int(arg_list[1])
        except ValueError:
            return None

    return None


async def handle_add_subadmin(
    group_id: int, user_id: int, bot: Bot, matcher: Matcher
) -> None:
    """处理添加协管操作"""
    if await check_group_admin(group_id, user_id, bot):
        await matcher.finish("⛔ 该用户已经是群管理员或协管，请勿重复添加！")

    success = await SubAdmin.add(group_id, user_id)
    if success:
        await matcher.finish(f"✅ 已添加 {user_id} 为群组协管！")
    else:
        await matcher.finish("⛔ 该用户已经是协管，请勿重复添加！")


async def handle_remove_subadmin(
    group_id: int, user_id: int, bot: Bot, matcher: Matcher
) -> None:
    """处理删除协管操作"""
    if not await check_group_admin(group_id, user_id, bot):
        await matcher.finish("⛔ 该用户没有管理员权限，无法删除！")

    if await is_sub_admin(group_id, user_id):
        success = await SubAdmin.remove(group_id, user_id)
        if success:
            await matcher.finish(f"✅ 已删除 {user_id} 的协管权限！")
        else:
            await matcher.finish("⛔ 该用户不持有协管权限！")
    else:
        await matcher.finish("⛔ 无法移除该用户管理权限（来自群组赋予）！")


async def handle_query_subadmin(
    group_id: int, user_id: int, bot: Bot, matcher: Matcher
) -> None:
    has_admin = await check_group_admin(group_id, user_id, bot)
    status = "持有" if has_admin else "未持有"
    await matcher.finish(f"该用户{status}管理权限！")


async def handle_list_subadmins(group_id: int, matcher: Matcher) -> None:
    sub_admins = await SubAdmin.get_list(group_id)

    if not sub_admins:
        await matcher.finish("📋 当前群组暂无协管")

    # 格式化协管列表
    admin_list = "\n".join(f"{i}. {admin}" for i, admin in enumerate(sub_admins, 1))
    await matcher.finish(f"📋 当前群组协管列表：\n{admin_list}")


@subadmin.handle()
async def subadmin_handler(
    event: GroupMessageEvent, matcher: Matcher, bot: Bot, arg: Message = CommandArg()
) -> None:
    """
    协管命令主处理函数

    支持的操作：
    - add/set/append: 添加协管
    - remove/delete/del/unset: 删除协管
    - has/query: 查询用户是否有管理权限
    - list: 列出所有协管
    """
    # 权限检查
    if not await is_event_group_admin(event, bot):
        await matcher.finish("⛔ 你没有权限使用此命令！")

    arg_list: list[str] = arg.extract_plain_text().strip().split()

    if not arg_list:
        await matcher.finish("⛔ 请输入操作类型！\n可用操作：add, remove, has, list")

    action = arg_list[0].lower()
    group_id = event.group_id

    match action:
        case "add" | "set" | "append":
            user_id = extract_user_id(arg, arg_list)
            if user_id is None:
                await matcher.finish("⛔ 请指定要添加的用户（@用户 或 输入用户ID）！")

            await handle_add_subadmin(group_id, user_id, bot, matcher)

        case "remove" | "delete" | "del" | "unset":
            user_id = extract_user_id(arg, arg_list)
            if user_id is None:
                await matcher.finish("⛔ 请指定要删除的用户（@用户 或 输入用户ID）！")

            await handle_remove_subadmin(group_id, user_id, bot, matcher)

        case "has" | "query":
            user_id = extract_user_id(arg, arg_list)
            if user_id is None:
                await matcher.finish("⛔ 请指定要查询的用户（@用户 或 输入用户ID）！")

            await handle_query_subadmin(group_id, user_id, bot, matcher)

        case "list":
            await handle_list_subadmins(group_id, matcher)

        case _:
            await matcher.finish(
                "⚠️ 不支持的操作类型！\n"
                "可用操作：\n"
                "• add - 添加协管\n"
                "• remove - 删除协管\n"
                "• has - 查询权限\n"
                "• list - 列出所有协管"
            )
