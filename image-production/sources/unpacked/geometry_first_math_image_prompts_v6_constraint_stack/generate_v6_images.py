#!/usr/bin/env python3
"""Batch runner template for Geometry-First Mathematics v6 image prompts.

Usage:
  export OPENAI_API_KEY=...
  python generate_v6_images.py --manifest geometry_first_math_image_prompts_v6_pilot_20.jsonl --out images/pilot --force-quality high --force-variants 3
  python generate_v6_images.py --manifest geometry_first_math_image_prompts_v6_constraint_stack.jsonl --out images/full
"""
import argparse, base64, json, pathlib, time
from openai import OpenAI


def load_jobs(path):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--model', default=None)
    ap.add_argument('--force-quality', default=None, choices=['low','medium','high','auto'])
    ap.add_argument('--force-size', default=None, choices=['1024x1024','1536x1024','1024x1536','auto'])
    ap.add_argument('--force-variants', type=int, default=None)
    ap.add_argument('--sleep', type=float, default=0.0)
    args = ap.parse_args()

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    client = OpenAI()

    for job in load_jobs(args.manifest):
        model = args.model or job.get('recommended_model') or 'gpt-image-1.5'
        quality = args.force_quality or job.get('api_quality') or 'medium'
        size = args.force_size or job.get('api_size') or '1536x1024'
        n = args.force_variants or int(job.get('recommended_variants') or 1)
        prompt_id = job['prompt_id']
        prompt = job['assembled_prompt']
        print(f'Generating {prompt_id}: n={n}, model={model}, quality={quality}, size={size}')
        result = client.images.generate(
            model=model,
            prompt=prompt,
            n=n,
            quality=quality,
            size=size,
            output_format=job.get('api_output_format','png'),
            background=job.get('api_background','opaque'),
        )
        for i, item in enumerate(result.data, start=1):
            image_bytes = base64.b64decode(item.b64_json)
            filename = f"{prompt_id}_{i:02d}.png"
            (outdir / filename).write_bytes(image_bytes)
        meta = outdir / f"{prompt_id}.json"
        meta.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
        if args.sleep:
            time.sleep(args.sleep)

if __name__ == '__main__':
    main()
