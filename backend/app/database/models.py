"""SQLAlchemy models used by Radar Concurso."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Concurso(Base):
    __tablename__ = "concursos"
    __table_args__ = (
        UniqueConstraint("identificador", name="uq_concursos_identificador"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identificador: Mapped[str] = mapped_column(String(64), nullable=False)
    orgao: Mapped[str | None] = mapped_column(String(255))
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    nicho_id: Mapped[str | None] = mapped_column(String(100))
    subnicho_id: Mapped[str | None] = mapped_column(String(100))
    situacao: Mapped[str] = mapped_column(String(50), nullable=False, default="PREVISTO")
    cidade: Mapped[str | None] = mapped_column(String(150))
    uf: Mapped[str | None] = mapped_column(String(2))
    data_publicacao: Mapped[date | None] = mapped_column(Date)
    data_coleta: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    descricao: Mapped[str | None] = mapped_column(Text)
    fonte: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text)
    url_edital: Mapped[str | None] = mapped_column(Text)
    hash_conteudo: Mapped[str | None] = mapped_column(String(128))
    vagas: Mapped[int | None] = mapped_column(Integer)
    salario_minimo: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    salario_maximo: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    escolaridade: Mapped[str | None] = mapped_column(String(255))
    inicio_inscricoes: Mapped[date | None] = mapped_column(Date)
    fim_inscricoes: Mapped[date | None] = mapped_column(Date)
    inicio_isencao: Mapped[date | None] = mapped_column(Date)
    fim_isencao: Mapped[date | None] = mapped_column(Date)
    cidade_prova: Mapped[str | None] = mapped_column(String(150))
    uf_prova: Mapped[str | None] = mapped_column(String(2))
    data_prova: Mapped[date | None] = mapped_column(Date)
    status_notificacao: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDENTE")


class Publicacao(Base):
    __tablename__ = "publicacoes"
    __table_args__ = (
        UniqueConstraint("identificador", name="uq_publicacoes_identificador"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identificador: Mapped[str] = mapped_column(String(128), nullable=False)
    concurso_id: Mapped[int | None] = mapped_column(Integer)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    fonte: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text)
    data_publicacao: Mapped[date | None] = mapped_column(Date)
    data_coleta: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    hash_conteudo: Mapped[str | None] = mapped_column(String(128))
    tipo: Mapped[str | None] = mapped_column(String(80))


def create_database_engine(database_url: str):
    """Create the SQLAlchemy engine for the configured database URL."""
    return create_engine(database_url, future=True)
