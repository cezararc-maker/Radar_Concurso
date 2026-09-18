import unittest
from unittest.mock import patch

from backend.app.collectors.official import OfficialHttpCollector, OfficialSourceConfig


class TestOfficialCollectors(unittest.TestCase):
    @patch.object(OfficialHttpCollector, "fetch", return_value="<html><title>Edital</title><body>Analista Contábil</body></html>")
    def test_normalizes_official_page(self, _fetch):
        config = OfficialSourceConfig(
            id="doe_ms",
            name="DOE-MS",
            url="https://example.org",
            transport="http",
            parser="official_html",
        )
        result = OfficialHttpCollector(config).collect()
        self.assertEqual(result.source, "DOE-MS")
        self.assertEqual(len(result.items), 1)
        self.assertIn("Analista Contábil", result.items[0].conteudo)
        self.assertEqual(result.items[0].fonte, "DOE-MS")


if __name__ == "__main__":
    unittest.main()
