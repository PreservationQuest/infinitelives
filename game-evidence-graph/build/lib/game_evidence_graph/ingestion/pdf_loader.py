from __future__ import annotations

from pathlib import Path

from game_evidence_graph.ingestion.metadata_extractor import extract_metadata
from game_evidence_graph.ingestion.pdf_to_text import extract_pages
from game_evidence_graph.schemas.paper import PaperDocument


def assign_paper_id(index: int) -> str:
    return f"paper_{index:03d}"


def load_pdf(pdf_path: str | Path, paper_id: str) -> PaperDocument:
    pages = extract_pages(pdf_path)
    metadata = extract_metadata(paper_id, pdf_path, pages)
    return PaperDocument(metadata=metadata, pages=pages)


def ingest_pdf_folder(pdf_dir: str | Path, out_dir: str | Path | None = None) -> list[PaperDocument]:
    paths = sorted(Path(pdf_dir).glob("*.pdf"))
    docs = [load_pdf(path, assign_paper_id(i)) for i, path in enumerate(paths, start=1)]
    if out_dir:
        for doc in docs:
            doc.save_intermediate(out_dir)
    return docs
