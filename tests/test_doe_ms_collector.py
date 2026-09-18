import unittest
from datetime import date
from unittest.mock import patch

from backend.app.collectors.doe_ms import DoeMsCollector

HTML = """
<table>
  <tr><td><a href="https://assets.example/DO12281_17_09_2026.pdf">
    Diário Oficial Eletrônico n. 12.281
  </a></td><td>Data: 17/09/2026</td></tr>
  <tr><td><a href="https://assets.example/DO12280_16_09_2026.pdf">
    Diário Oficial Eletrônico n. 12.280
  </a></td><td>Data: 16/09/2026</td></tr>
  <tr><td><a href="https://assets.example/SUP12281.pdf">
    Suplemento DOE n. 12281 - SAD - Diárias
  </a></td><td>Data: 17/09/2026</td></tr>
</table>
"""


class TestDoeMsCollector(unittest.TestCase):
    def test_discovers_main_and_supplement_editions(self):
        editions = DoeMsCollector.discover_editions(
            HTML, base_url="https://www.diariooficial.ms.gov.br/"
        )
        self.assertEqual(len(editions), 3)
        self.assertEqual(editions[0].issue_number, 12281)
        self.assertEqual(editions[0].publication_date, date(2026, 9, 17))
        self.assertFalse(editions[0].supplement)
        self.assertTrue(editions[2].supplement)

    @patch.object(DoeMsCollector, "fetch", return_value=HTML)
    def test_collect_normalizes_discovered_editions(self, _fetch):
        result = DoeMsCollector().collect()
        self.assertEqual(len(result.items), 3)
        self.assertEqual(result.items[0].tipo, "diario_oficial_edicao")
        self.assertIn("12281", result.items[0].identificador)
        self.assertTrue(result.items[0].url.endswith(".pdf"))


if __name__ == "__main__":
    unittest.main()
