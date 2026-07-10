from __future__ import annotations

from pydantic import BaseModel


class ReviewItem(BaseModel):
    review_id: str
    item_type: str
    paper_id: str | None = None
    study_id: str | None = None
    current_value: str | None = None
    suggested_value: str | None = None
    reason_for_review: str
    source_quote: str | None = None
    source_page: int | None = None
    options: list[str] = ["accept", "reject", "edit"]
    status: str = "pending"
