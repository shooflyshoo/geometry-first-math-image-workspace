# Geometry First Math Image Workspace

This is a shareable working workspace for the image-production pipeline for the Geometry-First Mathematics book.

## What is here

- `image-production/README.md` for the workflow
- `image-production/findings.md` for current findings
- `image-production/manifest-summary.md` for counts and rollout order
- `image-production/output/pilot-20/` for the first 20 generated pilot images
- `review/index.html` for the review page that pairs pilot images with manuscript excerpts
- `image-production/scripts/` for manifest validation and manuscript summarization
- `image-production/sources/unpacked/` for the unpacked prompt kits and manifests

## Current scope

This workspace is set up for a pilot-first workflow.
The 20-prompt pilot has been generated for review before any wider rollout.

## Review page

Run locally in Codespaces or any shell with:

```bash
cd review
python3 -m http.server 8000
```

Then open the forwarded port and visit `index.html`.

## Notes

- This repo is intended as a preview and collaboration workspace.
- Pilot images are first-pass review renders and should be evaluated before broader generation.
