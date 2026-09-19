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
    "edital de abertura",
    "edital de concurso",
    "inscricao para",
    "inscricoes",
    "candidato",
    "candidatos",
    "vaga para",
    "vagas para",
    "prova objetiva",
    "prova escrita",
    "certame",
)

UNEQUIVOCAL_CONTEST_CONTEXT_TERMS = (
    "concurso publico",
    "processo seletivo",
    "edital de concurso",
    "certame",
    "prova objetiva",
    "candidatos ao cargo",
)

INCOMPATIBLE_ELECTORAL_CONTEXT_TERMS = (
    "conselho fiscal",
    "eleicao",
    "eleicoes",
    "chapa",
    "chapas",
    "diretoria executiva",
    "filiado",
    "filiados",
    "mandato",
    "quadrienio",
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
class SubnicheMatchEvidence:
    """Keyword and nearby text that justified one subniche match."""

    subniche_id: str
    keyword: str
    excerpt: str


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


def find_subniche_evidence(
    item: PublicationInput,
    registry: NicheRegistry,
    *,
    context_window: int = 220,
    excerpt_radius: int = 180,
) -> tuple[SubnicheMatchEvidence, ...]:
    """Return the first contest-context occurrence for each matched subniche."""
    text = normalize_text(f"{item.titulo} {item.conteudo}")
    evidence: list[SubnicheMatchEvidence] = []

    for subniche_id, keywords in registry.keyword_map().items():
        matched = False
        for configured_keyword in keywords:
            keyword = normalize_text(configured_keyword)
            if not keyword:
                continue

            start = 0
            while True:
                position = text.find(keyword, start)
                if position < 0:
                    break

                context_start = max(0, position - context_window)
                context_end = min(
                    len(text),
                    position + len(keyword) + context_window,
                )
                context = text[context_start:context_end]
                has_contest_context = any(
                    term in context for term in CONTEST_CONTEXT_TERMS
                )
                has_incompatible_electoral_context = any(
                    term in context
                    for term in INCOMPATIBLE_ELECTORAL_CONTEXT_TERMS
                )
                has_unequivocal_contest_context = any(
                    term in context
                    for term in UNEQUIVOCAL_CONTEST_CONTEXT_TERMS
                )
                if (
                    has_contest_context
                    and (
                        not has_incompatible_electoral_context
                        or has_unequivocal_contest_context
                    )
                ):
                    excerpt_start = max(0, position - excerpt_radius)
                    excerpt_end = min(
                        len(text),
                        position + len(keyword) + excerpt_radius,
                    )
                    evidence.append(
                        SubnicheMatchEvidence(
                            subniche_id=subniche_id,
                            keyword=configured_keyword,
                            excerpt=text[excerpt_start:excerpt_end],
                        )
                    )
                    matched = True
                    break

                start = position + max(1, len(keyword))

            if matched:
                break

    return tuple(evidence)


def keyword_has_contest_context(
    text: str,
    keyword: str,
    *,
    context_window: int = 220,
) -> bool:
    """Require a contest term near each niche keyword occurrence."""
    probe = PublicationInput(titulo="", conteudo=text)
    registry = _SingleKeywordRegistry(keyword)
    return bool(
        find_subniche_evidence(
            probe,
            registry,
            context_window=context_window,
        )
    )


class _SingleKeywordRegistry:
    """Small internal adapter retained for the public helper contract."""

    def __init__(self, keyword: str) -> None:
        self.keyword = keyword

    def keyword_map(self) -> dict[str, list[str]]:
        return {"probe": [self.keyword]}


def match_subniches(
    item: PublicationInput,
    registry: NicheRegistry,
) -> tuple[str, ...]:
    """Return subniches supported by a nearby public-contest context."""
    return tuple(
        match.subniche_id
        for match in find_subniche_evidence(item, registry)
    )


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
