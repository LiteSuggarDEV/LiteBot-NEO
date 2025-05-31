from nonebot import logger

from .models import GroupBlacklist, PrivateBlacklist


class BL_Manager:
    async def private_append(self, user_id: str, reason: str = "违反使用规则！"):
        await PrivateBlacklist.update_or_create(
            defaults={"reason": reason}, user_id=user_id
        )
        logger.info(f"添加黑名单用户：{user_id}")

    async def group_append(self, group_id: str, reason: str = "违反使用规则！"):
        await GroupBlacklist.update_or_create(
            defaults={"reason": reason}, group_id=group_id
        )
        logger.info(f"添加黑名单群组：{group_id}")

    async def private_remove(self, user_id: str):
        deleted_count = await PrivateBlacklist.filter(user_id=user_id).delete()
        if deleted_count:
            logger.info(f"移除黑名单用户：{user_id}")
        else:
            logger.warning(f"用户{user_id}不在黑名单中")

    async def group_remove(self, group_id: str):
        deleted_count = await GroupBlacklist.filter(group_id=group_id).delete()
        if deleted_count:
            logger.info(f"移除黑名单群组：{group_id}")
        else:
            logger.warning(f"群组{group_id}不在黑名单中")

    async def is_private_black(self, user_id: str) -> bool:
        return await PrivateBlacklist.filter(user_id=user_id).exists()

    async def is_group_black(self, group_id: str) -> bool:
        return await GroupBlacklist.filter(group_id=group_id).exists()

    async def get_private_blacklist(self) -> dict[str, str]:
        records = await PrivateBlacklist.all()
        return {record.user_id: record.reason for record in records}

    async def get_group_blacklist(self) -> dict[str, str]:
        records = await GroupBlacklist.all()
        return {record.group_id: record.reason for record in records}


bl_manager = BL_Manager()
