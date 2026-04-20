# Findings Report

Date: 2026-04-20 (UTC)

## 1) Workspace Preparation

- Unpacked:
  - `Geometry_First_Mathematics_Image_Prompt_Blueprint_v6_Constraint_Stack_Package.zip`
  - `Geometry_First_Math_Image_Batch_Kit.zip`
- Unpacked sources are in `image-production/sources/unpacked/`.
- Stable source links are in `image-production/sources/originals/`.

## 2) Manifest and Pilot Reality Check

Validated via `image-production/scripts/validate_manifests.py`:

- Blueprint pilot: 20 prompts, all with `recommended_variants=3`.
- Blueprint full set: 265 prompts.
- Priority regen set: 71 prompts.
- Batch jobs: 175 total (`163` subsection + `12` extras).
- Section manifests present and consistent: `section_0..section_19`, `section_A`, `section_B`, `extras`.

This matches the package guidance:
- Run pilot first (20 prompts x 3 variants).
- Generate remaining jobs section-by-section.

## 3) Manuscript Primary-Text Assessment

Evidence from repository contents:

- `Geometry_First_Mathematics_Expanded_Intuition_Edition.pdf` metadata `CreationDate` is **April 18, 2026 01:59:24 UTC** and strongly matches
  `Geometry_First_Mathematics_Expanded_Intuition_Edition.docx` text.
- `Geometry_First_Mathematics_Visually_Informed_Expanded_Edition_v3.docx` is larger and explicitly labeled `v3` in filename.
- Both `.docx` files share very similar core metadata timestamps and titles.

Practical inference:

- **Provisional primary candidate:** `Geometry_First_Mathematics_Expanded_Intuition_Edition.docx` (because it aligns with the PDF).
- **Uncertainty remains:** the larger `...Visually_Informed_..._v3.docx` may be a later expansion branch.

Conclusion: manuscript choice is **ambiguous** from repository artifacts alone and should be confirmed by the editorial owner before full generation.

## 4) Minimal Usability Improvements Added

- Added reproducible setup script: `scripts/prepare_workspace.sh`.
- Added pilot + section dry-run validator: `scripts/validate_manifests.py`.
- Added manuscript metadata extractor: `scripts/summarize_manuscripts.py`.
- Added one-command dry-run wrapper: `scripts/dry_run_validate.sh`.
- Added workflow docs and generated manifest summary for handoff.

## 5) Next Step

- Confirm which manuscript is authoritative (`Expanded_Intuition` vs `Visually_Informed_v3`).
- Then run the pilot generation only (20 prompts, 3 variants each), QA that visual language, and proceed section-by-section.

## Update, fresh manuscript received

- Primary working manuscript is now `Geometry_First_Mathematics_Expanded_Intuition_Edition_Fresh.docx`.
- This file was provided directly after the initial workspace setup and should be treated as the current editorial source for image alignment unless replaced by a newer revision.
- Earlier manuscript ambiguity is now superseded for pilot work.

