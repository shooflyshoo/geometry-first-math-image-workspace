#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BATCH_ROOT="$ROOT/sources/unpacked/geometry_first_math_image_batch_kit"
BLUEPRINT_ROOT="$ROOT/sources/unpacked/geometry_first_math_image_prompts_v6_constraint_stack"

python3 "$ROOT/scripts/summarize_manuscripts.py"
python3 "$ROOT/scripts/validate_manifests.py" --write-reports

# Dry-run only: exercise batch generator path without API calls.
python3 "$BATCH_ROOT/generate_geometry_first_math_images.py" \
  --manifest "$BATCH_ROOT/manifests/section_0.jsonl" \
  --dry-run \
  --limit 2

python3 "$BATCH_ROOT/generate_geometry_first_math_images.py" \
  --manifest "$BATCH_ROOT/manifests/extras.jsonl" \
  --dry-run \
  --limit 2

cat <<'EOF'

Dry-run validation complete.
- Pilot validation was schema/count-based (20 prompts, variants=3) via validate_manifests.py.
- Batch generation checks were dry-run only (no image API calls).
- Reports written under image-production/reports/ and image-production/manifest-summary.md.
EOF
