import pydantic
from nonebot.plugin import PluginMetadata


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
