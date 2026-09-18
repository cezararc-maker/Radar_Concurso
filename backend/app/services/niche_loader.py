"""Carregador de nichos e subnichos configurados em JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class NicheLoader:
    """Lê as configurações de nichos sem acoplar regras ao código do coletor."""

    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir

    def load_file(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(f"Configuração inválida: {path}")

        return data

    def load_all(self) -> list[dict[str, Any]]:
        if not self.config_dir.exists():
            return []

        configs: list[dict[str, Any]] = []
        for path in sorted(self.config_dir.glob("*.json")):
            configs.append(self.load_file(path))
        return configs
