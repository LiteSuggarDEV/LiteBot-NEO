import base64
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import nonebot
import pydantic
from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot_plugin_htmlrender import md_to_pic
from nonebot_plugin_localstore import get_config_dir

from litebot_utils.utils import send_forward_msg

dir_path = Path(__file__).parent
CSS_PATH = str(dir_path / "dark.css")
PAGE_DIR = get_config_dir("LiteBot") / "pages"
PAGE_DIR.mkdir(parents=True, exist_ok=True)
_md_cache: dict[str, str] = {}


def _hash_md(md: str) -> str:
    return hashlib.sha256(md.encode("utf-8")).hexdigest()


async def cached_md_to_pic(md: str, css_path: str) -> str:
    key = _hash_md(md)
    if key in _md_cache:
        return _md_cache[key]

    # 渲染图片，得到 base64
    base64_img = f"base64://{base64.b64encode(await md_to_pic(md=md, css_path=css_path)).decode()}"

    _md_cache[key] = base64_img
    return base64_img


class MatcherData(pydantic.BaseModel):
    """功能模型"""

    rm_name: str = pydantic.Field(..., description="功能名称")
    rm_usage: str | None = pydantic.Field(default=None, description="功能用法")
    rm_desc: str = pydantic.Field(..., description="功能描述")
    rm_related: str | None = pydantic.Field(description="父级菜单", default=None)


class PluginData:
    """插件模型"""

    metadata: PluginMetadata | None
    matchers: list[MatcherData]
    matcher_grouping: dict[str, list[MatcherData]]

    def __init__(
        self, matchers: list[MatcherData], metadata: PluginMetadata | None = None
    ):
        self.metadata = metadata
        self.matchers = matchers
        self.matcher_grouping = {}

        # 先处理所有顶级菜单（没有rm_related的）
        for matcher in self.matchers:
            if matcher.rm_related is None:
                self.matcher_grouping[matcher.rm_name] = [matcher]

        # 然后处理子菜单（有rm_related的）
        for matcher in self.matchers:
            if matcher.rm_related is not None:
                # 确保父菜单存在
                if matcher.rm_related not in self.matcher_grouping:
                    # 如果父菜单不存在，先创建一个空列表
                    self.matcher_grouping[matcher.rm_related] = []

                found = any(
                    existing_matcher.rm_name == matcher.rm_name
                    for existing_matcher in self.matcher_grouping[matcher.rm_related]
                )
                if not found:
                    self.matcher_grouping[matcher.rm_related].append(matcher)


