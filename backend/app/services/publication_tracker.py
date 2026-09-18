"""Deduplication and classification of collected public notices."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Concurso, Publicacao
from backend.app.services.niche_registry import NicheRegistry


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
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
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


def match_subniches(item: PublicationInput, registry: NicheRegistry) -> tuple[str, ...]:
    """Return active subniches whose keywords occur in the publication text."""
    text = normalize_text(f"{item.titulo} {item.conteudo}")
    matches: list[str] = []
    for subniche_id, keywords in registry.keyword_map().items():
        if any(normalize_text(keyword) in text for keyword in keywords):
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
