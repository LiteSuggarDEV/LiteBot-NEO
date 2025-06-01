from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

from litebot_utils.config import ConfigManager
from src.plugins.menu.manager import MatcherData

from .rule import is_admin

clean_groups = on_command(
    "clean_groups",
    rule=is_admin,
    state=MatcherData(
        rm_name="无用群组清理",
        rm_desc="清理人数小于20的无效聊群",
        rm_usage="clean_groups",
    ).model_dump(),
)


@clean_groups.handle()
async def _(bot: Bot, event: MessageEvent):
    await clean_groups.send("开始清理低群人数群组...")
    groups = await bot.get_group_list()
    for group in groups:
        members: set[int] = {
            member["user_id"]
            for member in await bot.get_group_member_list(group_id=group["group_id"])
        }
        admins = set(ConfigManager.instance().config.admins)
        admin_members = members & admins
        if len(admin_members) > 0:
            await clean_groups.send(
                f"群组 {group['group_name']} ({group['group_id']}) 有 {len(admin_members)} 个Bot管理员，跳过"
            )
            continue
        if group["member_count"] < 20:
            await clean_groups.send(
                f"尝试退出群组{group['group_name']}({group['group_id']})....."
            )
            await bot.send_group_msg(
                group_id=group["group_id"],
                message="该群人数小于二十人！Bot将退出该群组。如有疑问请加群1002495699。",
            )
            await bot.set_group_leave(group_id=group["group_id"])
