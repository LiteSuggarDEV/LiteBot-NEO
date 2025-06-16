from nonebot import on_command
from nonebot.matcher import Matcher

from litebot_utils.utils import generate_info
from src.plugins.menu.manager import CSS_PATH, MatcherData, cached_md_to_pic


@on_command(
    "status",
    aliases={"状态", "info"},
    block=True,
    state=MatcherData(
        rm_name="LiteBot状态查询", rm_usage="info", rm_desc="查询LiteBot的运行状态"
    ).model_dump(),
).handle()
async def status(matcher: Matcher):
    md = generate_info()
    pic = await cached_md_to_pic(md, str(CSS_PATH))
    await matcher.finish(pic)
