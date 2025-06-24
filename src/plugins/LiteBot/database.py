from nonebot import get_driver

from litebot_utils.blacklist.models import GroupBlacklist, PrivateBlacklist
from litebot_utils.config import ConfigManager
from litebot_utils.model_utils import migrate_data
from litebot_utils.models import GroupConfig


@get_driver().on_startup
async def migrate():
    config_manager = ConfigManager.instance()
    if config_manager.config.auto_database_migrate:
        await migrate_data(GroupConfig)
        await migrate_data(GroupBlacklist)
        await migrate_data(PrivateBlacklist)
