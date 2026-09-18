import unittest
from pathlib import Path

from backend.app.services.source_registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "config" / "sources" / "official_sources.json"


class TestSourceRegistry(unittest.TestCase):
    def test_loads_official_sources(self):
        registry = SourceRegistry.from_file(SOURCES)
        enabled = registry.enabled()

        self.assertGreaterEqual(len(enabled), 2)
        self.assertEqual(registry.get("doe-ms")["state"], "MS")
        self.assertEqual(registry.get("diogrande-cg")["city"], "Campo Grande")

    def test_source_ids_are_unique_and_transports_are_supported(self):
        registry = SourceRegistry.from_file(SOURCES)
        ids = [source["id"] for source in registry.all()]

        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(source["transport"] in {"http", "rss", "api", "pdf"} for source in registry.all()))


if __name__ == "__main__":
    unittest.main()
