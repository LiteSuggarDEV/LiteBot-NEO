import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import aiofiles
import yaml
from nonebot import logger, require
from watchfiles import awatch

require("nonebot_plugin_localstore")
from nonebot_plugin_localstore import get_config_dir
from pydantic import BaseModel

config_dir = get_config_dir("LiteBot")


class Config(BaseModel):
    rate_limit: int = 3
    auto_database_migrate: bool = True
    admins: list[int] = [3196373166]
    notify_group: list[int] = [938229422]


@dataclass
class ConfigManager:
    config_path: Path = config_dir / "config.yaml"
    _config: Config = field(default_factory=Config)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _instance: Optional["ConfigManager"] = field(default=None, init=False, repr=False)
    _watch_task: asyncio.Task | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_config_sync()
        self._watch_task = asyncio.create_task(self._watch_config())

    def _load_config_sync(self) -> None:
        logger.info(f"正在加载配置文件: {self.config_path}")
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as f:
                self._config = Config.model_validate(yaml.safe_load(f) or {})
        else:
            self._save_config_sync()

    def _save_config_sync(self) -> None:
        with self.config_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(self._config.model_dump(), f, allow_unicode=True)

    async def _watch_config(self) -> None:
        async for changes in awatch(self.config_path):
            if any(path == str(self.config_path) for _, path in changes):
                logger.info("检测到配置文件变更，正在自动重载...")
                try:
                    await self.reload_config()
                except Exception as e:
                    logger.opt(exception=e).warning("配置文件重载失败")

    async def load_config(self) -> None:
        async with self._lock:
            if not self.config_path.exists():
                await self.save_config()
            else:
                async with aiofiles.open(self.config_path, encoding="utf-8") as f:
                    content = await f.read()
                self._config = Config.model_validate(yaml.safe_load(content) or {})

    async def reload_config(self) -> Config:
        await self.load_config()
        logger.info("配置文件已重新加载")
        return self._config

    async def save_config(self) -> None:
        async with self._lock:
            data = yaml.safe_dump(self._config.model_dump(), allow_unicode=True)
            async with aiofiles.open(self.config_path, "w", encoding="utf-8") as f:
                await f.write(data)

    async def override_config(self, config: Config) -> None:
        safe_old = self._safe_dump(self._config)
        safe_new = self._safe_dump(config)
        logger.warning(
            "正在覆写配置文件!\n原始值:\n%s\n修改后:\n%s", safe_old, safe_new
        )

        async with self._lock:
            self._config = Config.model_validate(config)
            await self.save_config()

    def get_config(self) -> Config:
        return self._config

    @property
    def config(self) -> Config:
        return self._config

    @staticmethod
    def _safe_dump(config: Config) -> str:
        config_dict = config.model_dump()
        if "admins" in config_dict:
            config_dict["admins"] = ["***"]
        return yaml.safe_dump(config_dict, allow_unicode=True)

    @classmethod
    def instance(cls) -> "ConfigManager":
        if not hasattr(cls, "_singleton_instance") or cls._singleton_instance is None:
            cls._singleton_instance = cls()
        return cls._singleton_instance
