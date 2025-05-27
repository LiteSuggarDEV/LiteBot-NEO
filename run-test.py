import os

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.log import logger as logger

__name__ = "LiteBot CI/CD Test Process"
logger.info("Testing LiteBot...")
nonebot.init()
logger.info("Loading driver...")
driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)

logger.info("Loading plugins...")
try:
    nonebot.load_from_toml("pyproject.toml")
except Exception as e:
    logger.error("OOPS!There is something wrong with loading plugins!")
    logger.opt(exception=True).error("Error!：{}", type(e).__name__)
else:
    logger.info("Done!")
logger.info("Testing pre-startup...")


@driver.on_startup
async def exit_test():
    logger.info("Finished!")
    os._exit(0)


nonebot.run()
