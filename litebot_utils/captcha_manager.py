import asyncio
from asyncio import Lock, Task

from nonebot.adapters.onebot.v11 import Bot, MessageSegment


class CaptchaManager:
    def __init__(self):
        # 存储验证码数据: {group_id: {user_id: code}}
        self._data: dict[str, dict[str, str]] = {}
        # 存储定时器句柄: {group_id: {user_id: Task}}
        self._tasks: dict[str, dict[str, Task[None]]] = {}
        self.__data_lock: Lock = asyncio.Lock()
        self.__tasks_lock: Lock = asyncio.Lock()

    async def add(
        self, gid: int, uid: int, captcha_code: str, bot: Bot, timeout_minutes: int = 5
    ) -> "CaptchaManager":
        group_id = str(gid)
        user_id = str(uid)

        await self._cancel_handle(gid, uid)

        async with self.__data_lock:
            self._data.setdefault(group_id, {})[user_id] = captcha_code

        delay = timeout_minutes * 60
        task = asyncio.create_task(self._expire(group_id, user_id, bot, delay))
        async with self.__tasks_lock:
            self._tasks.setdefault(group_id, {})[user_id] = task

        return self

    async def remove(self, gid: int, uid: int) -> "CaptchaManager":
        group_id = str(gid)
        user_id = str(uid)

        async with self.__data_lock:
            if group_id in self._data and user_id in self._data[group_id]:
                del self._data[group_id][user_id]
                if not self._data.get(group_id) == {}:
                    del self._data[group_id]
                await self._cancel_handle(gid, uid)

        return self

    async def _cancel_handle(self, gid: int, uid: int):
        group_id = str(gid)
        user_id = str(uid)

        async with self.__tasks_lock:
            handles = self._tasks.get(group_id)
            if not handles:
                return
            if handle := handles.pop(user_id, None):
                try:
                    handle.cancel()
                except Exception:
                    pass
            if not handles:
                self._tasks.pop(group_id, None)

    async def query(self, gid: int, uid: int) -> str | None:
        async with self.__data_lock:
            return self._data.get(str(gid), {}).get(str(uid))

    async def _expire(self, group_id: str, user_id: str, bot: Bot, time: int):
        await asyncio.sleep(time)
        if await self.query(int(group_id), int(user_id)) is not None:
            await bot.send_group_msg(
                group_id=int(group_id),
                message=(
                    MessageSegment.at(user_id=int(user_id))
                    + MessageSegment.text("验证已过期！请重新申请验证！")
                ),
            )
            await bot.set_group_kick(
                group_id=int(group_id), user_id=int(user_id), reject_add_request=False
            )
            await self.remove(int(group_id), int(user_id))


captcha_manager = CaptchaManager()
