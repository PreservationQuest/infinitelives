from game_evidence_graph.recite_adapter.adaptation_report import build_adaptation_report


def test_recite_adaptation_report_mentions_limits(tmp_path):
    (tmp_path / "module.py").write_text("print('x')")
    report = build_adaptation_report(tmp_path)
    assert "Assumptions Not Reused" in report
    assert "ontology-inferred mechanics" in report
