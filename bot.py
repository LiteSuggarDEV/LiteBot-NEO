import os
import sys
from typing import TYPE_CHECKING

import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.log import default_format, logger_id


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


if TYPE_CHECKING:
    # avoid sphinx autodoc resolve annotation failed
    # because loguru module do not have `Logger` class actually
    from loguru import Record
nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)


nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()
