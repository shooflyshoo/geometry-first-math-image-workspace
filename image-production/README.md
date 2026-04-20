# Image Production Workspace

This folder is a dry-run-safe workspace for the Geometry-First Mathematics image pipeline.

## What Is Included

- `sources/originals/`:
  - symlinks to repo-root source assets (`.zip`, `.docx`, `.pdf`)
- `sources/unpacked/`:
  - unpacked blueprint package and batch kit
- `scripts/prepare_workspace.sh`:
  - reproducible unpack/setup script
- `scripts/summarize_manuscripts.py`:
  - extracts manuscript metadata and text previews from `.docx`/`.pdf`
- `scripts/validate_manifests.py`:
  - validates pilot/full/section manifests and writes summaries
- `scripts/dry_run_validate.sh`:
  - end-to-end dry-run wrapper (no paid API calls)
- `manifest-summary.md`:
  - generated manifest counts, section breakdown, and suggested generation order
- `reports/`:
  - machine-readable and human-readable outputs from validation/metadata scripts
- `findings.md`:
  - concise conclusions and recommended next action

## Recommended Workflow For This Repo

1. Prepare workspace (safe to re-run):

```bash
./image-production/scripts/prepare_workspace.sh
```

2. Run dry-run validations and regenerate reports:

```bash
./image-production/scripts/dry_run_validate.sh
```

3. Review generated outputs:

- `image-production/reports/manuscript_metadata.md`
- `image-production/manifest-summary.md`
- `image-production/findings.md`

4. Start production manually (outside this dry-run task) in this order:

1. `geometry_first_math_image_prompts_v6_pilot_20.jsonl` with 3 variants each
2. Batch sections `0,1,2,3`
3. Batch sections `4,5,6,7`
4. Batch sections `8,9,10,11`
5. Interludes and bridges `A,12,13,B`
6. Advanced arc `14,15,16,17`
7. Final arc `18,19`
8. `extras.jsonl`

## Notes

- No paid image API calls are made by the helper tooling in this workspace.
- Existing batch generator already supports `--dry-run`; this workspace wraps it with `python3` and adds manifest-level pilot validation.
- The batch kit README example uses `section_00.jsonl`, but actual files are `section_0.jsonl` ... `section_19.jsonl`.
