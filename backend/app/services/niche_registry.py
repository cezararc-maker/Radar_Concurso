"""Registry for enabled niches and subniches."""

from pathlib import Path
from typing import Any
import json


class NicheRegistry:
    """Loads niche definitions from JSON configuration files."""

    def __init__(self, niches_dir: str | Path):
        self.niches_dir = Path(niches_dir)

    def load_all(self) -> list[dict[str, Any]]:
        """Load all valid niche configuration files."""
        if not self.niches_dir.exists():
            return []

        niches: list[dict[str, Any]] = []
        for path in sorted(self.niches_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError(f"Configuração inválida: {path}")
            niches.append(data)
        return niches

    def enabled_niches(self) -> list[dict[str, Any]]:
        """Return only niches marked as active."""
        return [niche for niche in self.load_all() if niche.get("ativo") is True]

    def enabled_subniches(self) -> list[dict[str, Any]]:
        """Return active subniches belonging to active niches."""
        result: list[dict[str, Any]] = []
        for niche in self.enabled_niches():
            for subniche in niche.get("subnichos", []):
                if subniche.get("ativo") is True:
                    result.append({
                        **subniche,
                        "nicho_id": niche.get("id"),
                        "nicho_nome": niche.get("nome"),
                    })
        return result

    def keyword_map(self) -> dict[str, list[str]]:
        """Map each active subniche to its configured keywords."""
        return {
            item["id"]: item.get("palavras_chave", [])
            for item in self.enabled_subniches()
        }
