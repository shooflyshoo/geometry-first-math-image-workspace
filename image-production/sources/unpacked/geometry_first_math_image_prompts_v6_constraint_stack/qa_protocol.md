# V6 QA protocol

## Pilot pass

1. Generate the 20 pilot prompts first.
2. Use `gpt-image-1.5` explicitly.
3. Use `quality="high"` for pilot prompts even when their library default is medium.
4. Generate exactly 3 variants for each pilot prompt.
5. Review variants side by side before choosing or rewriting.

## Reject a variant when

- It contains any generated letters, numerals, formulas, diagram labels, pseudo-script, signage, or watermark.
- The viewer cannot identify the focal action within two seconds.
- The image contains more conceptual actions than the prompt authorizes.
- A technical construction looks precise enough to be trusted but is geometrically wrong.
- A recurring motif has drifted from the approved system reference asset.

## Keep a variant when

- It reveals exactly one conceptual move.
- It leaves clean space for vector overlays.
- It supports the section without re-teaching the whole book.
- It feels visually generous, not crowded.
- It belongs to its visual family but does not feel like a repeated template.

## Automated checks

Run OCR/text detection if available. Treat hits as flags for human review, not automatic failure. For recurring motif consistency, compare selected variants to approved SYS.1/SYS.2/SYS.3 reference assets by eye before production embedding.
