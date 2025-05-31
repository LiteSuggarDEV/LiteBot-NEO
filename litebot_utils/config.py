import json
from dataclasses import dataclass, field
from pathlib import Path

from nonebot import logger
from nonebot_plugin_localstore import get_config_dir
from pydantic import BaseModel

# !!! 这里仅提供配置文件工厂 !!! 如果获取配置文件请通过 src.plugins.config.config获取ConfigManager实例 !!!

config_dir = get_config_dir("LiteBot")


class Config(BaseModel):
    """
    插件配置
    """

    # 上一条请求后需要等待的时间 ，单位秒
    rate_limit: int = 3


@dataclass
class ConfigManager:
    cofig_path: Path = config_dir / "config.json"
    _config: Config = field(default_factory=Config)

    def load_config(self):
        """加载配置文件"""
        if not self.cofig_path.exists():
            self.cofig_path.write_text(json.dumps(Config().model_dump()))
        self._config = Config.model_validate(json.loads(self.cofig_path.read_text()))

    def reload_config(self) -> Config:
        """重载配置文件（可能是为了好看？（划掉））

        Returns:
            Config: 配置文件
        """
        self.load_config()
        return self.config

    def save_config(self):
        """保存配置文件"""
        self.cofig_path.write_text(json.dumps(self.config.model_dump()))

    def override_config(self, config: Config):
        """覆写配置文件

        Args:
            config (Config): Config类
        """
        logger.warning(
            f"正在覆写配置文件!原始值：{self.config.model_dump_json()}，修改后值：{config.model_dump_json()}。"
        )
        self._config = Config.model_validate(config)
        self.save_config()

    # 此处设计是为了防止config被随意修改，直接修改config并非最佳实践。
    @property
    def config(self) -> Config:
        return self._config
