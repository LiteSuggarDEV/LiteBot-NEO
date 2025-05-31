import random
import time

from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.matcher import Matcher
from nonebot.rule import to_me

from src.plugins.config.config import config_manager

watch_group = {}
watch_user = {}


@on_message(rule=to_me(), block=False).handle()
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
            else:
                data[id] = time.time()
                return False

    if isinstance(event, GroupMessageEvent):
        ins_id = str(event.group_id)
    else:
        ins_id = str(event.user_id)
    if has_limited(watch_group, ins_id):
        try:
            await matcher.send(random.choice(too_fast_reply))
        except:  # noqa: E722
            pass
        matcher.stop_propagation()
