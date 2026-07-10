.PHONY: test lint run-all

test:
	pytest

lint:
	ruff check src tests

run-all:
	game-evidence run-all --pdf-dir data/input/papers --out data/processed
