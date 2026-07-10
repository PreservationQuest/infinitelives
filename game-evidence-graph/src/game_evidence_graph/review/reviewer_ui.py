from __future__ import annotations


def run_review_ui() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError("Install streamlit to run the review UI.") from exc
    st.title("Game Evidence Graph Review Queue")
    st.write("Load review_queue.csv, decide accept/reject/edit, and export decisions.")
