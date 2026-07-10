from typer.testing import CliRunner

from game_evidence_graph.cli import app


def test_cli_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / "data/input/papers").exists()
