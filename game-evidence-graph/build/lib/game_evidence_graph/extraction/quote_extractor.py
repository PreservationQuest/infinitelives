from __future__ import annotations

from game_evidence_graph.schemas.paper import PageText


def locate_quote(pages: list[PageText], quote: str | None) -> tuple[int | None, str]:
    if not quote:
        return None, "not_found"
    normalized_quote = " ".join(quote.split())
    for page in pages:
        if normalized_quote in " ".join(page.text.split()):
            return page.page, "found"
    return None, "not_found"
