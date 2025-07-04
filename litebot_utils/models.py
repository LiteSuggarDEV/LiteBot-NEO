from nonebot import require
from sqlalchemy import JSON, BigInteger, Boolean, Text, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Mapped, mapped_column

require("nonebot_plugin_orm")
from nonebot_plugin_orm import Model, get_session


class GroupConfig(Model):
    """群配置"""

    group_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    switch: Mapped[bool] = mapped_column(Boolean, default=True)
    welcome: Mapped[bool] = mapped_column(Boolean, default=False)
    judge: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_recall: Mapped[bool] = mapped_column(Boolean, default=False)
    welcome_message: Mapped[str] = mapped_column(Text, default="欢迎加入群组！")
    nailong: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_spam: Mapped[dict] = mapped_column(
        JSON, default=lambda: {"limit": 5, "interval": 5, "ban_time": 5, "enable": False}
    )
    anti_link: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_manage_join: Mapped[bool] = mapped_column(Boolean, default=False)
    captcha_timeout: Mapped[int] = mapped_column(BigInteger, default=5)
    captcha_format: Mapped[int] = mapped_column(
        Text, default=0
    )  # 0:纯数字 1:字母数字混合 3:纯字母 注：字母均为大小写组合
    captcha_length: Mapped[int] = mapped_column(BigInteger, default=6)
    sub_admins: Mapped[list[int]] = mapped_column(
        JSON, server_default="[]", nullable=False
    )

    __tablename__ = "group_config"


async def get_or_create_group_config(group_id: int) -> tuple[GroupConfig, bool]:
    """获取或创建群配置，返回 (config, created)"""
    async with get_session() as session:
        stmt = select(GroupConfig).where(GroupConfig.group_id == group_id)
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            return config, False

        stmt = insert(GroupConfig).values(group_id=group_id, sub_admins=[])
        await session.execute(stmt)
        await session.commit()

        stmt = select(GroupConfig).where(GroupConfig.group_id == group_id)
        result = await session.execute(stmt)
        config = result.scalar_one()

        return config, True
