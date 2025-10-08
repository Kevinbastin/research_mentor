#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install from https://github.com/astral-sh/uv and re-run." >&2
  exit 1
fi

echo "🔁 Cleaning previous build artifacts"
rm -rf dist/

echo "📦 Building wheel and source distribution"
uv build

echo "🚀 Publishing to PyPI (set UV_PUBLISH_TOKEN before running)"
uv publish "$@"
