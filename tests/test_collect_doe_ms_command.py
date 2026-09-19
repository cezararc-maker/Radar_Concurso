import tempfile
import unittest
from datetime import date
from pathlib import Path

from backend.app.collectors.base import CollectorResult
from backend.app.collectors.doe_ms_documents import DoeMsDocumentCollectionReport
from backend.app.services.publication_tracker import PublicationInput
from backend.commands.collect_doe_ms import execute_collection, render_report


class FakeControlledCollector:
    def collect_with_report(self):
        source = "Diário Oficial de Mato Grosso do Sul"
        return DoeMsDocumentCollectionReport(
            result=CollectorResult(
                source=source,
                collected_at=date(2026, 9, 19),
                items=(
                    PublicationInput(
                        titulo=f"{source} - Diário Oficial",
                        conteudo="Edital para Analista Contábil.",
                        fonte=source,
                        url="https://assets.example/DO12281.pdf",
                        data_publicacao=date(2026, 9, 17),
                        tipo="diario_oficial_pdf",
                        identificador="doe-ms:12281:2026-09-17",
                    ),
                ),
            ),
            discovered_count=3,
            attempted_count=1,
            failures=(),
        )


class TestCollectDoeMsCommand(unittest.TestCase):
    def test_duplicate_report_does_not_claim_no_subniches(self):
        collection = FakeControlledCollector().collect_with_report()

        report = render_report(
            collection,
            new_count=0,
            duplicate_count=1,
            matched_subniche_ids=(),
        )

        self.assertIn(
            "Subnichos encontrados: não reavaliado (publicação duplicada)",
            report,
        )

    def test_saves_readable_report_and_registers_publication(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            niches = root / "niches"
            niches.mkdir()
            (niches / "administrativo.json").write_text(
                '{"id":"administrativo","nome":"Administrativo","ativo":true,'
                '"subnichos":[{"id":"contabilidade","nome":"Contabilidade",'
                '"ativo":true,"palavras_chave":["analista contábil"]}]}',
                encoding="utf-8",
            )
            report_path = root / "reports" / "coleta.txt"

            result = execute_collection(
                max_editions=1,
                database_url=f"sqlite:///{root / 'radar.sqlite3'}",
                niches_dir=niches,
                report_path=report_path,
                collector=FakeControlledCollector(),
            )

            self.assertTrue(report_path.exists())
            self.assertTrue(report_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            report = report_path.read_text(encoding="utf-8-sig")
            self.assertIn("RADAR CONCURSO - COLETA DOE-MS", report)
            self.assertIn("Fonte: Diário Oficial de Mato Grosso do Sul", report)
            self.assertIn("Edições encontradas: 3", report)
            self.assertIn("PDFs processados: 1", report)
            self.assertIn("Publicações novas: 1", report)
            self.assertIn("Subnichos encontrados: contabilidade", report)
            self.assertEqual(result.new_count, 1)
            self.assertEqual(result.failure_count, 0)
            self.assertEqual(result.matched_subniche_ids, ("contabilidade",))


if __name__ == "__main__":
    unittest.main()
