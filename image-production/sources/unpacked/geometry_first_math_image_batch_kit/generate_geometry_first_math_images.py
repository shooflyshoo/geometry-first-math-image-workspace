
#!/usr/bin/env python3
"""Generate the Geometry-First Mathematics image library from the batch manifest.

Requirements:
  pip install openai

Environment:
  export OPENAI_API_KEY=...

Examples:
  python generate_geometry_first_math_images.py
  python generate_geometry_first_math_images.py --manifest manifests/section_00.jsonl --output-dir output/section_00
  python generate_geometry_first_math_images.py --match 16. --limit 3 --dry-run
  python generate_geometry_first_math_images.py --kind extra --output-dir output/extras
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from openai import OpenAI
except Exception as exc:  # pragma: no cover
    OpenAI = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=here / "geometry_first_math_image_jobs.jsonl",
        help="Path to the JSONL manifest.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=here / "output",
        help="Directory to write generated PNG files.",
    )
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=here / "metadata",
        help="Directory to write companion JSON metadata.",
    )
    parser.add_argument(
        "--model",
        default="gpt-image-1.5",
        help="Image model to use. Default: gpt-image-1.5",
    )
    parser.add_argument(
        "--quality",
        default=None,
        choices=["low", "medium", "high", "auto", None],
        help="Override manifest quality for all images.",
    )
    parser.add_argument(
        "--size",
        default=None,
        choices=["1024x1024", "1536x1024", "1024x1536", "auto", None],
        help="Override manifest size for all images.",
    )
    parser.add_argument(
        "--background",
        default=None,
        choices=["opaque", "transparent", "auto", None],
        help="Override manifest background for all images.",
    )
    parser.add_argument(
        "--kind",
        default="all",
        choices=["all", "subsection", "extra"],
        help="Generate all records, only subsections, or only extras.",
    )
    parser.add_argument(
        "--match",
        default=None,
        help="Case-insensitive substring filter applied to id, title, and source key.",
    )
    parser.add_argument(
        "--ids",
        nargs="*",
        default=None,
        help="Optional explicit IDs to generate, e.g. 0.1 0.2 EXTRA-01",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit after filtering.",
    )
    parser.add_argument(
        "--start-at",
        type=int,
        default=None,
        help="Optional sequence number to start from.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate images even if the output PNG already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned work without calling the API.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Seconds to sleep between requests.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Retry count for transient failures.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of variants per prompt. Saves with _v01 suffix when >1.",
    )
    parser.add_argument(
        "--moderation",
        default=None,
        choices=["auto", "low", None],
        help="Optional moderation strictness override if your SDK supports it.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
    return records


def filter_records(records: List[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    filtered = records

    if args.kind != "all":
        filtered = [r for r in filtered if r.get("kind") == args.kind]

    if args.start_at is not None:
        filtered = [r for r in filtered if int(r.get("sequence", 0)) >= args.start_at]

    if args.match:
        needle = args.match.lower()
        filtered = [
            r
            for r in filtered
            if needle in str(r.get("id", "")).lower()
            or needle in str(r.get("title", "")).lower()
            or needle in str(r.get("source_key", "")).lower()
            or needle in str(r.get("section", "")).lower()
        ]

    if args.ids:
        wanted = {s.lower() for s in args.ids}
        filtered = [r for r in filtered if str(r.get("id", "")).lower() in wanted]

    if args.limit is not None:
        filtered = filtered[: args.limit]

    return filtered


def safe_stem(record: Dict[str, Any]) -> str:
    filename = str(record["filename"])
    return Path(filename).stem


def image_paths(record: Dict[str, Any], output_dir: Path, n: int) -> List[Path]:
    stem = safe_stem(record)
    if n <= 1:
        return [output_dir / f"{stem}.png"]
    return [output_dir / f"{stem}_v{i:02d}.png" for i in range(1, n + 1)]


def metadata_path(record: Dict[str, Any], metadata_dir: Path) -> Path:
    return metadata_dir / f"{safe_stem(record)}.json"


def build_request_kwargs(record: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "model": args.model,
        "prompt": record["api_prompt"],
        "size": args.size or record["size"],
        "quality": args.quality or record["quality"],
        "background": args.background or record["background"],
        "n": args.n,
    }
    # The OpenAI docs show GPT Image returning b64_json without needing a format override.
    # We keep the request minimal to maximize SDK compatibility.
    if args.moderation is not None:
        kwargs["moderation"] = args.moderation
    return kwargs


def extract_payload(result: Any) -> Dict[str, Any]:
    """Try several SDK object shapes to obtain a JSON-like dict."""
    if result is None:
        return {}
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        try:
            return result.model_dump()
        except Exception:
            pass
    if hasattr(result, "to_dict"):
        try:
            return result.to_dict()
        except Exception:
            pass
    if hasattr(result, "json"):
        try:
            raw = result.json()
            if isinstance(raw, str):
                return json.loads(raw)
            if isinstance(raw, dict):
                return raw
        except Exception:
            pass
    # Fallback: inspect common attributes
    payload: Dict[str, Any] = {}
    for attr in ("data", "created", "usage"):
        if hasattr(result, attr):
            payload[attr] = getattr(result, attr)
    return payload


def extract_b64_images(result: Any, payload: Dict[str, Any]) -> List[str]:
    data = None
    if hasattr(result, "data"):
        data = getattr(result, "data")
    if data is None:
        data = payload.get("data")
    if data is None:
        return []

    b64_images: List[str] = []
    for item in data:
        if isinstance(item, dict):
            b64 = item.get("b64_json")
            if b64:
                b64_images.append(b64)
        else:
            if hasattr(item, "b64_json") and getattr(item, "b64_json"):
                b64_images.append(getattr(item, "b64_json"))
            elif hasattr(item, "url") and getattr(item, "url"):
                raise RuntimeError(
                    "SDK returned URLs instead of base64. This script expects GPT Image base64 responses. "
                    "Switch to a GPT Image model or update extraction logic."
                )
    return b64_images


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_images(image_b64_list: List[str], paths: List[Path]) -> None:
    if len(image_b64_list) != len(paths):
        raise ValueError(f"Expected {len(paths)} images but received {len(image_b64_list)}")
    for b64_data, path in zip(image_b64_list, paths):
        ensure_parent(path)
        image_bytes = base64.b64decode(b64_data)
        path.write_bytes(image_bytes)


def all_exist(paths: Iterable[Path]) -> bool:
    return all(path.exists() for path in paths)


def make_client() -> "OpenAI":
    if OpenAI is None:  # pragma: no cover
        raise RuntimeError(
            "The openai package is not importable. Install it with `pip install openai`."
        ) from _IMPORT_ERROR

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
    return OpenAI()


def write_metadata(record: Dict[str, Any], payload: Dict[str, Any], request_kwargs: Dict[str, Any], path: Path) -> None:
    ensure_parent(path)
    doc = {
        "request": request_kwargs,
        "record": {
            key: record[key]
            for key in (
                "sequence",
                "kind",
                "id",
                "section",
                "source_key",
                "title",
                "format",
                "layout_label",
                "size",
                "quality",
                "background",
                "filename",
                "caption",
                "overlay",
            )
        },
        "response": payload,
        "generated_at_unix": int(time.time()),
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    records = load_manifest(args.manifest)
    selected = filter_records(records, args)

    if not selected:
        logging.warning("No matching records after filters.")
        return 0

    logging.info("Selected %d records from %s", len(selected), args.manifest)

    if args.dry_run:
        for rec in selected:
            paths = image_paths(rec, args.output_dir, args.n)
            logging.info(
                "DRY RUN | %03d | %s | %s | %s",
                rec["sequence"],
                rec["id"],
                rec["title"],
                ", ".join(str(p) for p in paths),
            )
        return 0

    client = make_client()

    for rec in selected:
        out_paths = image_paths(rec, args.output_dir, args.n)
        meta_path = metadata_path(rec, args.metadata_dir)

        if not args.overwrite and all_exist(out_paths):
            logging.info("Skipping existing: %s", ", ".join(str(p) for p in out_paths))
            continue

        request_kwargs = build_request_kwargs(rec, args)

        attempt = 0
        while True:
            attempt += 1
            try:
                logging.info(
                    "Generating %s | %s | size=%s quality=%s n=%d",
                    rec["id"],
                    rec["title"],
                    request_kwargs["size"],
                    request_kwargs["quality"],
                    args.n,
                )
                result = client.images.generate(**request_kwargs)
                payload = extract_payload(result)
                b64_images = extract_b64_images(result, payload)
                if not b64_images:
                    raise RuntimeError("No base64 image data returned by the API.")
                save_images(b64_images, out_paths)
                write_metadata(rec, payload, request_kwargs, meta_path)
                logging.info("Saved %s", ", ".join(str(p) for p in out_paths))
                if args.sleep:
                    time.sleep(args.sleep)
                break
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                if attempt > args.retries:
                    logging.error("Failed after %d attempts for %s: %s", attempt - 1, rec["id"], exc)
                    return 1
                wait = min(2 ** (attempt - 1), 20)
                logging.warning(
                    "Attempt %d/%d failed for %s: %s. Retrying in %ss...",
                    attempt,
                    args.retries,
                    rec["id"],
                    exc,
                    wait,
                )
                time.sleep(wait)

    logging.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
