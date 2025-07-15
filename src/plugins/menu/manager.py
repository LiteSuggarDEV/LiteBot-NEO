from dataclasses import dataclass, field

import nonebot
from nonebot import get_driver
from nonebot.log import logger

from .models import MatcherData, PluginData
from .utils import cached_md_to_pic, generate_markdown_menus, get_css_path


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


@get_driver().on_startup
async def load_menus():
    """加载菜单并预渲染图片"""
    menu_mamager.load_menus()
    menu_mamager.print_menus()

    markdown_menus = generate_markdown_menus(menu_mamager.plugins)

    logger.info("开始预渲染菜单图片...")
    for md_str in markdown_menus:
        await cached_md_to_pic(md=md_str, css_path=get_css_path("dark"))
        await cached_md_to_pic(md=md_str, css_path=get_css_path("light"))
    logger.info("菜单图片预渲染完成")
