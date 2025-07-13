from nonebot import logger, require
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError

require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session

from .models import GroupBlacklist, PrivateBlacklist


class BL_Manager:
    async def private_append(self, user_id: str, reason: str = "违反使用规则！"):
        async with get_session() as session:
            stmt = insert(PrivateBlacklist).values(user_id=user_id, reason=reason)
            await session.execute(stmt)
            await session.commit()
        logger.info(f"添加黑名单用户：{user_id}")

    async def group_append(self, group_id: str, reason: str = "违反使用规则！"):
        async with get_session() as session:
            try:
                stmt = insert(GroupBlacklist).values(group_id=group_id, reason=reason)
                await session.execute(stmt)
                await session.commit()
            except IntegrityError:
                logger.warning(f"群组{group_id}已存在")
        logger.info(f"添加黑名单群组：{group_id}")

    async def private_remove(self, user_id: str):
        async with get_session() as session:
            stmt = delete(PrivateBlacklist).where(PrivateBlacklist.user_id == user_id)
            result = await session.execute(stmt)
            await session.commit()
            deleted_count = result.rowcount
            if deleted_count:
                logger.info(f"移除黑名单用户：{user_id}")
            else:
                logger.warning(f"用户{user_id}不在黑名单中")

    async def group_remove(self, group_id: str):
        async with get_session() as session:
            stmt = delete(GroupBlacklist).where(GroupBlacklist.group_id == group_id)
            result = await session.execute(stmt)
            await session.commit()
            deleted_count = result.rowcount
            if deleted_count:
                logger.info(f"移除黑名单群组：{group_id}")
            else:
                logger.warning(f"群组{group_id}不在黑名单中")

    async def is_private_black(self, user_id: str) -> bool:
        async with get_session() as session:
            stmt = (
                select(PrivateBlacklist)
                .where(PrivateBlacklist.user_id == user_id)
                .with_for_update()
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def is_group_black(self, group_id: str) -> bool:
        async with get_session() as session:
            stmt = (
                select(GroupBlacklist)
                .where(GroupBlacklist.group_id == group_id)
                .with_for_update()
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get_private_blacklist(self) -> dict[str, str]:
        async with get_session() as session:
            stmt = select(PrivateBlacklist).with_for_update()
            result = await session.execute(stmt)
            records = result.scalars().all()
            return {record.user_id: record.reason for record in records}

    async def get_group_blacklist(self) -> dict[str, str]:
        async with get_session() as session:
            stmt = select(GroupBlacklist).with_for_update()
            result = await session.execute(stmt)
            records = result.scalars().all()
            return {record.group_id: record.reason for record in records}


bl_manager = BL_Manager()
