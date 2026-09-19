"""Run one controlled DOE-MS collection and save a readable report."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

from backend.app.collectors.doe_ms_documents import (
    DoeMsDocumentCollectionReport,
    DoeMsDocumentCollector,
)
from backend.app.config.settings import DATABASE_URL, NICHE_CONFIG_DIR, PROJECT_ROOT
from backend.app.database.database import initialize_database
from backend.app.services.niche_registry import NicheRegistry
from backend.app.services.publication_tracker import (
    PublicationTracker,
    SubnicheMatchEvidence,
    find_subniche_evidence,
)


@dataclass(frozen=True)
class DoeMsCommandResult:
    """Summary returned by a controlled command execution."""

    report_path: Path
    discovered_count: int
    attempted_count: int
    processed_count: int
    failure_count: int
    new_count: int
    duplicate_count: int
    matched_subniche_ids: tuple[str, ...]
    match_evidence: tuple[SubnicheMatchEvidence, ...]


def render_report(
    collection: DoeMsDocumentCollectionReport,
    *,
    new_count: int,
    duplicate_count: int,
    matched_subniche_ids: tuple[str, ...],
    match_evidence: tuple[SubnicheMatchEvidence, ...] = (),
) -> str:
    if matched_subniche_ids:
        subniche_summary = ", ".join(matched_subniche_ids)
    elif duplicate_count and not new_count:
        subniche_summary = "não reavaliado (publicação duplicada)"
    else:
        subniche_summary = "nenhum"

    lines = [
        "RADAR CONCURSO - COLETA DOE-MS",
        "=" * 40,
        f"Executado em: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Fonte: {collection.result.source}",
        f"Edições encontradas: {collection.discovered_count}",
        f"Edições tentadas: {collection.attempted_count}",
        f"PDFs processados: {len(collection.result.items)}",
        f"Falhas: {len(collection.failures)}",
        f"Publicações novas: {new_count}",
        f"Publicações duplicadas: {duplicate_count}",
        f"Subnichos encontrados: {subniche_summary}",
    ]

    if match_evidence:
        lines.extend(("", "EVIDÊNCIAS DE CLASSIFICAÇÃO", "-" * 40))
        for evidence in match_evidence:
            lines.extend(
                (
                    f"Subnicho: {evidence.subniche_id}",
                    f"Palavra-chave: {evidence.keyword}",
                    f"Trecho: {evidence.excerpt}",
                    "",
                )
            )

    if collection.failures:
        lines.extend(("", "FALHAS", "-" * 40))
        for failure in collection.failures:
            lines.extend(
                (
                    f"Identificador: {failure.identifier or 'não informado'}",
                    f"URL: {failure.url or 'não informada'}",
                    f"Motivo: {failure.reason}",
                    "",
                )
            )

    return "\n".join(lines).rstrip() + "\n"


def execute_collection(
    *,
    max_editions: int,
    database_url: str = DATABASE_URL,
    niches_dir: str | Path = NICHE_CONFIG_DIR,
    report_path: str | Path | None = None,
    collector: DoeMsDocumentCollector | None = None,
) -> DoeMsCommandResult:
    document_collector = collector or DoeMsDocumentCollector(
        max_editions=max_editions
    )
    collection = document_collector.collect_with_report()

    session_factory = initialize_database(database_url)
    engine = session_factory.kw["bind"]
    try:
        registry = NicheRegistry(niches_dir)
        with session_factory() as session:
            tracker = PublicationTracker(session, registry)
            tracked = tuple(
                tracker.register(item) for item in collection.result.items
            )
            session.commit()
    finally:
        engine.dispose()

    new_count = sum(1 for item in tracked if item.is_new)
    duplicate_count = len(tracked) - new_count
    matched_subniche_ids = tuple(
        sorted(
            {
                subniche_id
                for item in tracked
                for subniche_id in item.matched_subnicho_ids
            }
        )
    )
    match_evidence = tuple(
        evidence
        for publication, tracking in zip(collection.result.items, tracked)
        if tracking.is_new
        for evidence in find_subniche_evidence(publication, registry)
    )

    destination = Path(report_path) if report_path else (
        PROJECT_ROOT
        / "data"
        / "runtime"
        / "reports"
        / f"doe_ms_{datetime.now():%Y%m%d_%H%M%S}.txt"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_report(
            collection,
            new_count=new_count,
            duplicate_count=duplicate_count,
            matched_subniche_ids=matched_subniche_ids,
            match_evidence=match_evidence,
        ),
        # UTF-8 with BOM is detected correctly by Windows PowerShell 5.1.
        encoding="utf-8-sig",
    )

    return DoeMsCommandResult(
        report_path=destination,
        discovered_count=collection.discovered_count,
        attempted_count=collection.attempted_count,
        processed_count=len(collection.result.items),
        failure_count=len(collection.failures),
        new_count=new_count,
        duplicate_count=duplicate_count,
        matched_subniche_ids=matched_subniche_ids,
        match_evidence=match_evidence,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa uma coleta controlada do DOE-MS."
    )
    parser.add_argument(
        "--max-editions",
        type=int,
        default=5,
        help="Número máximo de edições a processar (padrão: 5).",
    )
    parser.add_argument("--database-url", default=DATABASE_URL)
    parser.add_argument("--niches-dir", default=str(NICHE_CONFIG_DIR))
    parser.add_argument("--report-path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = execute_collection(
            max_editions=args.max_editions,
            database_url=args.database_url,
            niches_dir=args.niches_dir,
            report_path=args.report_path,
        )
    except Exception as exc:
        print(f"Coleta DOE-MS não concluída: {exc}")
        return 1

    print("Coleta DOE-MS concluída.")
    print(f"Relatório: {result.report_path}")
    print(f"PDFs processados: {result.processed_count}")
    print(f"Falhas: {result.failure_count}")
    print(f"Publicações novas: {result.new_count}")
    print(f"Publicações duplicadas: {result.duplicate_count}")
    return 0 if result.processed_count or not result.failure_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
