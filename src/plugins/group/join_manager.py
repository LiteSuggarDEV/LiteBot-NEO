import contextlib

from nonebot import get_driver, on_command, on_message, on_notice
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    Bot,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_orm import get_session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from litebot_utils.captcha import generate_captcha
from litebot_utils.captcha_manager import captcha_manager
from litebot_utils.event import GroupEvent
from litebot_utils.models import CaptchaFormat, GroupConfig, get_or_create_group_config
from litebot_utils.rule import is_bot_group_admin, is_event_group_admin
from src.plugins.menu.models import MatcherData

pending_cancelable_msg: dict[str, dict[str, str]] = {}


async def captcha(
    bot: Bot, matcher: Matcher, event: GroupEvent, uid: int | None = None
):
    user_id = event.user_id if uid is None else uid
    async with get_session() as session:
        config, _ = await get_or_create_group_config(event.group_id)
        session.add(config)
        if not await is_bot_group_admin(event, bot):
            config.auto_manage_join = False
            await session.commit()
            return
        captcha_length = config.captcha_length
        captcha_format = config.captcha_format
        captcha_timeout = config.captcha_timeout
    captcha_code = generate_captcha(captcha_length, captcha_format)
    sent_msg_id: int = (
        await matcher.send(
            MessageSegment.at(user_id)
            + MessageSegment.text(
                f"⚠️ 请完成以下操作，验证您是真人。\n请在{captcha_timeout}分钟内输入验证码 {captcha_code} ，否则您将被移出聊群\n继续之前，该群需要先检查您的账号安全性。"
            ),
        )
    )["message_id"]
    await captcha_manager.add(
        event.group_id, user_id, captcha_code, bot, captcha_timeout
    )
    pending_cancelable_msg[str(sent_msg_id)] = {
        "group_id": str(event.group_id),
        "user_id": str(user_id),
    }
    matcher.stop_propagation()


@on_command(
    "captcha",
    aliases={"验证"},
    state=MatcherData(
        rm_name="验证特定人",
        rm_desc="验证群内特定成员是否为机器人",
        rm_usage="captcha [@user|<user_id>]",
    ).model_dump(),
).handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot: Bot, args: Message = CommandArg()
):
    if not await is_event_group_admin(event, bot):
        return

    async with get_session() as session:
        config, _ = await get_or_create_group_config(group_id=event.group_id)
        session.add(config)
        if not await is_bot_group_admin(event, bot):
            config.auto_manage_join = False
            await session.commit()
            await matcher.finish("⛔ LiteBot为普通群成员！")
    for segment in args:
        if segment.type == "at":
            uid = int(segment.data["qq"])
            await captcha(bot, matcher, event, uid)
            break
    else:
        await matcher.finish("⚠️ 请at需要验证的人。")


@on_command(
    "set_captcha",
    aliases={"验证码设置"},
    state=MatcherData(
        rm_name="验证码设置",
        rm_desc="入群验证码的配置文件设置(format:0:纯数字 1:字母数字混合 2:纯字母 注：字母均为大小写组合)",
        rm_usage="set_captcha <参数[length|timeout|format]> <值>",
    ).model_dump(),
).handle()
async def set_captcha(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, arg: Message = CommandArg()
):
    if not await is_event_group_admin(event, bot):
        return await matcher.finish("请使用管理员权限执行此命令")
    args = arg.extract_plain_text().strip().split()

    if len(args) < 2:
        format_options = ", ".join(f"{f.value}:{f.name}" for f in CaptchaFormat)
        await matcher.send(
            "⚠️ 请输入参数[length|timeout|format]，以及参数值！\n"
            + "参数length：设置验证码长度，默认为6\n"
            + "参数timeout：设置验证码超时时间，默认为5分钟\n"
            + f"参数format：设置验证码格式，默认为0；可选值：{format_options}\n"
        )
        return

    action: str = args[0]
    value: str = args[1]

    async with get_session() as session:
        config, _ = await get_or_create_group_config(event.group_id)
        session.add(config)
        try:
            match action:
                case "length":
                    if int(value) >= 4 and int(value) <= 10:
                        config.captcha_length = int(value)
                        await session.commit()
                        await matcher.finish(f"✅ 已设置长度为：{value}")
                    else:
                        await matcher.finish("⚠️ 请输入长度(4~10)！")
                case "timeout":
                    if int(value) >= 1 and int(value) <= 30:
                        config.captcha_timeout = int(value)
                        await session.commit()
                        await matcher.finish(f"✅ 已设置超时时间为：{value}")
                    else:
                        await matcher.finish("⚠️ 请输入超时(1~30) 单位：分钟！")
                case "format":
                    if int(value) in {f.value for f in CaptchaFormat}:
                        config.captcha_format = CaptchaFormat(int(value))
                        await session.commit()
                        format_name = CaptchaFormat(int(value)).name
                        await matcher.finish(
                            f"✅ 已设置验证码格式为：{value} ({format_name})"
                        )
                    else:
                        valid_formats = ", ".join(
                            f"{f.value}:{f.name}" for f in CaptchaFormat
                        )
                        await matcher.finish(
                            f"⚠️ 请输入有效的验证码格式！可选值：{valid_formats}"
                        )
        except ValueError:
            await matcher.finish("⚠️ 请输入正确的数字！")


