import unittest
from datetime import date
from unittest.mock import patch

from backend.app.collectors.pdf import OfficialPdfCollector


class TestOfficialPdfCollector(unittest.TestCase):
    @patch.object(OfficialPdfCollector, "fetch_bytes", return_value=b"fake-pdf")
    @patch.object(
        OfficialPdfCollector,
        "extract_text",
        return_value="Edital de concurso\nAnalista Contábil",
    )
    def test_normalizes_pdf_publication(self, _extract, _fetch):
        collector = OfficialPdfCollector(
            "https://example.org/diario.pdf",
            source="DOE-MS",
            publication_date=date(2026, 9, 17),
            identifier="doe-ms:12345",
        )

        result = collector.collect()

        self.assertEqual(result.source, "DOE-MS")
        self.assertEqual(len(result.items), 1)
        item = result.items[0]
        self.assertEqual(item.identificador, "doe-ms:12345")
        self.assertEqual(item.tipo, "diario_oficial_pdf")
        self.assertIn("Analista Contábil", item.conteudo)

    @patch("backend.app.collectors.pdf.PdfReader")
    def test_extracts_text_from_all_pages(self, pdf_reader):
        page_one = type("Page", (), {"extract_text": lambda self: "Página 1"})()
        page_two = type("Page", (), {"extract_text": lambda self: "Página 2"})()
        pdf_reader.return_value.pages = [page_one, page_two]

        text = OfficialPdfCollector.extract_text(b"fake")
        self.assertEqual(text, "Página 1\nPágina 2")


if __name__ == "__main__":
    unittest.main()
