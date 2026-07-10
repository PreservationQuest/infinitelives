from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PathConfig(BaseModel):
    papers: Path = Path("data/input/papers")
    intermediate: Path = Path("data/intermediate")
    processed: Path = Path("data/processed")


class LLMConfig(BaseModel):
    provider: str = "mock"
    model: str = "mock"


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    review: dict[str, Any] = Field(default_factory=lambda: {"low_confidence_threshold": 0.70})


def load_config(path: str | Path = "configs/default.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()
    data = yaml.safe_load(config_path.read_text()) or {}
    return AppConfig.model_validate(data)


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text()) or {}
