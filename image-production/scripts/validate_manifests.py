#!/usr/bin/env python3
"""Validate pilot and section manifests without calling image APIs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: invalid JSON at line {i}: {exc}") from exc
    return rows


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def sorted_section_items(counter: Counter[str]) -> list[tuple[str, int]]:
    order_map: dict[str, int] = {str(i): i for i in range(20)}
    order_map.update({"A": 20, "B": 21, "EXTRA": 99})
    return sorted(counter.items(), key=lambda kv: order_map.get(kv[0], 1000))


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Manifest Summary",
        "",
        "## Core Counts",
        "",
        f"- Pilot prompts (v6): **{summary['pilot_count']}**",
        f"- Full blueprint prompts (v6): **{summary['full_blueprint_count']}**",
        f"- Priority regen prompts (v6): **{summary['priority_regen_count']}**",
        f"- Batch jobs (section manifests): **{summary['batch_total']}**",
        f"- Subsection jobs: **{summary['subsection_count']}**",
        f"- Extra jobs: **{summary['extra_count']}**",
        "",
        "## Pilot Requirements Check",
        "",
        f"- Pilot prompt count is 20: **{summary['pilot_count'] == 20}**",
        f"- Pilot recommended variants are all 3: **{summary['pilot_all_variants_3']}**",
        "",
        "## Section Manifest Counts",
        "",
        "| Section | Count |",
        "|---|---:|",
    ]

    for sec, cnt in summary["section_counts"]:
        lines.append(f"| `{sec}` | {cnt} |")

    lines += [
        "",
        "## Format Mix",
        "",
        "| Format | Count |",
        "|---|---:|",
    ]
    for fmt, cnt in summary["format_counts"]:
        lines.append(f"| `{fmt}` | {cnt} |")

    lines += [
        "",
        "## Suggested Generation Order",
        "",
        "1. `geometry_first_math_image_prompts_v6_pilot_20.jsonl` (3 variants each; visual language lock)",
        "2. Batch sections `0,1,2,3`",
        "3. Batch sections `4,5,6,7`",
        "4. Batch sections `8,9,10,11`",
        "5. Interludes and bridges `A,12,13,B`",
        "6. Advanced arc `14,15,16,17`",
        "7. Final arc `18,19`",
        "8. `extras.jsonl`",
        "",
        "## Validation Result",
        "",
        f"- Status: **{'PASS' if not summary['errors'] else 'FAIL'}**",
    ]

    if summary["errors"]:
        lines.append("- Errors:")
        for err in summary["errors"]:
            lines.append(f"  - {err}")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="image-production/sources/unpacked")
    ap.add_argument("--write-reports", action="store_true")
    ap.add_argument("--out-json", default="image-production/reports/manifest_summary.json")
    ap.add_argument("--out-md", default="image-production/manifest-summary.md")
    args = ap.parse_args()

    base = Path(args.base)
    blueprint = base / "geometry_first_math_image_prompts_v6_constraint_stack"
    batch = base / "geometry_first_math_image_batch_kit"
    manifests_dir = batch / "manifests"

    pilot = load_jsonl(blueprint / "geometry_first_math_image_prompts_v6_pilot_20.jsonl")
    full = load_jsonl(blueprint / "geometry_first_math_image_prompts_v6_constraint_stack.jsonl")
    priority = load_jsonl(blueprint / "geometry_first_math_image_prompts_v6_priority_regen.jsonl")
    jobs = load_jsonl(batch / "geometry_first_math_image_jobs.jsonl")

    errors: list[str] = []

    if len(pilot) != 20:
        fail(errors, f"Pilot manifest expected 20 rows; found {len(pilot)}")

    pilot_variants = {int(r.get("recommended_variants", -1)) for r in pilot}
    if pilot_variants != {3}:
        fail(errors, f"Pilot recommended_variants expected only {{3}}; found {sorted(pilot_variants)}")

    prompt_ids = [str(r.get("prompt_id")) for r in full]
    if len(prompt_ids) != len(set(prompt_ids)):
        fail(errors, "Full blueprint prompt_id values are not unique")

    batch_ids = [str(r.get("id")) for r in jobs]
    if len(batch_ids) != len(set(batch_ids)):
        fail(errors, "Batch job id values are not unique")

    sequences = [int(r.get("sequence", -1)) for r in jobs]
    if sorted(sequences) != list(range(1, len(jobs) + 1)):
        fail(errors, "Batch sequence values are not a contiguous 1..N range")

    kind_counts = Counter(str(r.get("kind")) for r in jobs)
    format_counts = Counter(str(r.get("format")) for r in jobs)
    section_counts = Counter(str(r.get("section")) for r in jobs)

    expected_manifest_names = {f"section_{i}.jsonl" for i in range(20)} | {"section_A.jsonl", "section_B.jsonl", "extras.jsonl"}
    existing_manifest_names = {p.name for p in manifests_dir.glob("*.jsonl")}

    missing = sorted(expected_manifest_names - existing_manifest_names)
    if missing:
        fail(errors, f"Missing section manifest files: {missing}")

    if existing_manifest_names - expected_manifest_names:
        fail(errors, f"Unexpected manifest files: {sorted(existing_manifest_names - expected_manifest_names)}")

    manifest_rows: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(manifests_dir.glob("*.jsonl")):
        manifest_rows[path.name] = load_jsonl(path)

    manifest_union_ids: set[str] = set()
    for rows in manifest_rows.values():
        for row in rows:
            manifest_union_ids.add(str(row.get("id")))

    if manifest_union_ids != set(batch_ids):
        fail(errors, "Union of section manifests does not match master batch ids")

    for name, rows in manifest_rows.items():
        if name == "extras.jsonl":
            if any(str(r.get("kind")) != "extra" for r in rows):
                fail(errors, "extras.jsonl contains non-extra rows")
        elif any(str(r.get("kind")) != "subsection" for r in rows):
            fail(errors, f"{name} contains non-subsection rows")

    summary = {
        "pilot_count": len(pilot),
        "full_blueprint_count": len(full),
        "priority_regen_count": len(priority),
        "batch_total": len(jobs),
        "subsection_count": kind_counts.get("subsection", 0),
        "extra_count": kind_counts.get("extra", 0),
        "pilot_all_variants_3": pilot_variants == {3},
        "section_counts": sorted_section_items(section_counts),
        "format_counts": sorted(format_counts.items(), key=lambda kv: kv[0]),
        "manifest_file_counts": {k: len(v) for k, v in sorted(manifest_rows.items())},
        "errors": errors,
    }

    print(json.dumps(summary, indent=2))

    if args.write_reports:
        out_json = Path(args.out_json)
        out_md = Path(args.out_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        out_md.write_text(render_markdown(summary), encoding="utf-8")
        print(f"Wrote {out_json}")
        print(f"Wrote {out_md}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
