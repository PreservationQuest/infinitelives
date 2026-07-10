from __future__ import annotations

from pathlib import Path

from game_evidence_graph.ingestion.text_cleaner import clean_page_text
from game_evidence_graph.schemas.paper import PageText


def extract_pages(pdf_path: str | Path) -> list[PageText]:
    path = Path(pdf_path)
    try:
        import fitz

        doc = fitz.open(path)
        pages: list[PageText] = []
        for idx, page in enumerate(doc, start=1):
            text = clean_page_text(page.get_text("text"))
            drawings = len(page.get_drawings())
            pages.append(
                PageText(
                    page=idx,
                    text=text,
                    non_textual_content_detected=drawings > 15 and len(text) < 500,
                    needs_review=drawings > 15 and len(text) < 500,
                    reason=(
                        "Possible figure or table not represented in extracted text."
                        if drawings > 15 and len(text) < 500
                        else None
                    ),
                )
            )
        return pages
    except Exception:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return [
            PageText(page=i, text=clean_page_text(page.extract_text() or ""))
            for i, page in enumerate(reader.pages, start=1)
        ]
