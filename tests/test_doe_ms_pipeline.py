import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.collectors.base import CollectorResult
from backend.app.collectors.doe_ms_documents import DoeMsDocumentCollector
from backend.app.database.models import Base
from backend.app.services.collection_pipeline import CollectionPipeline
from backend.app.services.niche_registry import NicheRegistry
from backend.app.services.publication_tracker import PublicationInput, PublicationTracker


class FakeEditionCollector:
    def collect(self):
        return CollectorResult(
            source="Diário Oficial de Mato Grosso do Sul",
            collected_at=date(2026, 9, 17),
            items=(
                PublicationInput(
                    titulo="Diário Oficial Eletrônico n. 12.281",
                    fonte="Diário Oficial de Mato Grosso do Sul",
                    url="https://assets.example/DO12281.pdf",
                    data_publicacao=date(2026, 9, 17),
                    tipo="diario_oficial_edicao",
                    identificador="doe-ms:12281:2026-09-17",
                ),
            ),
        )


class FakePdfCollector:
    def __init__(self, url, *, source, publication_date, identifier):
        self.url = url
        self.source = source
        self.publication_date = publication_date
        self.identifier = identifier

    def collect(self):
        return CollectorResult(
            source=self.source,
            collected_at=self.publication_date,
            items=(
                PublicationInput(
                    titulo=f"{self.source} - Diário Oficial",
                    conteudo="Edital de concurso para Analista Contábil.",
                    fonte=self.source,
                    url=self.url,
                    data_publicacao=self.publication_date,
                    tipo="diario_oficial_pdf",
                    identificador=self.identifier,
                ),
            ),
        )


class TestDoeMsPipeline(unittest.TestCase):
    def test_collects_pdf_classifies_and_deduplicates_publication(self):
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

            engine = create_engine(f"sqlite:///{root / 'radar.sqlite3'}")
            Base.metadata.create_all(engine)
            try:
                registry = NicheRegistry(niches)
                collector = DoeMsDocumentCollector(
                    FakeEditionCollector(),
                    pdf_collector_factory=FakePdfCollector,
                )

                with Session(engine) as session:
                    tracker = PublicationTracker(session, registry)
                    pipeline = CollectionPipeline(collector, tracker)

                    first = pipeline.run()
                    session.commit()
                    second = pipeline.run()

                    self.assertEqual(len(first.tracked_items), 1)
                    self.assertTrue(first.tracked_items[0].is_new)
                    self.assertEqual(
                        first.tracked_items[0].matched_subnicho_ids,
                        ("contabilidade",),
                    )
                    self.assertFalse(second.tracked_items[0].is_new)
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
