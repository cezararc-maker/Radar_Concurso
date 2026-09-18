import json
import tempfile
import unittest
from pathlib import Path

from backend.app.services.niche_registry import NicheRegistry


class TestNicheRegistry(unittest.TestCase):
    def test_only_active_niches_and_subniches_are_returned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "teste.json").write_text(
                json.dumps({
                    "id": "teste",
                    "nome": "Teste",
                    "ativo": True,
                    "subnichos": [
                        {
                            "id": "ativo",
                            "nome": "Ativo",
                            "ativo": True,
                            "palavras_chave": ["palavra"]
                        },
                        {
                            "id": "inativo",
                            "nome": "Inativo",
                            "ativo": False,
                            "palavras_chave": ["ignorar"]
                        }
                    ]
                }),
                encoding="utf-8",
            )

            registry = NicheRegistry(directory)

            self.assertEqual(len(registry.enabled_niches()), 1)
            subniches = registry.enabled_subniches()
            self.assertEqual(len(subniches), 1)
            self.assertEqual(subniches[0]["id"], "ativo")
            self.assertEqual(registry.keyword_map(), {"ativo": ["palavra"]})

    def test_inactive_niche_hides_active_subniches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "teste.json").write_text(
                json.dumps({
                    "id": "teste",
                    "nome": "Teste",
                    "ativo": False,
                    "subnichos": [{
                        "id": "ativo",
                        "nome": "Ativo",
                        "ativo": True,
                        "palavras_chave": ["palavra"]
                    }]
                }),
                encoding="utf-8",
            )

            registry = NicheRegistry(directory)
            self.assertEqual(registry.enabled_niches(), [])
            self.assertEqual(registry.enabled_subniches(), [])
            self.assertEqual(registry.keyword_map(), {})


if __name__ == "__main__":
    unittest.main()
