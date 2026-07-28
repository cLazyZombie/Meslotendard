#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_root"

case "$(uname -s)" in
  Darwin | Linux) ;;
  *)
    printf '오류: macOS 또는 Linux에서만 실행할 수 있습니다.\n' >&2
    exit 1
    ;;
esac

if ! command -v uv >/dev/null 2>&1; then
  printf '오류: uv를 먼저 설치하세요: https://docs.astral.sh/uv/\n' >&2
  exit 1
fi

uv sync --all-groups --frozen
uv run ruff check .
uv run pytest
uv run meslotendard fetch
uv run meslotendard build --all
uv run meslotendard verify --reproducible
uv run meslotendard render

if [[ $# -gt 0 ]]; then
  uv run meslotendard package --version "$1"
else
  uv run meslotendard package
fi

(
  cd dist
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum --check SHA256SUMS.txt
  else
    shasum -a 256 -c SHA256SUMS.txt
  fi
)

printf '완료: fonts/ttf, assets/meslotendard-preview.png, dist/Meslotendard.zip\n'
