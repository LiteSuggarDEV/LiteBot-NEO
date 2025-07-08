from enum import IntEnum

from nonebot import require
from sqlalchemy import JSON, BigInteger, Boolean, Text, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Mapped, mapped_column

require("nonebot_plugin_orm")
from nonebot_plugin_orm import Model, get_session


class CaptchaFormat(IntEnum):
    """验证码格式枚举"""

    NUMERIC = 0  # 纯数字
    MIXED = 1  # 字母数字混合
    ALPHA = 2  # 纯字母 (大小写混合)


class SubAdmin(Model):
    """子管理员表"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    __tablename__ = "sub_admin"

    @classmethod
    async def add(cls, group_id: int, user_id: int) -> bool:
        """添加子管理员，返回是否成功（False表示已存在）"""
        async with get_session() as session:
            # 检查是否已存在
            stmt = select(cls).where(cls.group_id == group_id, cls.user_id == user_id)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                return False

            # 添加新的子管理员
            stmt = insert(cls).values(group_id=group_id, user_id=user_id)
            await session.execute(stmt)
            await session.commit()
            return True

    @classmethod
    async def remove(cls, group_id: int, user_id: int) -> bool:
        """移除子管理员，返回是否成功（False表示不存在）"""
        async with get_session() as session:
            stmt = select(cls).where(cls.group_id == group_id, cls.user_id == user_id)
            result = await session.execute(stmt)
            sub_admin = result.scalar_one_or_none()

            if not sub_admin:
                return False

            await session.delete(sub_admin)
            await session.commit()
            return True

    @classmethod
    async def get_list(cls, group_id: int) -> list[int]:
        """获取群组的所有子管理员用户ID列表"""
        async with get_session() as session:
            stmt = select(cls.user_id).where(cls.group_id == group_id)
            result = await session.execute(stmt)
            return [row[0] for row in result.fetchall()]

    @classmethod
    async def exists(cls, group_id: int, user_id: int) -> bool:
        """检查用户是否为群组的子管理员"""
        async with get_session() as session:
            stmt = select(cls).where(cls.group_id == group_id, cls.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    @classmethod
    async def clear(cls, group_id: int) -> int:
        """清空群组的所有子管理员，返回删除的数量"""
        async with get_session() as session:
            stmt = select(cls).where(cls.group_id == group_id)
            result = await session.execute(stmt)
            sub_admins = result.scalars().all()

            count = len(sub_admins)
            for sub_admin in sub_admins:
                await session.delete(sub_admin)

            await session.commit()
            return count


class GroupConfig(Model):
    """群配置"""

    group_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    switch: Mapped[bool] = mapped_column(Boolean, default=True)
    welcome: Mapped[bool] = mapped_column(Boolean, default=False)
    judge: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_recall: Mapped[bool] = mapped_column(Boolean, default=False)
    welcome_message: Mapped[str] = mapped_column(Text(1024), default="欢迎加入群组！")
    nailong: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_spam: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {"limit": 5, "interval": 5, "ban_time": 5, "enable": False},
    )
    anti_link: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_manage_join: Mapped[bool] = mapped_column(Boolean, default=False)
    captcha_timeout: Mapped[int] = mapped_column(BigInteger, default=5)
    captcha_format: Mapped[CaptchaFormat] = mapped_column(
        BigInteger, default=CaptchaFormat.NUMERIC
    )
    captcha_length: Mapped[int] = mapped_column(BigInteger, default=6)

    __tablename__ = "group_config"


async def get_or_create_group_config(group_id: int) -> tuple[GroupConfig, bool]:
    """获取或创建群配置，返回 (config, created)"""
    async with get_session() as session:
        stmt = select(GroupConfig).where(GroupConfig.group_id == group_id)
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            return config, False

        stmt = insert(GroupConfig).values(group_id=group_id)
        await session.execute(stmt)
        await session.commit()

        stmt = select(GroupConfig).where(GroupConfig.group_id == group_id)
        result = await session.execute(stmt)
        config = result.scalar_one()

        return config, True
