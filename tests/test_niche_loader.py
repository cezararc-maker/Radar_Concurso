import unittest
from pathlib import Path

from backend.app.services.niche_loader import NicheLoader


class TestNicheLoader(unittest.TestCase):
    def test_load_administrativo(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        config_dir = project_root / "config" / "niches"

        niches = NicheLoader(config_dir).load_all()

        self.assertGreaterEqual(len(niches), 1)
        administrativo = next(item for item in niches if item["id"] == "administrativo")
        self.assertTrue(administrativo["ativo"])
        self.assertGreaterEqual(len(administrativo["subnichos"]), 1)


if __name__ == "__main__":
    unittest.main()
