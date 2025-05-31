import json
from pathlib import Path

from nonebot import logger, require

require("nonebot_plugin_localstore")
from nonebot_plugin_localstore import get_data_dir

data_dir = get_data_dir("LiteBot")


class BL_Manager:
    def __init__(self):
        self.__data_dir: Path = data_dir
        self.__group_black_list_path = self.__data_dir / "black_group.json"
        self.__private_black_list_path = self.__data_dir / "black_private.json"
        self.__group_blacklist: dict[str, str] = {}
        self.__private_blacklist: dict[str, str] = {}

    def load(self):
        if not self.__group_black_list_path.exists():
            self.__group_black_list_path.write_text(json.dumps({}))
        if not self.__private_black_list_path.exists():
            self.__private_black_list_path.write_text(json.dumps({}))
        self.__group_blacklist = json.loads(self.__group_black_list_path.read_text())
        self.__private_blacklist = json.loads(
            self.__private_black_list_path.read_text()
        )

    def save_group(self):
        """保存群组黑名单到文件"""
        self.__group_black_list_path.write_text(json.dumps(self.__group_blacklist))
        logger.warning("保存群组黑名单成功")

    def save_private(self):
        """保存私聊黑名单到文件"""
        self.__private_black_list_path.write_text(json.dumps(self.__private_blacklist))
        logger.warning("保存私聊黑名单成功")

    def save_all(self):
        """保存所有黑名单到文件"""
        self.save_group()
        self.save_private()

    def private_append(self, user_id: str, reason: str = "违反使用规则！"):
        """增加一个私聊黑名单

        Args:
            user_id (str): 用户ID
            reason (str, optional): 原因. 默认为 "违反使用规则！".
        """
        self.__private_blacklist[user_id] = reason
        self.save_private()
        logger.info(f"添加黑名单用户：{user_id}")

    def group_append(self, group_id: str, reason: str = "违反使用规则！"):
        """增加一个群组黑名单

        Args:
            group_id (str): 群组ID
            reason (str, optional): 原因. 默认为 "违反使用规则！".
        """
        self.__group_blacklist[group_id] = reason
        self.save_group()
        logger.info(f"添加黑名单群组：{group_id}")

    def reload(self):
        """重新加载黑名单"""
        self.load()
        logger.info("加载黑名单成功")

    def private_remove(self, user_id: str):
        """移除一个私聊黑名单

        Args:
            user_id (str): 用户ID
        """
        if user_id in self.__private_blacklist:
            del self.__private_blacklist[user_id]
            self.save_private()
            logger.info(f"移除黑名单用户：{user_id}")
        else:
            logger.warning(f"用户{user_id}不在黑名单中")

    def group_remove(self, group_id: str):
        """移除一个群组黑名单

        Args:
            group_id (str): 群组ID
        """
        if group_id in self.__group_blacklist:
            del self.__group_blacklist[group_id]
            self.save_group()
            logger.info(f"移除黑名单群组：{group_id}")
        else:
            logger.warning(f"群组{group_id}不在黑名单中")

    def is_private_black(self, user_id: str) -> bool:
        """判断一个用户是否在私聊黑名单中

        Args:
            user_id (str): 用户ID

        Returns:
            bool: 如果在黑名单中则返回True，否则返回False
        """
        return user_id in self.__private_blacklist

    def is_group_black(self, group_id: str) -> bool:
        """判断一个群组是否在群组黑名单中

        Args:
            group_id (str): 群组ID

        Returns:
            bool: 如果在黑名单中则返回True，否则返回False
        """
        return group_id in self.__group_blacklist

    def get_group_blacklist(self) -> dict[str, str]:
        """获取群组黑名单

        Returns:
            dict[str,str]: 返回群组黑名单字典
        """
        return self.__group_blacklist

    def get_private_blacklist(self) -> dict[str, str]:
        """获取私聊黑名单

        Returns:
            dict[str,str]: 私聊黑名单字典
        """
        return self.__private_blacklist

    @property
    def group_blacklist(self) -> dict[str, str]:
        """群组黑名单

        Returns:
            dict[str,str]: 群组黑名单字典
        """
        return self.__group_blacklist

    @property
    def private_blacklist(self) -> dict[str, str]:
        """私聊黑名单

        Returns:
            dict[str,str]: 私聊黑名单字典
        """
        return self.__private_blacklist


bl_manager = BL_Manager()
