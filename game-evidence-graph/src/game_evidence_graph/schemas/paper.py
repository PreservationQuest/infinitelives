from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class PageText(BaseModel):
    page: int
    text: str
    non_textual_content_detected: bool = False
    needs_review: bool = False
    reason: Optional[str] = None


class PaperMetadata(BaseModel):
    paper_id: str
    title: Optional[str] = None
    authors: list[str] = []
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    source_pdf: Optional[str] = None


class PaperDocument(BaseModel):
    metadata: PaperMetadata
    pages: list[PageText]

    @property
    def full_text(self) -> str:
        return "\n\n".join(f"[Page {page.page}]\n{page.text}" for page in self.pages)

    def save_intermediate(self, out_dir: str | Path) -> None:
        folder = Path(out_dir) / self.metadata.paper_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "pages.json").write_text(self.model_dump_json(indent=2))
        (folder / "full_text.txt").write_text(self.full_text)
        (folder / "metadata.json").write_text(self.metadata.model_dump_json(indent=2))
        (folder / "sections.json").write_text("[]")
