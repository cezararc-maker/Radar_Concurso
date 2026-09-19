import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.database.models import Base
from backend.app.services.niche_registry import NicheRegistry
from backend.app.services.publication_tracker import (
    PublicationInput,
    PublicationTracker,
    find_subniche_evidence,
    match_subniches,
)


class TestPublicationTracker(unittest.TestCase):
    def test_registers_publication_only_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            niches = root / "niches"
            niches.mkdir()
            (niches / "administrativo.json").write_text(
                '{"id":"administrativo","nome":"Administrativo","ativo":true,'
                '"subnichos":[{"id":"contabilidade","nome":"Contabilidade",'
                '"ativo":true,"palavras_chave":["analista contabil","contador"]}]}',
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
                    self.assertEqual(
                        first.publication.identificador,
                        second.publication.identificador,
                    )
                    self.assertEqual(
                        first.matched_subnicho_ids,
                        ("contabilidade",),
                    )
            finally:
                engine.dispose()

    def test_requires_contest_context_near_niche_keyword(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            niches = Path(temp_dir) / "niches"
            niches.mkdir()
            (niches / "administrativo.json").write_text(
                '{"id":"administrativo","nome":"Administrativo","ativo":true,'
                '"subnichos":[{"id":"auditoria","nome":"Auditoria",'
                '"ativo":true,"palavras_chave":["auditoria","auditor"]}]}',
                encoding="utf-8",
            )
            registry = NicheRegistry(niches)

            unrelated = PublicationInput(
                titulo="Diário Oficial",
                conteudo="Concurso público. " + ("x" * 1200) + " Auditoria interna anual.",
            )
            relevant = PublicationInput(
                titulo="Edital de concurso",
                conteudo="Vagas para o cargo de Auditor de Controle.",
            )

            self.assertEqual(match_subniches(unrelated, registry), ())
            self.assertEqual(match_subniches(relevant, registry), ("auditoria",))

            evidence = find_subniche_evidence(relevant, registry)
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0].subniche_id, "auditoria")
            self.assertEqual(evidence[0].keyword, "auditor")
            self.assertIn("edital de concurso", evidence[0].excerpt)


if __name__ == "__main__":
    unittest.main()
