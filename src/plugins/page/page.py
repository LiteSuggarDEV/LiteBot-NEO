import base64
from pathlib import Path

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_htmlrender import md_to_pic
from nonebot_plugin_localstore import get_plugin_data_dir

from src.plugins.menu.manager import MatcherData

DIR_PATH = Path(__file__).parent
CSS_PATH = DIR_PATH.parent / "menu" / "dark.css"
PAGE_DIR = get_plugin_data_dir() / "pages"
PAGE_DIR.mkdir(parents=True, exist_ok=True)


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
        pages = [p.stem for p in PAGE_DIR.glob("*.md")]
        if pages:
            await matcher.finish("可用页面:\n" + "\n".join(pages))
        await matcher.finish("暂无页面")

    page_file = PAGE_DIR / f"{arg}.md"
    if not page_file.exists():
        await matcher.finish("页面不存在")

    md_text = page_file.read_text(encoding="utf-8")
    img_bytes = await md_to_pic(md=md_text, css_path=str(CSS_PATH))
    img_b64 = base64.b64encode(img_bytes).decode()
    await matcher.finish(MessageSegment.image(f"base64://{img_b64}"))


md_cmd = on_command(
    "md",
    aliases={"markdown"},
    state=MatcherData(
        rm_name="md",
        rm_desc="渲染 Markdown 为图片",
        rm_usage="md <content>",
    ).model_dump(),
)


@md_cmd.handle()
async def handle_md(matcher: Matcher, args: Message = CommandArg()):
    md_text = args.extract_plain_text().strip()
    if not md_text:
        await matcher.finish("请输入 Markdown 内容")

    img_bytes = await md_to_pic(md=md_text, css_path=str(CSS_PATH))
    img_b64 = base64.b64encode(img_bytes).decode()
    await matcher.finish(MessageSegment.image(f"base64://{img_b64}"))
