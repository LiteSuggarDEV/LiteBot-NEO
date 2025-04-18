from dataclasses import dataclass, field

import nonebot
import pydantic
from nonebot.log import logger
from nonebot.plugin import PluginMetadata


class MatcherData(pydantic.BaseModel):
    """功能模型"""

    rm_name: str = pydantic.Field(..., description="功能名称")
    rm_desc: str = pydantic.Field(..., description="功能描述")
    rm_related: str | None = pydantic.Field(None, description="父级菜单")


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
                    for existing_matcher in self.matcher_grouping[
                        matcher.rm_related
                    ]
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
                matcher_info = MatcherData.model_validate(matcher._default_state)
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
                f"插件: {plugin.metadata.name}" if plugin.metadata else "未命名插件"
            )
            logger.info(plugin_title)
            if plugin.metadata and plugin.metadata.description:
                logger.info(f"描述: {plugin.metadata.description}")

            # 先打印所有顶级菜单（没有rm_related的）
            for group_name, matchers in plugin.matcher_grouping.items():
                # 只处理顶级菜单（组内所有matcher都没有rm_related）
                if all(matcher.rm_related is None for matcher in matchers):
                    for matcher in matchers:
                        logger.info(f"  - {matcher.rm_name}: {matcher.rm_desc}")

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

                    # 然后打印子菜单
                    for other_group, other_matchers in plugin.matcher_grouping.items():
                        for matcher in other_matchers:
                            if matcher.rm_related == group_name:
                                logger.info(
                                    f"  └─ {matcher.rm_name}: {matcher.rm_desc}"
                                )
            logger.info(f"\n{'=' * 40}")
        logger.info("\n菜单打印完成")


menu_mamager = MenuManager()

driver = nonebot.get_driver()


@driver.on_startup
async def load_menus():
    """加载菜单"""
    menu_mamager.load_menus()
    menu_mamager.print_menus()
