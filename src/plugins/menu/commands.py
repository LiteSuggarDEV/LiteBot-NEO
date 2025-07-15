import nonebot
from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.utils import send_forward_msg

from .manager import menu_mamager
from .models import MatcherData
from .utils import (
    PAGE_DIR,
    cached_md_to_pic,
    generate_markdown_menus,
    get_css_path,
)

command_start = get_driver().config.command_start

md_cmd = on_command(
    "md",
    aliases={"markdown"},
    state=MatcherData(
        rm_name="md",
        rm_desc="渲染 Markdown 为图片",
        rm_usage="md <content>",
    ).model_dump(),
)

page_cmd = on_command(
    "page",
    aliases={"页面"},
    state=MatcherData(
        rm_name="page",
        rm_desc="显示自定义页面",
        rm_usage="page <name|list>",
    ).model_dump(),
)


@page_cmd.handle()
async def handle_page(matcher: Matcher, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if not arg:
        await matcher.finish("请输入页面名或 list")

    if arg == "list":
        if pages := [p.stem for p in PAGE_DIR.glob("*.md")]:
            await matcher.finish("可用页面:\n" + "\n".join(pages))
        await matcher.finish("暂无页面")

    page_file = PAGE_DIR / f"{arg}.md"
    if not page_file.exists():
        await matcher.finish("页面不存在")

    md_text = page_file.read_text(encoding="utf-8")
    img = await cached_md_to_pic(md=md_text, css_path=str(get_css_path()))
    await matcher.finish(MessageSegment.image(file=img))


@md_cmd.handle()
async def handle_md(matcher: Matcher, args: Message = CommandArg()):
    md_text = args.extract_plain_text().strip()
    if not md_text:
        await matcher.finish("请输入 Markdown 内容")

    img = await cached_md_to_pic(md=md_text, css_path=str(get_css_path()))
    await matcher.finish(MessageSegment.image(file=img))


@nonebot.on_fullmatch(
    tuple(
        [f"{prefix}menu" for prefix in command_start]
        + [f"{prefix}菜单" for prefix in command_start]
        + [f"{prefix}help" for prefix in command_start]
    ),
    state=MatcherData(
        rm_name="Menu",
        rm_desc="展示菜单",
        rm_usage="menu",
    ).model_dump(),
).handle()
async def show_menu(matcher: Matcher, bot: Bot, event: MessageEvent):
    """显示菜单"""
    if not menu_mamager.plugins:
        await matcher.finish("菜单加载失败，请检查日志")

    markdown_menus = generate_markdown_menus(menu_mamager.plugins)

    if not markdown_menus:
        await matcher.finish("没有可用的菜单")

    markdown_menus_pics = [
        MessageSegment.image(
            file=await cached_md_to_pic(
                md=markdown_menus_string, css_path=get_css_path()
            )
        )
        for markdown_menus_string in markdown_menus
    ] + [
        MessageSegment.text(
            "LiteBot开源地址：https://github.com/LiteSuggarDEV/LiteBot-NEO/"
        )
    ]

    await send_forward_msg(
        bot,
        event,
        name="LiteBot 菜单",
        uin=str(bot.self_id),
        msgs=markdown_menus_pics,
    )