@on_command(
    "入群验证",
    aliases={"robot_fight", "anti_robot"},
    state=MatcherData(
        rm_name="入群验证",
        rm_desc="入群验证",
        rm_usage="入群验证 [开启|关闭]",
    ).model_dump(),
).handle()
async def cmd(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()
) -> None:
    if not await is_event_group_admin(event, bot):
        return

    if arg := args.extract_plain_text().strip().lower():
        async with get_session() as session:
            config, _ = await get_or_create_group_config(event.group_id)
            session.add(config)
            is_enable: bool = False
            if arg in ("启用", "on", "enable", "开启", "yes", "y", "true"):
                if not await is_bot_group_admin(event, bot):
                    config.auto_manage_join = is_enable
                    await session.commit()
                    await matcher.send("⛔ LiteBot为普通群成员，无法开启！")
                    return
                is_enable = True
            elif arg in ("关闭", "off", "disable", "关闭", "no", "n", "false"):
                is_enable = False
            else:
                await matcher.finish("⚠️ 请输入 on/off 来开启或关闭！")
            config.auto_manage_join = is_enable
            await session.commit()
            await matcher.send(
                f"✅ 群组进群验证码已 {'开启' if is_enable else '关闭'} ！"
            )


@on_message(priority=5, block=False).handle()
async def checker(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    config, _ = await get_or_create_group_config(group_id=event.group_id)
    if not config.auto_manage_join:
        return
    if (
        captcha := await captcha_manager.query(event.group_id, event.user_id)
    ) is not None:
        message: str = event.message.extract_plain_text().strip()
        group_name: str = (await bot.get_group_info(group_id=event.group_id))[
            "group_name"
        ]
        if str(captcha) == message:
            await matcher.send(
                MessageSegment.at(event.user_id)
                + MessageSegment.text(f"✅ 验证成功！欢迎加入{group_name}！"),
            )
            async with get_session() as session:
                config, _ = await get_or_create_group_config(event.group_id)
                session.add(config)
                welcome_msg = config.welcome_message
                enable_welcome = config.welcome
            if enable_welcome:
                await matcher.send(welcome_msg)
            await captcha_manager.remove(event.group_id, event.user_id)
            for k in list(pending_cancelable_msg):
                v = pending_cancelable_msg[k]
                if v.get("user_id") == event.get_user_id() and v.get("group_id") == str(
                    event.group_id
                ):
                    await bot.delete_msg(message_id=int(k))
                    del pending_cancelable_msg[k]
                    break
            matcher.stop_propagation()
        elif any(
            isinstance(msg, dict) and msg.get("type") in ["json", "xml", "share"]
            for msg in event.message
        ):
            await bot.delete_msg(message_id=event.message_id)


@on_message(
    priority=10,
    block=False,
    state=MatcherData(
        rm_name="取消验证",
        rm_desc="引用机器人发送的验证消息取消单次验证",
        rm_usage="<REPLY> /skip",
    ).model_dump(),
).handle()
async def handle_cancel(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    if not event.reply:
        return
    if str(event.reply.message_id) not in pending_cancelable_msg:
        return
    if event.message.extract_plain_text().strip() not in (
        f"{prefix}skip" for prefix in get_driver().config.command_start
    ):
        return
    if not await is_event_group_admin(event, bot):
        return
    if (
        await bot.get_group_member_info(user_id=event.self_id, group_id=event.group_id)
    )["role"] == "member":
        return
    with contextlib.suppress(ActionFailed):
        await bot.delete_msg(message_id=event.reply.message_id)
    await captcha_manager.remove(
        event.group_id,
        int(pending_cancelable_msg[str(event.reply.message_id)]["user_id"]),
    )
    del pending_cancelable_msg[str(event.reply.message_id)]

    await matcher.send("⚠️ 已取消该验证！")
    matcher.stop_propagation()


@on_notice(priority=9, block=False).handle()
async def handle_join(bot: Bot, event: GroupIncreaseNoticeEvent, matcher: Matcher):
    if event.user_id == event.self_id:
        return

    try:
        config, _ = await get_or_create_group_config(group_id=event.group_id)
    except IntegrityError:
        async with get_session() as session:
            stmt = select(GroupConfig).where(GroupConfig.group_id == event.group_id)
            result = await session.execute(stmt)
            config = result.scalars().first()

    if not config or not config.auto_manage_join:
        return

    if not await is_bot_group_admin(event, bot):
        return

    await captcha(bot, matcher, event)
