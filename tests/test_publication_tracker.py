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

    def test_rejects_real_doe_ms_administrative_false_positives(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            niches = Path(temp_dir) / "niches"
            niches.mkdir()
            (niches / "administrativo.json").write_text(
                '{"id":"administrativo","nome":"Administrativo","ativo":true,'
                '"subnichos":['
                '{"id":"fiscal","nome":"Fiscal","ativo":true,'
                '"palavras_chave":["fiscal","auditor fiscal"]},'
                '{"id":"auditoria","nome":"Auditoria","ativo":true,'
                '"palavras_chave":["auditor"]},'
                '{"id":"financas","nome":"Finanças","ativo":true,'
                '"palavras_chave":["financeiro"]},'
                '{"id":"gestao","nome":"Gestão","ativo":true,'
                '"palavras_chave":["gestão"]}'
                ']}',
                encoding="utf-8",
            )
            registry = NicheRegistry(niches)
            excerpts = (
                "ICMS. Falta de emissão de documento fiscal. Prova documental. "
                "Regime de substituição tributária e obrigação acessória.",
                "A dotação relativa aos exercícios financeiros subsequentes "
                "será indicada após aprovação da lei orçamentária.",
                "Reunião na Secretaria de Estado de Governo e Gestão "
                "Estratégica, localizada no Parque dos Poderes.",
                "Na condição de pensionista de ex-servidor da Secretaria de "
                "Estado de Fazenda, que detinha o cargo de Auditor Fiscal da "
                "Receita Estadual, em conformidade com parecer da AGEPREV.",
                "Cônjuge do ex-servidor aposentado no cargo de Técnico de "
                "Serviços Operacionais da Agência Estadual de Gestão de "
                "Empreendimentos, conforme a legislação previdenciária.",
            )

            for excerpt in excerpts:
                with self.subTest(excerpt=excerpt):
                    item = PublicationInput(
                        titulo="Diário Oficial",
                        conteudo=excerpt,
                    )
                    self.assertEqual(match_subniches(item, registry), ())

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

    def test_rejects_real_doe_ms_union_election_false_positive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            niches = Path(temp_dir) / "niches"
            niches.mkdir()
            (niches / "administrativo.json").write_text(
                '{"id":"administrativo","nome":"Administrativo","ativo":true,'
                '"subnichos":[{"id":"fiscal","nome":"Fiscal","ativo":true,'
                '"palavras_chave":["fiscal"]}]}',
                encoding="utf-8",
            )
            registry = NicheRegistry(niches)
            item = PublicationInput(
                titulo="Diário Oficial",
                conteudo=(
                    "torna público, aos filiados, que estarão abertas a partir de "
                    "18.09.2026 as inscrições das chapas concorrentes à eleição da "
                    "nova diretoria executiva e conselho fiscal do SINPAP/MS para o "
                    "quadriênio 2026/2030..."
                ),
            )

            self.assertEqual(match_subniches(item, registry), ())

    def test_keeps_legitimate_contest_when_electoral_terms_are_nearby(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            niches = Path(temp_dir) / "niches"
            niches.mkdir()
            (niches / "administrativo.json").write_text(
                '{"id":"administrativo","nome":"Administrativo","ativo":true,'
                '"subnichos":[{"id":"fiscal","nome":"Fiscal","ativo":true,'
                '"palavras_chave":["fiscal"]}]}',
                encoding="utf-8",
            )
            registry = NicheRegistry(niches)
            item = PublicationInput(
                titulo="Concurso público",
                conteudo=(
                    "O edital de concurso oferece vagas para Auditor Fiscal. "
                    "A comissão eleitoral interna acompanhará apenas a escolha "
                    "de representantes dos servidores."
                ),
            )

            self.assertEqual(match_subniches(item, registry), ("fiscal",))


if __name__ == "__main__":
    unittest.main()
