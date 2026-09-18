"""Load and validate official source definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SourceRegistryError(ValueError):
    """Raised when the source registry is invalid."""


class SourceRegistry:
    REQUIRED_FIELDS = {"id", "name", "scope", "url", "enabled", "priority", "transport", "parser"}

    def __init__(self, sources: list[dict[str, Any]]):
        self._sources = tuple(sources)
        self._validate()

    @classmethod
    def from_file(cls, path: str | Path) -> "SourceRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
            raise SourceRegistryError("O arquivo de fontes deve conter uma lista 'sources'.")
        return cls(payload["sources"])

    def _validate(self) -> None:
        ids: set[str] = set()
        for source in self._sources:
            missing = self.REQUIRED_FIELDS - source.keys()
            if missing:
                raise SourceRegistryError(f"Fonte sem campos obrigatórios: {sorted(missing)}")
            if source["id"] in ids:
                raise SourceRegistryError(f"ID de fonte duplicado: {source['id']}")
            ids.add(source["id"])
            if source["transport"] not in {"http", "rss", "api", "pdf"}:
                raise SourceRegistryError(f"Transporte não suportado: {source['transport']}")
            if not isinstance(source["enabled"], bool):
                raise SourceRegistryError(f"enabled inválido para {source['id']}")

    def all(self) -> tuple[dict[str, Any], ...]:
        return self._sources

    def enabled(self) -> tuple[dict[str, Any], ...]:
        return tuple(source for source in self._sources if source["enabled"])

    def get(self, source_id: str) -> dict[str, Any]:
        for source in self._sources:
            if source["id"] == source_id:
                return source
        raise KeyError(source_id)
