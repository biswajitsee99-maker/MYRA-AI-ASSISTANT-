"""Configuration helpers for the MYRA assistant."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path.home() / ".myra" / "config.json"


@dataclass
class AppConfig:
    name: str = "MYRA"
    wake_word: str = "MYRA"
    voice_enabled: bool = True
    ai_enabled: bool = True
    automation_enabled: bool = True
    screen_reading_enabled: bool = True
    model: str = "default"
    theme: str = "futuristic"
    memory: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppConfig()

    return AppConfig(**{**AppConfig().__dict__, **data})


def save_config(config: AppConfig, path: str | Path = DEFAULT_CONFIG_PATH) -> Path:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config.as_dict(), indent=2), encoding="utf-8")
    return config_path
