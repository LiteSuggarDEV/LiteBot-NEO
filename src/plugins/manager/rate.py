import contextlib
import random
from collections import defaultdict

from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.exception import IgnoredException
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor
from nonebot.rule import (
    CommandRule,
    EndswithRule,
    FullmatchRule,
    KeywordsRule,
    RegexRule,
    ShellCommandRule,
    StartswithRule,
)

from litebot_utils.config import ConfigManager
from litebot_utils.token_bucket import TokenBucket

watch_group = defaultdict(
    lambda: TokenBucket(rate=1 / ConfigManager.instance().config.rate_limit, capacity=1)
)
watch_user = defaultdict(
    lambda: TokenBucket(rate=1 / ConfigManager.instance().config.rate_limit, capacity=1)
)


@run_preprocessor
async def run(matcher: Matcher, event: MessageEvent):
    if not any(
        isinstance(
            checker.call,
            FullmatchRule
            | CommandRule
            | StartswithRule
            | EndswithRule
            | KeywordsRule
            | ShellCommandRule
            | RegexRule,
        )
        for checker in matcher.rule.checkers
    ):  # 检查该匹配器是否有文字类匹配类规则
        return

    ins_id = str(
        event.group_id if isinstance(event, GroupMessageEvent) else event.user_id
    )
    data = watch_group if isinstance(event, GroupMessageEvent) else watch_user

    bucket = data[ins_id]
    if not bucket.consume():
        too_fast_reply = (
            "请不要频繁发送请求哦～",
            "请降低请求速度～",
            "请稍后再试哦～",
        )

        with contextlib.suppress(Exception):
            await matcher.send(random.choice(too_fast_reply))
        raise IgnoredException("Too fast!")
