import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect

from backend.app.database.database import initialize_database
from backend.app.database.models import Cargo, Concurso


class TestCargos(unittest.TestCase):
    def test_concurso_accepts_multiple_cargos_with_distinct_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "radar.sqlite3"
            session_factory = initialize_database(f"sqlite:///{db_path}")
            engine = session_factory.kw["bind"]

            try:
                with session_factory() as session:
                    concurso = Concurso(
                        identificador="teste-cargos-001",
                        titulo="Concurso Teste com Cargos",
                        nicho_id="administrativo",
                        subnicho_id="contabilidade",
                        situacao="EDITAL_PUBLICADO",
                        uf="MS",
                    )
                    concurso.cargos = [
                        Cargo(
                            nome="Analista Contábil",
                            escolaridade="Superior",
                            vagas=10,
                            salario=7500,
                            carga_horaria="40h",
                        ),
                        Cargo(
                            nome="Técnico Administrativo",
                            escolaridade="Médio",
                            vagas=30,
                            salario=3200,
                            carga_horaria="40h",
                        ),
                    ]
                    session.add(concurso)
                    session.commit()

                    saved = session.query(Concurso).filter_by(identificador="teste-cargos-001").one()
                    self.assertEqual(len(saved.cargos), 2)
                    self.assertEqual(saved.cargos[0].nome, "Analista Contábil")
                    self.assertEqual(saved.cargos[1].escolaridade, "Médio")
                    self.assertEqual(float(saved.cargos[0].salario), 7500.0)
                    self.assertEqual(saved.cargos[1].vagas, 30)

                tables = inspect(engine).get_table_names()
                self.assertIn("cargos", tables)
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
