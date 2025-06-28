import asyncio

from nonebot.adapters.onebot.v11 import Bot, MessageSegment


class CaptchaManager:
    def __init__(self):
        # 存储验证码数据: {group_id: {user_id: code}}
        self._data: dict[str, dict[str, str]] = {}
        # 存储定时器句柄: {group_id: {user_id: Handle}}
        self._tasks: dict[str, dict[str, asyncio.Handle]] = {}
        self._data_lock = asyncio.Lock()
        self._tasks_lock = asyncio.Lock()
        self._loop = asyncio.get_event_loop()

    async def add(
        self, gid: int, uid: int, captcha_code: int, bot: Bot, timeout_minutes: int = 5
    ) -> "CaptchaManager":
        group_id = str(gid)
        user_id = str(uid)

        await self._cancel_handle(gid, uid)

        async with self._data_lock:
            self._data.setdefault(group_id, {})[user_id] = str(captcha_code)

        delay = timeout_minutes * 60
        handle = self._loop.call_later(
            delay, lambda: asyncio.create_task(self._expire(group_id, user_id, bot))
        )

        async with self._tasks_lock:
            self._tasks.setdefault(group_id, {})[user_id] = handle

        return self

    async def remove(self, gid: int, uid: int) -> "CaptchaManager":
        group_id = str(gid)
        user_id = str(uid)

        async with self._data_lock:
            if group_id in self._data and user_id in self._data[group_id]:
                del self._data[group_id][user_id]
                if not self._data[group_id]:
                    del self._data[group_id]
                await self._cancel_handle(gid, uid)

        return self

    async def _cancel_handle(self, gid: int, uid: int):
        group_id = str(gid)
        user_id = str(uid)

        async with self._tasks_lock:
            handles = self._tasks.get(group_id)
            if not handles:
                return
            if handle := handles.pop(user_id, None):
                handle.cancel()
            if not handles:
                self._tasks.pop(group_id, None)

    async def query(self, gid: int, uid: int) -> str | None:
        return self._data.get(str(gid), {}).get(str(uid))

    async def _expire(self, group_id: str, user_id: str, bot: Bot):
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
