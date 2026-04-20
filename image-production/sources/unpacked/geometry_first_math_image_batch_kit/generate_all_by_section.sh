#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python}"
GEN="$ROOT/generate_geometry_first_math_images.py"

if [[ ! -n "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is not set." >&2
  exit 1
fi

for manifest in "$ROOT"/manifests/*.jsonl; do
  name="$(basename "$manifest" .jsonl)"
  echo "=== Generating $name ==="
  "$PYTHON" "$GEN" \
    --manifest "$manifest" \
    --output-dir "$ROOT/output/$name" \
    --metadata-dir "$ROOT/metadata/$name"
done
