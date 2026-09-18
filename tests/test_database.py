import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect

from backend.app.database.database import initialize_database
from backend.app.database.models import Concurso, Publicacao


class TestDatabase(unittest.TestCase):
    def test_initialize_creates_tables_and_accepts_concurso(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "radar.sqlite3"
            session_factory = initialize_database(f"sqlite:///{db_path}")

            with session_factory() as session:
                concurso = Concurso(
                    identificador="teste-concurso-001",
                    titulo="Concurso Teste",
                    nicho_id="administrativo",
                    subnicho_id="contabilidade",
                    situacao="EDITAL_PUBLICADO",
                    uf="MS",
                    salario_minimo=3000,
                    salario_maximo=8000,
                    inicio_inscricoes=None,
                    fim_inscricoes=None,
                )
                session.add(concurso)
                session.commit()

                saved = session.query(Concurso).filter_by(identificador="teste-concurso-001").one()
                self.assertEqual(saved.titulo, "Concurso Teste")
                self.assertEqual(saved.salario_maximo, 8000)

            engine = session_factory.kw["bind"]
            tables = inspect(engine).get_table_names()
            self.assertIn("concursos", tables)
            self.assertIn("publicacoes", tables)


if __name__ == "__main__":
    unittest.main()
