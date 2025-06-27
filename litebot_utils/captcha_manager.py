import asyncio
from copy import deepcopy

from nonebot.adapters.onebot.v11 import Bot, MessageSegment


class CaptchaManager:
    def __init__(self):
        self.__data: dict[str, dict[str, str]] = {}
        self.__task_data: dict[str, dict[str, asyncio.Task]] = {}
        self.__lock: asyncio.Lock = asyncio.Lock()

    async def add(self, gid: int, uid: int, captcha: int) -> "CaptchaManager":
        async with self.__lock:
            group_id = str(gid)
            user_id = str(uid)
            if gid not in self.__data:
                self.__data[group_id] = {}
            self.__data[group_id][user_id] = str(captcha)
            return self

    async def remove(self, gid: int, uid: int) -> "CaptchaManager":
        group_id = str(gid)
        user_id = str(uid)
        if group_id in self.__data and user_id in self.__data.get(group_id, {}):
            del self.__data[group_id][user_id]
            await self._cancel_task(gid, uid)
        return self

    async def _cancel_task(self, gid: int, uid: int):
        task = await self._get_task(gid, uid)
        async with self.__lock:
            if task is not None:
                try:
                    task.cancel()
                except Exception:
                    pass
                del self.__task_data[str(gid)][str(uid)]

    async def query(self, gid: int, uid: int) -> str | None:
        async with self.__lock:
            group_id = str(gid)
            user_id = str(uid)
            if group_id in self.__data and user_id in self.__data.get(group_id, {}):
                return self.__data[group_id][user_id]

    async def _get_task(self, gid: int, uid: int) -> asyncio.Task | None:
        async with self.__lock:
            if str(gid) in self.__task_data:
                return self.__task_data[str(gid)].get(str(uid), None)

    async def pending(
        self, gid: int, uid: int, bot: Bot, time: int = 5
    ) -> asyncio.Task:
        async with self.__lock:
            mins = time * 60
            group_id = str(gid)
            user_id = str(uid)
            task = asyncio.create_task(self.__waitter(group_id, user_id, bot, mins))
            if group_id not in self.__task_data:
                self.__task_data[group_id] = {}
            self.__task_data[group_id][user_id] = task
            return task

    async def __waitter(self, gid: str, uid: str, bot: Bot, time: int):
        await asyncio.sleep(time)
        if self.query(int(gid), int(uid)) is not None:
            await bot.send_group_msg(
                group_id=int(gid),
                message=MessageSegment.at(user_id=int(uid))
                + MessageSegment.text("验证已过期！请重新申请验证！"),
            )
            await bot.set_group_kick(
                group_id=int(gid), user_id=int(uid), reject_add_request=False
            )
            await self.remove(int(gid), int(uid))

    @property
    def data(self):
        return deepcopy(self.__task_data)

    @property
    def tasks(self):
        return deepcopy(self.__task_data)


captcha_manager = CaptchaManager()
