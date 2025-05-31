import contextlib
import random
import time

from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.matcher import Matcher
from nonebot.rule import to_me

from src.plugins.config.config import config_manager

watch_group = {}
watch_user = {}


@on_message(rule=to_me(), block=False, priority=2).handle()
async def run(matcher: Matcher, event: MessageEvent):
    time_diff: int = config_manager.config.rate_limit
    too_fast_reply = (
        "请不要频繁发送请求哦～",
        "请降低请求速度～",
        f"请等待{time_diff}秒再发送哦～",
    )

    def has_limited(data: dict, id: str) -> bool:
        if id not in data:
            data[id] = time.time()
            return False
        else:
            if time.time() - data[id] < time_diff:
                return True
            data[id] = time.time()
            return False

    ins_id = str(event.group_id if isinstance(event, GroupMessageEvent) else event.user_id)
    data = watch_group if isinstance(event, GroupMessageEvent) else watch_user

    if has_limited(data, ins_id):
        with contextlib.suppress(Exception):
            await matcher.send(random.choice(too_fast_reply))
        matcher.stop_propagation()
