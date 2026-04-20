#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"
UNPACK_DIR="$ROOT/sources/unpacked"
ORIG_DIR="$ROOT/sources/originals"

mkdir -p "$UNPACK_DIR" "$ORIG_DIR"

ln -sfn "$REPO_ROOT/Geometry_First_Mathematics_Image_Prompt_Blueprint_v6_Constraint_Stack_Package.zip" \
  "$ORIG_DIR/Geometry_First_Mathematics_Image_Prompt_Blueprint_v6_Constraint_Stack_Package.zip"
ln -sfn "$REPO_ROOT/Geometry_First_Math_Image_Batch_Kit.zip" \
  "$ORIG_DIR/Geometry_First_Math_Image_Batch_Kit.zip"
ln -sfn "$REPO_ROOT/Geometry_First_Mathematics_Expanded_Intuition_Edition.docx" \
  "$ORIG_DIR/Geometry_First_Mathematics_Expanded_Intuition_Edition.docx"
ln -sfn "$REPO_ROOT/Geometry_First_Mathematics_Expanded_Intuition_Edition.pdf" \
  "$ORIG_DIR/Geometry_First_Mathematics_Expanded_Intuition_Edition.pdf"
ln -sfn "$REPO_ROOT/Geometry_First_Mathematics_Visually_Informed_Expanded_Edition_v3.docx" \
  "$ORIG_DIR/Geometry_First_Mathematics_Visually_Informed_Expanded_Edition_v3.docx"

unzip -q -o "$REPO_ROOT/Geometry_First_Mathematics_Image_Prompt_Blueprint_v6_Constraint_Stack_Package.zip" -d "$UNPACK_DIR"
unzip -q -o "$REPO_ROOT/Geometry_First_Math_Image_Batch_Kit.zip" -d "$UNPACK_DIR"

echo "Workspace prepared under: $ROOT"
