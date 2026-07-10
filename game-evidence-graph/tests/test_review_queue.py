import numpy as np
import pandas as pd

from game_evidence_graph.review.review_queue import build_review_queue


def test_review_queue_coerces_nan_source_quote_to_none():
    df = pd.DataFrame(
        [
            {
                "paper_id": "paper_001",
                "study_id": "study_001",
                "review_status": "needs_review",
                "attribution_level": "mechanic_set_inferred",
                "source_quote": np.nan,
                "source_page": np.nan,
                "is_supported_evidence": True,
            }
        ]
    )

    items = build_review_queue(df)

    assert len(items) == 1
    assert items[0].source_quote is None
    assert items[0].source_page is None
