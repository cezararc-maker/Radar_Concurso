"""Deduplication and contextual classification of collected public notices."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Concurso, Publicacao
from backend.app.services.niche_registry import NicheRegistry


CONTEST_CONTEXT_TERMS = (
    "concurso",
    "processo seletivo",
    "selecao publica",
    "edital",
    "inscricao",
    "candidato",
    "candidatos",
    "vaga",
    "vagas",
    "prova",
    "certame",
)


@dataclass(frozen=True)
class PublicationInput:
    """Normalized publication data supplied by a collector."""

    titulo: str
    conteudo: str = ""
    fonte: str | None = None
    url: str | None = None
    data_publicacao: date | None = None
    tipo: str | None = None
    identificador: str | None = None
    concurso_id: int | None = None


@dataclass(frozen=True)
class TrackingResult:
    """Result of registering a collected publication."""

    publication: Publicacao
    is_new: bool
    concurso: Concurso | None
    matched_subnicho_ids: tuple[str, ...]


def normalize_text(value: str) -> str:
    """Normalize text for stable comparisons."""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", normalized).strip().lower()


def build_publication_identifier(item: PublicationInput) -> str:
    """Use a source identifier when available, otherwise hash stable fields."""
    if item.identificador:
        return item.identificador.strip()

    payload = "|".join(
        (
            normalize_text(item.titulo),
            normalize_text(item.fonte or ""),
            (item.url or "").strip(),
            item.data_publicacao.isoformat() if item.data_publicacao else "",
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def keyword_has_contest_context(
    text: str,
    keyword: str,
    *,
    context_window: int = 500,
) -> bool:
    """Require a contest term near each niche keyword occurrence."""
    start = 0
    while True:
        position = text.find(keyword, start)
        if position < 0:
            return False

        excerpt_start = max(0, position - context_window)
        excerpt_end = min(len(text), position + len(keyword) + context_window)
        excerpt = text[excerpt_start:excerpt_end]
        if any(term in excerpt for term in CONTEST_CONTEXT_TERMS):
            return True

        start = position + max(1, len(keyword))


def match_subniches(
    item: PublicationInput,
    registry: NicheRegistry,
) -> tuple[str, ...]:
    """Return subniches supported by a nearby public-contest context."""
    text = normalize_text(f"{item.titulo} {item.conteudo}")
    matches: list[str] = []

    for subniche_id, keywords in registry.keyword_map().items():
        normalized_keywords = (
            normalize_text(keyword)
            for keyword in keywords
            if normalize_text(keyword)
        )
        if any(
            keyword_has_contest_context(text, keyword)
            for keyword in normalized_keywords
        ):
            matches.append(subniche_id)

    return tuple(matches)


class PublicationTracker:
    """Register publications exactly once and preserve their source identity."""

    def __init__(self, session: Session, registry: NicheRegistry):
        self.session = session
        self.registry = registry

    def register(self, item: PublicationInput) -> TrackingResult:
        identifier = build_publication_identifier(item)
        existing = self.session.scalar(
            select(Publicacao).where(Publicacao.identificador == identifier)
        )
        if existing is not None:
            concurso = existing.concurso
            return TrackingResult(existing, False, concurso, ())

        concurso = None
        if item.concurso_id is not None:
            concurso = self.session.get(Concurso, item.concurso_id)

        publication = Publicacao(
            identificador=identifier,
            concurso_id=item.concurso_id,
            titulo=item.titulo.strip(),
            fonte=item.fonte,
            url=item.url,
            data_publicacao=item.data_publicacao,
            tipo=item.tipo,
        )
        self.session.add(publication)
        self.session.flush()

        matches = match_subniches(item, self.registry)
        return TrackingResult(publication, True, concurso, matches)
