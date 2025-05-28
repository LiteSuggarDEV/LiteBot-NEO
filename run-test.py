import os

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter

__name__ = "LiteBot CI/CD Test Process"


os.environ["LOG_LEVEL"] = "DEBUG"
logger = nonebot.logger

logger.info("Start testing LiteBot...")
nonebot.init()
logger.info("Loading driver...")
driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)

logger.info("Loading plugins...")
try:
    nonebot.load_from_toml("pyproject.toml")
    logger.info("plugin import done!")

except Exception as e:
    logger.error("OOPS!There is something wrong while loading plugins!")
    logger.opt(exception=True).error("Error!：{}", type(e).__name__)
    exit(1)

logger.info("Testing pre-startup...")


@driver.on_startup
async def exit_test():
    logger.info("Finished!")
    os._exit(0)


try:
    nonebot.run()

except Exception as e:
    logger.error("OOPS!There is something wrong while loading plugins!")
    logger.opt(exception=True).error("Error!：{}", type(e).__name__)
    exit(1)
else:
    logger.info("Done!")
