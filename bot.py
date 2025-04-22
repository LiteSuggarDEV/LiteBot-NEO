import asyncio
import os
import sys
from typing import TYPE_CHECKING

import nonebot
from nonebot import get_driver, logger
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import default_format, logger_id

from litebot.utils import send_to_admin

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)


nonebot.load_from_toml("pyproject.toml")

if TYPE_CHECKING:
    # avoid sphinx autodoc resolve annotation failed
    # because loguru module do not have `Logger` class actually
    from loguru import Record

SUPERUSER_list = list(get_driver().config.superusers)


def default_filter(record: "Record"):
    """默认的日志过滤器，根据 `config.log_level` 配置改变日志等级。"""
    log_level = record["extra"].get("nonebot_log_level", "INFO")
    levelno = logger.level(log_level).no if isinstance(log_level, str) else log_level
    return record["level"].no >= levelno


log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 移除 NoneBot 默认的日志处理器
logger.remove(logger_id)
# 添加新的日志处理器
logger.add(
    sys.stdout,
    level=0,
    diagnose=True,
    format=default_format,
    filter=default_filter,
)
logger.add(
    f"{log_dir}/" + "{time}.log",  # 传入函数，每天自动更新日志路径
    level="WARNING",
    format=default_format,
    rotation="00:00",
    retention="7 days",
    encoding="utf-8",
    enqueue=True,
)


class AsyncErrorHandler:
    def write(self, message):
        # message 是一个 loguru 的 Message 对象
        asyncio.create_task(self.process(message))

    async def process(self, message):
        try:
            record = message.record
            if record["level"].name == "ERROR":
                content = record["message"]
                bot = nonebot.get_bot()
                if isinstance(bot, Bot):
                    await send_to_admin(content)
        except Exception as e:
            logger.warning(f"发送群消息失败: {e}")


logger.add(AsyncErrorHandler(), level="ERROR")


if __name__ == "__main__":
    nonebot.run()