@dataclass
class MenuManager:
    """菜单管理器"""

    plugins: list[PluginData] = field(default_factory=list)

    def load_menus(self):
        """加载菜单"""
        for plugin in nonebot.get_loaded_plugins():
            matchers = []
            for matcher in plugin.matcher:
                if not matcher._default_state:
                    continue
                matcher_info = MatcherData.model_validate(matcher._default_state)
                logger.debug(f"加载菜单: {matcher_info.model_dump_json(indent=2)}")
                matchers.append(matcher_info)
            self.plugins.append(PluginData(matchers=matchers, metadata=plugin.metadata))
        logger.info("菜单加载完成")

    def print_menus(self):
        """打印菜单（按照matcher_grouping的层级结构）"""
        logger.info("开始打印菜单...")
        logger.info(f"\n{'=' * 40}")

        for plugin in self.plugins:
            # 打印插件信息
            plugin_title = (
                f"插件: {plugin.metadata.name}"
                if plugin.metadata
                else "未命名插件（未读取到元数据）"
            )
            logger.info(plugin_title)
            if plugin.metadata and plugin.metadata.description:
                logger.info(f"描述: {plugin.metadata.description}")

            # 先打印所有顶级菜单（没有rm_related的）
            for group_name, matchers in plugin.matcher_grouping.items():
                # 只处理顶级菜单（组内所有matcher都没有rm_related）
                if all(matcher.rm_related is None for matcher in matchers):
                    for matcher_data in matchers:
                        logger.info(
                            f"  - {matcher_data.rm_name}: {matcher_data.rm_desc}"
                        )
                        if matcher_data.rm_usage:
                            logger.info(
                                f"    └─ 用法:{matcher_data.rm_usage}"
                                if matcher_data.rm_usage != ""
                                else ""
                            )

            # 然后打印有子菜单的顶级菜单
            for group_name, matchers in plugin.matcher_grouping.items():
                # 跳过纯子菜单（组内所有matcher都有rm_related）
                if all(matcher.rm_related is not None for matcher in matchers):
                    continue

                has_submenu = any(
                    any(
                        matcher.rm_related == group_name
                        for matcher in other_matchers
                        if matcher.rm_related is not None
                    )
                    for _, other_matchers in plugin.matcher_grouping.items()
                )
                if has_submenu:
                    # 先打印顶级菜单自己
                    for matcher in matchers:
                        if matcher.rm_related is None:
                            logger.info(f"  - {matcher.rm_name}: {matcher.rm_desc}")
                            if matcher.rm_usage != "":
                                logger.info(
                                    f"    └─ 用法:{matcher.rm_usage}"
                                    if matcher.rm_usage != ""
                                    else ""
                                )

                    # 然后打印子菜单
                    for other_matchers in plugin.matcher_grouping.values():
                        for matcher in other_matchers:
                            if matcher.rm_related == group_name:
                                logger.info(
                                    f"  └─ {matcher.rm_name}: {matcher.rm_desc}"
                                )

                                if matcher.rm_usage != "":
                                    logger.info(
                                        f"      └─ 用法:{matcher.rm_usage}"
                                        if matcher.rm_usage != ""
                                        else ""
                                    )
            logger.info(f"\n{'=' * 40}")
        logger.info("菜单打印完成")


menu_mamager = MenuManager()


def generate_markdown_menus(plugins: list[PluginData]) -> list[str]:
    """生成 Markdown 菜单列表"""
    head = (
        "# LiteBot 菜单\n\n"
        + "> 这是 LiteBot 的菜单列表，包含所有可用的功能和用法。\n\n"
    )
    head += "## 模块列表\n\n"
    for plugin in plugins:
        if not plugin.metadata or not plugin.matcher_grouping:
            continue
        plugin_name = plugin.metadata.name
        plugin_desc = plugin.metadata.description or "无描述"
        head += f"\n\n- **{plugin_name}**: {plugin_desc}"

    markdown_menus: list[str] = [head.strip()]
    for plugin in plugins:
        if not plugin.matcher_grouping or not plugin.metadata:
            continue

        plugin_title = f"## {plugin.metadata.name}\n"
        plugin_description = (
            f"> {plugin.metadata.description}\n\n"
            if plugin.metadata.description
            else ""
        )
        plugin_markdown = plugin_title + plugin_description
        for matchers in plugin.matcher_grouping.values():
            for matcher_data in matchers:
                plugin_markdown += (
                    f"- **{matcher_data.rm_name}**: {matcher_data.rm_desc}"
                )
                if matcher_data.rm_usage:
                    plugin_markdown += f"\n    - 用法: `{matcher_data.rm_usage}`"
                plugin_markdown += "\n\n"
        markdown_menus.append(plugin_markdown.strip())

    return markdown_menus


command_start = get_driver().config.command_start


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
    img = await cached_md_to_pic(md=md_text, css_path=str(CSS_PATH))
    await matcher.finish(MessageSegment.image(file=img))


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

    img = await cached_md_to_pic(md=md_text, css_path=str(CSS_PATH))
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
            file=await cached_md_to_pic(md=markdown_menus_string, css_path=CSS_PATH)
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


@get_driver().on_startup
async def load_menus():
    """加载菜单并预渲染图片"""
    menu_mamager.load_menus()
    menu_mamager.print_menus()

    markdown_menus = generate_markdown_menus(menu_mamager.plugins)

    logger.info("开始预渲染菜单图片...")
    for md_str in markdown_menus:
        await cached_md_to_pic(md=md_str, css_path=CSS_PATH)
    logger.info("菜单图片预渲染完成")
