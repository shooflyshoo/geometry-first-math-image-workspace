# Manifest Summary

## Core Counts

- Pilot prompts (v6): **20**
- Full blueprint prompts (v6): **265**
- Priority regen prompts (v6): **71**
- Batch jobs (section manifests): **175**
- Subsection jobs: **163**
- Extra jobs: **12**

## Pilot Requirements Check

- Pilot prompt count is 20: **True**
- Pilot recommended variants are all 3: **True**

## Section Manifest Counts

| Section | Count |
|---|---:|
| `0` | 8 |
| `1` | 8 |
| `2` | 7 |
| `3` | 9 |
| `4` | 10 |
| `5` | 8 |
| `6` | 8 |
| `7` | 5 |
| `8` | 5 |
| `9` | 6 |
| `10` | 9 |
| `11` | 7 |
| `12` | 8 |
| `13` | 6 |
| `14` | 6 |
| `15` | 6 |
| `16` | 10 |
| `17` | 7 |
| `18` | 7 |
| `19` | 7 |
| `A` | 8 |
| `B` | 8 |
| `EXTRA` | 12 |

## Format Mix

| Format | Count |
|---|---:|
| `B` | 21 |
| `D` | 32 |
| `F` | 6 |
| `H` | 61 |
| `M` | 20 |
| `S` | 15 |
| `V` | 20 |

## Suggested Generation Order

1. `geometry_first_math_image_prompts_v6_pilot_20.jsonl` (3 variants each; visual language lock)
2. Batch sections `0,1,2,3`
3. Batch sections `4,5,6,7`
4. Batch sections `8,9,10,11`
5. Interludes and bridges `A,12,13,B`
6. Advanced arc `14,15,16,17`
7. Final arc `18,19`
8. `extras.jsonl`

## Validation Result

- Status: **PASS**
