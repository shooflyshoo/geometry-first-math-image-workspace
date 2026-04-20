# Geometry-First Mathematics Image Prompt Blueprint v6

This package contains the v6 constraint-stack prompt library for the Geometry-First Mathematics book.

## Files

- `geometry_first_math_image_prompts_v6_constraint_stack.json` - full structured library.
- `geometry_first_math_image_prompts_v6_constraint_stack.jsonl` - batch generation manifest.
- `geometry_first_math_image_prompts_v6_pilot_20.jsonl` - the 20-prompt pilot set. Run this first.
- `geometry_first_math_image_prompts_v6_priority_regen.jsonl` - medium/high priority prompts and pilot-critical prompts.
- `geometry_first_math_image_prompts_v6_constraint_stack.csv` - review index.
- `generate_v6_images.py` - batch runner template.
- `qa_protocol.md` - pilot and image QA protocol.
- `Geometry_First_Mathematics_Image_Prompt_Blueprint_v6_Constraint_Stack.md` - human-readable blueprint source.

## Operating rule

Do not generate all 265 prompt cards at once. Run the 20-prompt pilot first with 3 variants each. Approve the visual language, then batch the rest section-by-section.

## Prompt structure

Every prompt follows this stack:

Scene -> Subject -> Conceptual action -> Composition -> Materials / medium -> Surface / text policy -> Use

Do not append extra style poetry. If a line does not control behavior, remove it.
