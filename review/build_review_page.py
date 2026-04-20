#!/usr/bin/env python3
from __future__ import annotations
import json, re, zipfile
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / 'image-production/sources/unpacked/geometry_first_math_image_prompts_v6_constraint_stack/geometry_first_math_image_prompts_v6_pilot_20.jsonl'
DOCX = ROOT / 'image-production/sources/originals/Geometry_First_Mathematics_Expanded_Intuition_Edition_Fresh.docx'
OUT_JSON = ROOT / 'review/pilot-review-data.json'

OVERRIDES = {
    'GFV6-0_7-A': {'anchor_index_hint': 147},
    'GFV6-4_3-A': {'search': 'The Eudoxus definition'},
    'GFV6-6_1-B': {'search': 'Division as inverse scaling'},
}

def norm(s: str) -> str:
    s = s.replace('’', "'").replace('“', '"').replace('”', '"')
    s = re.sub(r'\s+', ' ', s.strip().lower())
    s = re.sub(r'[^a-z0-9 ]+', '', s)
    return s

def load_paragraphs(docx_path: Path):
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    paras_xml = re.findall(r'<w:p[\s\S]*?</w:p>', xml)
    paras = []
    for pxml in paras_xml:
        txt = ' '.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', pxml)).strip()
        if txt:
            paras.append(txt)
    return paras

def best_match(title: str, paras: list[str], prompt_id: str):
    override = OVERRIDES.get(prompt_id, {})
    if 'anchor_index_hint' in override:
        idx = override['anchor_index_hint']
        return idx, 1.0, 'manual-index-hint'
    targets = [title]
    if 'search' in override:
        targets.insert(0, override['search'])
    best = (-1, -1.0, 'fuzzy')
    nparas = [norm(p) for p in paras]
    for target in targets:
        nt = norm(target)
        exacts = [i for i, p in enumerate(nparas) if nt and nt in p]
        if exacts:
            return exacts[0], 1.0, f'exact:{target}'
        for i, p in enumerate(nparas):
            score = SequenceMatcher(None, nt, p).ratio()
            if score > best[1]:
                best = (i, score, f'fuzzy:{target}')
    return best

def excerpt(paras: list[str], idx: int, window: int = 2):
    start = max(0, idx - window)
    end = min(len(paras), idx + window + 1)
    return paras[start:end], start, end - 1

paras = load_paragraphs(DOCX)
items = []
for line in PILOT.read_text().splitlines():
    obj = json.loads(line)
    idx, score, method = best_match(obj['title'], paras, obj['prompt_id'])
    snippets, start, end = excerpt(paras, idx)
    image_matches = sorted((ROOT / 'image-production/output/pilot-20').glob(f"{obj['prompt_id']}.*"))
    image_rel = image_matches[0].relative_to(ROOT).as_posix() if image_matches else None
    items.append({
        'prompt_id': obj['prompt_id'],
        'section_id': obj['section_id'],
        'title': obj['title'],
        'placement': obj.get('placement'),
        'caption': obj.get('caption'),
        'role': obj.get('role'),
        'prompt': obj.get('prompt'),
        'image': image_rel,
        'match': {'paragraph_index': idx, 'score': round(score, 3), 'method': method},
        'excerpt_range': [start, end],
        'excerpt': snippets,
    })
OUT_JSON.write_text(json.dumps({'source_docx': DOCX.relative_to(ROOT).as_posix(), 'items': items}, indent=2), encoding='utf-8')
print(f'Wrote {OUT_JSON}')
