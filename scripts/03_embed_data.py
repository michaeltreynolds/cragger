"""
Step 3: Split into Sentences & Generate Embeddings
=====================================================
Reads data/talks.json, splits each talk into sentences,
generates OpenAI embeddings, and saves the result.

Usage:
    python scripts/03_embed_data.py

Input:
    data/talks.json  — from Step 2

Output:
    data/sentences_with_embeddings.json  — sentence records with embedding vectors

Prerequisites:
    - config.secret.json with OPENAI_API_KEY
    - data/talks.json from the scraping step
"""

import json
import os
import re
import sys
import time
import uuid

from openai import OpenAI
from tqdm import tqdm


INPUT_FILE = os.path.join('data', 'talks.json')
OUTPUT_FILE = os.path.join('data', 'sentences_with_embeddings.json')
BATCH_SIZE = 100


def load_secrets():
    with open('config.secret.json', 'r') as f:
        return json.load(f)


def split_into_sentences(text):
    """Split text into sentences using a simple heuristic."""
    sentences = re.split(r'\. (?=[A-Z])', text)
    sentences = [s.strip() + '.' if not s.endswith('.') else s.strip() for s in sentences]
    return [s for s in sentences if len(s) > 20]


def main():
    # Load talks
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} not found. Run scripts/02_scrape_data.py first.")
        sys.exit(1)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        talks = json.load(f)

    print("=" * 60)
    print("Splitting Talks into Sentences")
    print("=" * 60)

    # Split into sentence records
    sentence_records = []
    for talk in tqdm(talks, desc="Splitting"):
        talk_id = str(uuid.uuid4())
        sentences = split_into_sentences(talk['text'])
        for i, sentence in enumerate(sentences, 1):
            sentence_records.append({
                'talk_id': talk_id,
                'title': talk['title'],
                'speaker': talk['speaker'],
                'calling': talk['calling'],
                'year': int(talk['year']) if talk['year'] else None,
                'season': talk['season'],
                'url': talk['url'],
                'sentence_num': i,
                'text': sentence
            })

    print(f"✅ Split {len(talks)} talks into {len(sentence_records):,} sentences")
    print(f"   Average: {len(sentence_records) / len(talks):.1f} sentences per talk")

    # Generate embeddings
    print("\n" + "=" * 60)
    print("Generating OpenAI Embeddings")
    print("=" * 60)

    secrets = load_secrets()
    client = OpenAI(api_key=secrets['OPENAI_API_KEY'])

    print(f"Generating embeddings for {len(sentence_records):,} sentences...")
    print(f"Batch size: {BATCH_SIZE}\n")

    embeddings = []
    for i in tqdm(range(0, len(sentence_records), BATCH_SIZE), desc="Embedding"):
        batch_texts = [r['text'] for r in sentence_records[i:i + BATCH_SIZE]]
        try:
            response = client.embeddings.create(model='text-embedding-3-small', input=batch_texts)
            embeddings.extend([item.embedding for item in response.data])
        except Exception as e:
            print(f"\nError at batch {i // BATCH_SIZE}: {e}")
            embeddings.extend([None] * len(batch_texts))
        time.sleep(0.1)

    # Attach embeddings to records
    valid_records = []
    for record, embedding in zip(sentence_records, embeddings):
        if embedding is not None:
            record['embedding'] = embedding
            valid_records.append(record)

    print(f"\n✅ Generated {len(valid_records):,} embeddings")
    if len(valid_records) < len(sentence_records):
        print(f"   ⚠️ {len(sentence_records) - len(valid_records)} failed (removed)")

    # Estimate cost
    total_chars = sum(len(r['text']) for r in valid_records)
    est_tokens = total_chars / 4  # rough estimate
    cost = (est_tokens / 1_000_000) * 0.020
    print(f"   💰 Estimated cost: ${cost:.2f}")

    # Save output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(valid_records, f, ensure_ascii=False)

    file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\n✅ Saved to {OUTPUT_FILE} ({file_size_mb:.1f} MB)")
    print(f"\nNext: python scripts/04_import_data.py")


if __name__ == '__main__':
    main()
