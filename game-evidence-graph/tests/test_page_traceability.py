from game_evidence_graph.extraction.quote_extractor import locate_quote
from game_evidence_graph.schemas.paper import PageText


def test_locate_quote_returns_page():
    page, status = locate_quote([PageText(page=3, text="The game group improved.")], "game group improved")
    assert page == 3
    assert status == "found"
