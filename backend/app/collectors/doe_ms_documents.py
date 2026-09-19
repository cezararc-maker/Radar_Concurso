"""Compose DOE-MS edition discovery with official PDF extraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from backend.app.collectors.base import Collector, CollectorError, CollectorResult
from backend.app.collectors.doe_ms import DoeMsCollector
from backend.app.collectors.pdf import OfficialPdfCollector


PdfCollectorFactory = Callable[..., OfficialPdfCollector]


@dataclass(frozen=True)
class DoeMsDocumentFailure:
    """One edition that could not be downloaded or parsed."""

    identifier: str | None
    url: str | None
    reason: str


@dataclass(frozen=True)
class DoeMsDocumentCollectionReport:
    """Detailed outcome of a controlled DOE-MS document collection."""

    result: CollectorResult
    discovered_count: int
    attempted_count: int
    failures: tuple[DoeMsDocumentFailure, ...]


class DoeMsDocumentCollector(Collector):
    """Discover DOE-MS editions and collect the text of their official PDFs."""

    name = "doe_ms_documents"

    def __init__(
        self,
        edition_collector: DoeMsCollector | None = None,
        *,
        pdf_collector_factory: PdfCollectorFactory = OfficialPdfCollector,
        max_editions: int = 5,
        continue_on_error: bool = True,
    ) -> None:
        if max_editions < 1:
            raise ValueError("max_editions deve ser maior que zero.")

        self.edition_collector = edition_collector or DoeMsCollector()
        self.pdf_collector_factory = pdf_collector_factory
        self.max_editions = max_editions
        self.continue_on_error = continue_on_error

    def collect_with_report(self) -> DoeMsDocumentCollectionReport:
        edition_result = self.edition_collector.collect()
        selected_editions = edition_result.items[: self.max_editions]
        documents = []
        failures: list[DoeMsDocumentFailure] = []

        for edition in selected_editions:
            try:
                if (
                    not edition.url
                    or not edition.data_publicacao
                    or not edition.identificador
                ):
                    raise CollectorError(
                        "Edição DOE-MS sem URL, data de publicação ou identificador."
                    )

                pdf_collector = self.pdf_collector_factory(
                    edition.url,
                    source=edition.fonte or edition_result.source,
                    publication_date=edition.data_publicacao,
                    identifier=edition.identificador,
                )
                pdf_result = pdf_collector.collect()
                documents.extend(pdf_result.items)
            except Exception as exc:
                if not self.continue_on_error:
                    raise CollectorError(
                        f"Falha ao processar a edição DOE-MS "
                        f"{edition.identificador or edition.url}: {exc}"
                    ) from exc
                failures.append(
                    DoeMsDocumentFailure(
                        identifier=edition.identificador,
                        url=edition.url,
                        reason=str(exc),
                    )
                )

        result = CollectorResult(
            source=edition_result.source,
            collected_at=date.today(),
            items=tuple(documents),
        )
        return DoeMsDocumentCollectionReport(
            result=result,
            discovered_count=len(edition_result.items),
            attempted_count=len(selected_editions),
            failures=tuple(failures),
        )

    def collect(self) -> CollectorResult:
        return self.collect_with_report().result
