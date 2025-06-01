import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from nonebot import logger, require
from nonebot_plugin_localstore import get_config_dir
from pydantic import BaseModel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

require("nonebot_plugin_localstore")

config_dir = get_config_dir("LiteBot")


class Config(BaseModel):
    rate_limit: int = 3
    admins: list[int] = [3196373166]
    notify_group: list[int] = [938229422]


class _ConfigFileChangeHandler(FileSystemEventHandler):
    def __init__(self, manager: "ConfigManager"):
        self.manager = manager

    def on_modified(self, event):
        if event.src_path == str(self.manager.config_path):
            logger.info("检测到配置文件变更，正在自动重载...")
            self.reload_task = asyncio.create_task(self.manager.reload_config())


@dataclass
class ConfigManager:
    config_path: Path = config_dir / "config.json"
    _config: Config = field(default_factory=Config)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _instance: Optional["ConfigManager"] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self._load_config_task = asyncio.create_task(self.load_config())
        self._start_watchdog()

    async def load_config(self) -> None:
        async with self._lock:
            if not self.config_path.exists():
                await self.save_config()
            else:
                content = await asyncio.to_thread(
                    self.config_path.read_text, encoding="utf-8"
                )
                self._config = Config.model_validate(json.loads(content))

    async def reload_config(self) -> Config:
        await self.load_config()
        return self._config

    async def save_config(self) -> None:
        async with self._lock:
            data = json.dumps(self._config.model_dump(), ensure_ascii=False, indent=4)
            await asyncio.to_thread(self.config_path.write_text, data, encoding="utf-8")

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

    def _start_watchdog(self):
        event_handler = _ConfigFileChangeHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.config_path.parent), recursive=False)
        observer.daemon = True
        observer.start()

    @staticmethod
    def _safe_dump(config: Config) -> str:
        config_dict = config.model_dump()
        if "admins" in config_dict:
            config_dict["admins"] = ["***"]
        return json.dumps(config_dict, ensure_ascii=False, indent=2)

    @classmethod
    def instance(cls) -> "ConfigManager":
        if not hasattr(cls, "_singleton_instance") or cls._singleton_instance is None:
            cls._singleton_instance = cls()
        return cls._singleton_instance
