"""PDF collector foundation for official diary editions."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from urllib.request import Request, urlopen

from pypdf import PdfReader

from backend.app.collectors.base import CollectorResult, CollectorError
from backend.app.services.publication_tracker import PublicationInput


class OfficialPdfCollector:
    """Download one official PDF and normalize its extracted text.

    Discovery of the PDF URL is deliberately kept separate from PDF parsing.
    This lets each official source have its own edition-discovery strategy.
    """

    name = "official_pdf"

    def __init__(
        self,
        url: str,
        *,
        source: str,
        publication_date: date,
        identifier: str,
        timeout: float = 30.0,
        user_agent: str = "RadarConcurso/0.1",
    ):
        self.url = url
        self.source = source
        self.publication_date = publication_date
        self.identifier = identifier
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch_bytes(self) -> bytes:
        request = Request(
            self.url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/pdf,*/*;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except Exception as exc:
            raise CollectorError(
                f"Falha ao baixar PDF de {self.source}: {exc}"
            ) from exc

    @staticmethod
    def extract_text(content: bytes) -> str:
        reader = PdfReader(BytesIO(content))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()

    def collect(self) -> CollectorResult:
        content = self.fetch_bytes()
        text = self.extract_text(content)
        item = PublicationInput(
            titulo=f"{self.source} - Diário Oficial",
            conteudo=text,
            fonte=self.source,
            url=self.url,
            data_publicacao=self.publication_date,
            tipo="diario_oficial_pdf",
            identificador=self.identifier,
        )
        return CollectorResult(
            source=self.source,
            collected_at=date.today(),
            items=(item,),
        )
