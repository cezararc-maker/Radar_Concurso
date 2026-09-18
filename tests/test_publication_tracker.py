import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.database.models import Base
from backend.app.services.niche_registry import NicheRegistry
from backend.app.services.publication_tracker import PublicationInput, PublicationTracker


class TestPublicationTracker(unittest.TestCase):
    def test_registers_publication_only_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            niches = root / "niches"
            niches.mkdir()
            (niches / "administrativo.json").write_text(
                '{"id":"administrativo","nome":"Administrativo","ativo":true,"subnichos":[{"id":"contabilidade","nome":"Contabilidade","ativo":true,"palavras_chave":["analista contabil","contador"]}]}',
                encoding="utf-8",
            )
            engine = create_engine(f"sqlite:///{root / 'radar.sqlite3'}")
            Base.metadata.create_all(engine)
            try:
                registry = NicheRegistry(niches)
                item = PublicationInput(
                    titulo="Edital para Analista Contábil",
                    conteudo="Concurso público com vagas para contador.",
                    fonte="Diário Oficial",
                    url="https://example.test/edital/1",
                    data_publicacao=date(2026, 9, 17),
                )
                with Session(engine) as session:
                    tracker = PublicationTracker(session, registry)
                    first = tracker.register(item)
                    session.commit()
                    second = tracker.register(item)
                    self.assertTrue(first.is_new)
                    self.assertFalse(second.is_new)
                    self.assertEqual(first.publication.identificador, second.publication.identificador)
                    self.assertEqual(first.matched_subnicho_ids, ("contabilidade",))
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
