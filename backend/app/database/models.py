"""SQLAlchemy models used by Radar Concurso."""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Concurso(Base):
    __tablename__ = "concursos"
    __table_args__ = (UniqueConstraint("identificador", name="uq_concursos_identificador"),)

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
    data_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
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

    cargos: Mapped[list["Cargo"]] = relationship(back_populates="concurso", cascade="all, delete-orphan")
    publicacoes: Mapped[list["Publicacao"]] = relationship(back_populates="concurso", cascade="all, delete-orphan")


class Cargo(Base):
    __tablename__ = "cargos"
    __table_args__ = (UniqueConstraint("concurso_id", "nome", name="uq_cargo_concurso_nome"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey("concursos.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    escolaridade: Mapped[str | None] = mapped_column(String(255))
    requisitos: Mapped[str | None] = mapped_column(Text)
    vagas: Mapped[int | None] = mapped_column(Integer)
    vagas_ampla: Mapped[int | None] = mapped_column(Integer)
    vagas_cotas: Mapped[int | None] = mapped_column(Integer)
    salario: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    carga_horaria: Mapped[str | None] = mapped_column(String(100))
    cidade: Mapped[str | None] = mapped_column(String(150))
    uf: Mapped[str | None] = mapped_column(String(2))
    observacoes: Mapped[str | None] = mapped_column(Text)

    concurso: Mapped["Concurso"] = relationship(back_populates="cargos")


class Publicacao(Base):
    __tablename__ = "publicacoes"
    __table_args__ = (UniqueConstraint("identificador", name="uq_publicacoes_identificador"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identificador: Mapped[str] = mapped_column(String(128), nullable=False)
    concurso_id: Mapped[int | None] = mapped_column(ForeignKey("concursos.id"))
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    fonte: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text)
    data_publicacao: Mapped[date | None] = mapped_column(Date)
    data_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    hash_conteudo: Mapped[str | None] = mapped_column(String(128))
    tipo: Mapped[str | None] = mapped_column(String(80))

    concurso: Mapped["Concurso | None"] = relationship(back_populates="publicacoes")


def create_database_engine(database_url: str):
    """Create the SQLAlchemy engine for the configured database URL."""
    return create_engine(database_url, future=True)
