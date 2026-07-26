.PHONY: sync download build smoke test lint verify package

sync:
	uv sync --all-groups

download:
	uv run monatendard fetch

build:
	uv run monatendard build --all

smoke:
	uv run monatendard build --variants Regular

test:
	uv run pytest

lint:
	uv run ruff check .

verify:
	uv run monatendard verify

package:
	uv run monatendard package --version 0.1.0
