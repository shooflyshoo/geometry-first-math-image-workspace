#!/usr/bin/env python3
"""Estimate image generation cost for a manifest.
Default prices reflect the OpenAI GPT Image 1.5 model page at the time this package was produced.
Confirm current pricing before production.
"""
import argparse, json

DEFAULT_PRICES = {
    ('low','1024x1024'): 0.009, ('low','1024x1536'): 0.013, ('low','1536x1024'): 0.013,
    ('medium','1024x1024'): 0.034, ('medium','1024x1536'): 0.050, ('medium','1536x1024'): 0.050,
    ('high','1024x1024'): 0.133, ('high','1024x1536'): 0.200, ('high','1536x1024'): 0.200,
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    args = ap.parse_args()
    count = 0; total = 0.0
    by = {}
    for line in open(args.manifest, encoding='utf-8'):
        if not line.strip(): continue
        job = json.loads(line)
        q = job.get('api_quality','medium')
        s = job.get('api_size','1536x1024')
        n = int(job.get('recommended_variants') or 1)
        price = DEFAULT_PRICES.get((q,s))
        if price is None:
            price = DEFAULT_PRICES.get((q,'1536x1024'), 0.05)
        count += n; total += n * price
        by[(q,s)] = by.get((q,s),0) + n
    print('Images:', count)
    for (q,s), n in sorted(by.items()):
        print(f'{q:>6} {s:>9}: {n:4d} images @ ${DEFAULT_PRICES.get((q,s), 0):.3f} default each')
    print(f'Estimated output cost: ${total:,.2f}')

if __name__ == '__main__':
    main()
