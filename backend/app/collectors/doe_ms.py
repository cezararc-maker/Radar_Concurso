"""DOE-MS edition discovery adapter.

The official DOE-MS search page exposes recent editions as direct PDF links.
This adapter discovers those links instead of guessing edition numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

from backend.app.collectors.base import CollectorError, CollectorResult
from backend.app.collectors.http import HttpCollector
from backend.app.services.publication_tracker import PublicationInput

_DATE_RE = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_ISSUE_RE = re.compile(r"n\.\s*([\d.]+)", re.IGNORECASE)


@dataclass(frozen=True)
class DoeMsEdition:
    issue_number: int
    publication_date: date
    title: str
    pdf_url: str
    supplement: bool = False


class _EditionLinkParser(HTMLParser):
    """Collect PDF links together with nearby row/container text."""

    def __init__(self) -> None:
        super().__init__()
        self._current_href: str | None = None
        self._current_text: list[str] = []
        self._current_context: list[str] = []
        self._row_depth = 0
        self._row_text: list[str] = []
        self.links: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._row_depth = 1
            self._row_text = []
            return
        if self._row_depth:
            self._row_depth += 1

        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._current_href = href
            self._current_text = []
            self._current_context = list(self._row_text)

    def handle_data(self, data: str) -> None:
        if self._row_depth:
            self._row_text.append(data)
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag == "a" and self._current_href is not None:
            title = " ".join(" ".join(self._current_text).split())
            context = " ".join(" ".join(self._row_text).split())
            self.links.append((title, self._current_href, context))
            self._current_href = None
            self._current_text = []
            self._current_context = []

        if self._row_depth:
            self._row_depth -= 1
            if tag == "tr" and self._row_depth == 0:
                self._row_text = []


class DoeMsCollector(HttpCollector):
    """Discover recent DOE-MS PDF editions from the official search page."""

    name = "doe_ms"

    def __init__(
        self,
        discovery_url: str = "https://www.diariooficial.ms.gov.br/",
        *,
        timeout: float = 20.0,
    ) -> None:
        super().__init__(
            discovery_url,
            source="Diário Oficial de Mato Grosso do Sul",
            timeout=timeout,
        )

    @staticmethod
    def discover_editions(html: str, *, base_url: str) -> tuple[DoeMsEdition, ...]:
        parser = _EditionLinkParser()
        parser.feed(html)
        editions: list[DoeMsEdition] = []

        for title, href, context in parser.links:
            match_issue = _ISSUE_RE.search(title) or _ISSUE_RE.search(context)
            match_date = _DATE_RE.search(title) or _DATE_RE.search(context)
            if not match_issue or not match_date or not href.lower().endswith(".pdf"):
                continue

            day, month, year = map(int, match_date.groups())
            edition = DoeMsEdition(
                issue_number=int(match_issue.group(1).replace(".", "")),
                publication_date=date(year, month, day),
                title=title or context,
                pdf_url=urljoin(base_url, href),
                supplement=("suplement" in (title + " " + context).lower() or "extra" in (title + " " + context).lower()),
            )
            editions.append(edition)

        unique = {
            (item.issue_number, item.publication_date, item.pdf_url): item
            for item in editions
        }
        return tuple(
            sorted(
                unique.values(),
                key=lambda item: (item.publication_date, item.issue_number, not item.supplement),
                reverse=True,
            )
        )

    def collect(self) -> CollectorResult:
        html = self.fetch()
        editions = self.discover_editions(html, base_url=self.url)
        if not editions:
            raise CollectorError("Nenhuma edição DOE-MS foi encontrada na página oficial.")

        items = tuple(
            PublicationInput(
                titulo=edition.title,
                fonte=self.source,
                url=edition.pdf_url,
                data_publicacao=edition.publication_date,
                tipo="diario_oficial_edicao",
                identificador=f"doe-ms:{edition.issue_number}:{edition.publication_date.isoformat()}:{edition.pdf_url}",
            )
            for edition in editions
        )
        return CollectorResult(
            source=self.source,
            collected_at=date.today(),
            items=items,
        )
