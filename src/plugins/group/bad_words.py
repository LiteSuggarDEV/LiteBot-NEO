from base64 import b64decode
from json import load
from pathlib import Path

from nonebot import on_command, on_message, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.matcher import Matcher

require("src.plugins.menu")
require("nonebot_plugin_orm")
from async_lru import alru_cache
from nonebot_plugin_orm import get_session

from litebot_utils.models import get_or_create_group_config
from litebot_utils.rule import is_bot_group_admin, is_event_group_admin
from src.plugins.menu.models import MatcherData


import logging

def load_bad_words() -> list[str]:
    with open(Path(__file__).parent / "badwords.json", encoding="utf-8") as f:
        b64_words: list[str] = load(f)
    data = []
    for word in b64_words:
        try:
            decoded = b64decode(word.encode("utf-8")).decode("utf-8")
            data.append(decoded)
        except Exception as e:
            logging.warning(f"Invalid base64 entry in badwords.json: {word} ({e})")
    data.sort()
    return data


BAD_WORDS = tuple(load_bad_words())

print(f"加载了{len(BAD_WORDS)} 个内置敏感词")


def check_bad_words(text: str) -> bool:
    return any(word in text for word in BAD_WORDS if text)


@alru_cache(1024)
async def is_check_enabled(group_id: int) -> bool:
    async with get_session() as session:
        config, _ = await get_or_create_group_config(group_id)
        session.add(config)
        return config.badwords_check


@on_message(priority=1, block=False).handle()
async def _(event: GroupMessageEvent, bot: Bot, matcher: Matcher):
    group_id = event.group_id
    if event.sender.role != "member":
        return
    if check_bad_words(event.message.extract_plain_text()):
        if not await is_check_enabled():
            return
        self_role = (
            await bot.get_group_member_info(group_id=group_id, user_id=event.self_id)
        )["role"]
        if self_role == "member":
            return
        await bot.delete_msg(message_id=event.message_id)
        matcher.stop_propagation()


@on_command(
    "违禁词检测",
    priority=10,
    block=True,
    state=MatcherData(
        rm_name="违禁词检测",
        rm_usage="/违禁词检测 [开启|关闭]",
        rm_desc="是否开启违禁词检查功能",
    ).model_dump(),
).handle()
async def _(event: GroupMessageEvent, matcher: Matcher, bot: Bot):
    if not await is_event_group_admin(event, bot):
        return
    if not await is_bot_group_admin(event, bot):
        return
    self_role = (
        await bot.get_group_member_info(
            group_id=event.group_id, user_id=event.self_id, no_cache=True
        )
    )["role"]
    group_id = event.group_id
    async with get_session() as session:
        config, _ = await get_or_create_group_config(group_id)
        session.add(config)
        if self_role == "member":
            config.badwords_check = False
            await session.commit()
            await matcher.finish("❌Bot为普通群员")
        if arg := event.message.extract_plain_text().strip():
            match arg:
                case "enable" | "on" | "1" | "yes" | "true" | "启用" | "开启":
                    config.badwords_check = True
                case "disable" | "off" | "0" | "no" | "false" | "禁用" | "关闭":
                    config.badwords_check = False
                case _:
                    await matcher.finish("❌ 请输入on/off")
            is_check_enabled.cache_clear()
            await session.commit()
            await matcher.finish("✔ 已完成操作")
        else:
            await matcher.finish("❌ 请输入on/off")
