# Geometry-First Mathematics image batch kit

This kit turns the subsection prompt library into a runnable OpenAI image-generation workflow.

## What is in here

- `geometry_first_math_image_jobs.json` — full enriched manifest for all jobs
- `geometry_first_math_image_jobs.jsonl` — one JSON object per job, ready for scripting
- `geometry_first_math_image_jobs.csv` — spreadsheet-friendly index
- `manifests/` — section-by-section JSONL manifests so you can generate chapter by chapter
- `generate_geometry_first_math_images.py` — Python batch runner using the OpenAI Images API
- `output/` — default image output folder
- `metadata/` — companion metadata folder for saved responses

## Coverage

- 163 subsection images
- 12 extras (cover, part openers, appendix plates)
- 175 total image jobs

## Prompt assembly

Each job prompt is assembled from:
1. the blueprint master preamble
2. the subsection role
3. the layout code and layout label
4. the style direction
5. the core image brief
6. the caption intent
7. the overlay note
8. the negative block

This makes the prompts immediately usable with OpenAI image generation without having to hand-stitch every subsection prompt again.

## Default layout mapping used in this kit

- `F` → `1024x1536`
- `V` → `1024x1536`
- `H` → `1536x1024`
- `B` → `1536x1024`
- `D` → `1536x1024`
- `S` → `1536x1024`
- `M` → `1024x1024`

All jobs default to `quality="high"` and `background="opaque"` in the manifest. Override globally from the command line if you want a different run.

## Quick start

```bash
export OPENAI_API_KEY=YOUR_KEY_HERE
python generate_geometry_first_math_images.py
```

Generate only one section:

```bash
python generate_geometry_first_math_images.py \
  --manifest manifests/section_00.jsonl \
  --output-dir output/section_00 \
  --metadata-dir metadata/section_00
```

Generate only selected subsection IDs:

```bash
python generate_geometry_first_math_images.py --ids 0.1 0.2 0.3
```

Generate only extras:

```bash
python generate_geometry_first_math_images.py --kind extra --output-dir output/extras
```

Preview the run without calling the API:

```bash
python generate_geometry_first_math_images.py --match 16. --limit 3 --dry-run
```

Save multiple variants per prompt:

```bash
python generate_geometry_first_math_images.py --manifest manifests/section_04.jsonl --n 3
```

## Suggested production workflow

1. Generate Sections 0–3 first to lock the visual language.
2. Generate Sections 4–7 next; these are the ratio / similarity / division spine.
3. Treat `D` jobs as hybrid plates. Use the generated art as base imagery, then overlay exact axes, labels, tick marks, or theorem marks in layout.
4. Treat `M` jobs as optional margin sketches if the page feels dense.
5. Keep the generated metadata JSON files. They preserve the request data and help with later revisions.

## Notes for the mathematically exact plates

Jobs marked `D` are intentionally designed as hybrid diagram plates rather than fully self-contained final diagrams. The art should carry the intuition and mood; exact mathematical labeling should usually be added later in layout.

## File naming

Files are prefixed by sequence number so the output order matches the document’s pedagogical sequence. Example:

- `001_0_1_magnitudes_are_older_than_numerals.png`
- `002_0_2_same_without_counting.png`
- `...`

## Manifest schema

Key fields include:

- `sequence`
- `kind`
- `id`
- `section`
- `title`
- `format`
- `layout_label`
- `size`
- `quality`
- `background`
- `filename`
- `caption`
- `overlay`
- `prompt_core`
- `api_prompt`

## Recommended way to work

Do not try to generate all 175 blind and trust the first pass. Generate in section batches, review, tighten the repeat motifs, then continue. This manuscript lives or dies by conceptual continuity.
