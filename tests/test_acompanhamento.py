import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.database.models import Acompanhamento, Base, Concurso


class TestAcompanhamento(unittest.TestCase):
    def test_concurso_can_be_marked_for_monitoring(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "radar.sqlite3"
            engine = create_engine(f"sqlite:///{database_path}")
            Base.metadata.create_all(engine)

            try:
                with Session(engine) as session:
                    concurso = Concurso(
                        identificador="TESTE-ACOMP-001",
                        titulo="Concurso de Teste",
                    )
                    concurso.acompanhamento = Acompanhamento(
                        ativo=True,
                        notificar_novas_publicacoes=True,
                        notificar_alteracoes_edital=True,
                        notificar_prazos=True,
                        notificar_resultados=True,
                    )
                    session.add(concurso)
                    session.commit()
                    session.refresh(concurso)

                    self.assertIsNotNone(concurso.acompanhamento)
                    self.assertTrue(concurso.acompanhamento.ativo)
                    self.assertTrue(concurso.acompanhamento.notificar_prazos)
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
