#!/usr/bin/env python3
"""Summarize manuscript source files and infer likely primary text."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
CP_NS = {
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
}
APP_NS = {"ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"}


@dataclass
class ManuscriptRecord:
    path: str
    kind: str
    size_bytes: int
    sha256: str
    mtime_utc: str
    metadata: dict[str, Any]
    text_preview: str
    text_word_count: int | None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_docx(path: Path) -> ManuscriptRecord:
    with zipfile.ZipFile(path) as zf:
        core_xml = zf.read("docProps/core.xml")
        app_xml = zf.read("docProps/app.xml")
        doc_xml = zf.read("word/document.xml")

    core = ET.fromstring(core_xml)
    app = ET.fromstring(app_xml)
    doc = ET.fromstring(doc_xml)

    texts = [t.text or "" for t in doc.findall(".//w:t", W_NS)]
    joined = " ".join(s.strip() for s in texts if s and s.strip())
    joined = re.sub(r"\s+", " ", joined).strip()

    meta = {
        "title": (core.findtext("dc:title", default="", namespaces=CP_NS) or "").strip(),
        "subject": (core.findtext("dc:subject", default="", namespaces=CP_NS) or "").strip(),
        "creator": (core.findtext("dc:creator", default="", namespaces=CP_NS) or "").strip(),
        "created": (core.findtext("dcterms:created", default="", namespaces=CP_NS) or "").strip(),
        "modified": (core.findtext("dcterms:modified", default="", namespaces=CP_NS) or "").strip(),
        "application": (app.findtext("ep:Application", default="", namespaces=APP_NS) or "").strip(),
        "pages": (app.findtext("ep:Pages", default="", namespaces=APP_NS) or "").strip(),
        "words": (app.findtext("ep:Words", default="", namespaces=APP_NS) or "").strip(),
    }

    stat = path.stat()
    mtime_iso = dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).isoformat()
    return ManuscriptRecord(
        path=str(path),
        kind="docx",
        size_bytes=stat.st_size,
        sha256=sha256_file(path),
        mtime_utc=mtime_iso,
        metadata=meta,
        text_preview=joined[:260],
        text_word_count=len(joined.split()) if joined else 0,
    )


def run_cmd(args: list[str]) -> str:
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if proc.returncode != 0:
        return ""
    return proc.stdout


def read_pdf(path: Path) -> ManuscriptRecord:
    info_text = run_cmd(["pdfinfo", str(path)])
    meta: dict[str, Any] = {}
    for line in info_text.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip().lower().replace(" ", "_")] = v.strip()

    preview = ""
    text_dump = run_cmd(["pdftotext", str(path), "-"])
    if text_dump:
        lines = [ln.strip() for ln in text_dump.splitlines() if ln.strip()]
        preview = " ".join(lines[:8])[:260]

    stat = path.stat()
    words = len(text_dump.split()) if text_dump else None
    mtime_iso = dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).isoformat()
    return ManuscriptRecord(
        path=str(path),
        kind="pdf",
        size_bytes=stat.st_size,
        sha256=sha256_file(path),
        mtime_utc=mtime_iso,
        metadata=meta,
        text_preview=preview,
        text_word_count=words,
    )


def similarity_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a_words = set(re.findall(r"[A-Za-z]+", a.lower()))
    b_words = set(re.findall(r"[A-Za-z]+", b.lower()))
    if not a_words or not b_words:
        return 0.0
    return len(a_words & b_words) / len(a_words | b_words)


def infer_primary(records: list[ManuscriptRecord]) -> dict[str, Any]:
    docx_records = [r for r in records if r.kind == "docx"]
    pdf_records = [r for r in records if r.kind == "pdf"]

    evidence: list[str] = []
    candidate = None
    confidence = "low"

    if pdf_records and docx_records:
        pdf = pdf_records[0]
        scores = [(d.path, similarity_score(pdf.text_preview, d.text_preview)) for d in docx_records]
        scores.sort(key=lambda x: x[1], reverse=True)
        if scores:
            best_path, best = scores[0]
            second = scores[1][1] if len(scores) > 1 else 0.0
            evidence.append(f"PDF-to-DOCX lexical similarity: {scores}")
            if best >= 0.7 and (best - second) >= 0.05:
                candidate = best_path
                confidence = "medium"

    visually = next((r for r in docx_records if "Visually_Informed" in Path(r.path).name), None)
    expanded = next((r for r in docx_records if "Expanded_Intuition" in Path(r.path).name), None)

    if visually and expanded:
        if (visually.text_word_count or 0) > (expanded.text_word_count or 0):
            evidence.append(
                f"Visually informed DOCX is longer ({visually.text_word_count} words) than expanded intuition DOCX ({expanded.text_word_count} words)."
            )
        evidence.append("Filename includes explicit version tag 'v3' only on visually informed DOCX.")

    has_conflict = bool(visually and expanded)
    if candidate is None and visually:
        candidate = visually.path
        confidence = "low"

    if has_conflict and confidence == "medium":
        confidence = "low"

    if candidate is None:
        return {
            "primary_candidate": None,
            "confidence": "uncertain",
            "summary": "Could not infer a primary manuscript candidate from available metadata.",
            "evidence": evidence,
        }

    return {
        "primary_candidate": candidate,
        "confidence": confidence,
        "summary": (
            "Primary candidate inferred with limited certainty; manuscript selection is ambiguous and should be confirmed by editorial owner."
            if confidence == "low"
            else "Primary candidate inferred from PDF match and metadata."
        ),
        "evidence": evidence,
    }


def to_markdown(records: list[ManuscriptRecord], inference: dict[str, Any]) -> str:
    lines = [
        "# Manuscript Metadata Summary",
        "",
        "## Files",
        "",
        "| File | Type | Size (bytes) | Word count (estimated) | Key metadata |",
        "|---|---:|---:|---:|---|",
    ]
    for r in records:
        meta_bits = []
        for k in ["title", "subject", "pages", "modified", "creationdate"]:
            v = r.metadata.get(k)
            if v:
                meta_bits.append(f"{k}={v}")
        lines.append(
            f"| `{Path(r.path).name}` | {r.kind} | {r.size_bytes} | {r.text_word_count if r.text_word_count is not None else 'n/a'} | {'; '.join(meta_bits)} |"
        )

    lines += [
        "",
        "## Primary Text Inference",
        "",
        f"- Candidate: `{Path(inference['primary_candidate']).name if inference.get('primary_candidate') else 'none'}`",
        f"- Confidence: `{inference.get('confidence')}`",
        f"- Summary: {inference.get('summary')}",
        "- Evidence:",
    ]
    for item in inference.get("evidence", []):
        lines.append(f"  - {item}")

    lines += [
        "",
        "## Notes",
        "",
        "- Confidence is constrained by missing explicit revision log linking manuscript file names to image manifests.",
        "- Confirm final manuscript choice with editor before full image generation.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--files",
        nargs="+",
        default=[
            "Geometry_First_Mathematics_Expanded_Intuition_Edition.docx",
            "Geometry_First_Mathematics_Visually_Informed_Expanded_Edition_v3.docx",
            "Geometry_First_Mathematics_Expanded_Intuition_Edition.pdf",
        ],
    )
    ap.add_argument("--out-json", default="image-production/reports/manuscript_metadata.json")
    ap.add_argument("--out-md", default="image-production/reports/manuscript_metadata.md")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    records: list[ManuscriptRecord] = []

    for raw in args.files:
        path = Path(raw)
        if not path.exists():
            continue
        if path.suffix.lower() == ".docx":
            records.append(read_docx(path))
        elif path.suffix.lower() == ".pdf":
            records.append(read_pdf(path))

    if not records:
        raise SystemExit("No manuscript files found.")

    inference = infer_primary(records)
    payload = {
        "records": [
            {
                "path": r.path,
                "kind": r.kind,
                "size_bytes": r.size_bytes,
                "sha256": r.sha256,
                "mtime_utc_ns": r.mtime_utc,
                "metadata": r.metadata,
                "text_preview": r.text_preview,
                "text_word_count": r.text_word_count,
            }
            for r in records
        ],
        "inference": inference,
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(to_markdown(records, inference), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
