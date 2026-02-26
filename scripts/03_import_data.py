"""
Step 3: Import Talk Data to Supabase
======================================
Reads data/talks.json, splits each talk into sentences,
and imports the text records to Supabase (without embeddings).

After this step, KEYWORD SEARCH will light up green on your site!
Embeddings are added in the next step to enable semantic search.

Usage:
    python scripts/03_import_data.py

Input:
    data/talks.json  — from Step 2 (scraping)

Prerequisites:
    - config.public.json with Supabase URL and anon key
    - config.secret.json with Supabase service key
    - Database schema created (Step 1)
    - Talks scraped (Step 2)
"""

import json
import os
import re
import sys
import time
import uuid

from supabase import create_client
from tqdm import tqdm


INPUT_FILE = os.path.join('data', 'talks.json')
BATCH_SIZE = 100


def load_config():
    with open('config.public.json', 'r') as f:
        public_config = json.load(f)
    with open('config.secret.json', 'r') as f:
        secrets = json.load(f)
    return public_config, secrets


def split_into_sentences(text):
    """Split text into sentences using a simple heuristic."""
    sentences = re.split(r'\. (?=[A-Z])', text)
    sentences = [s.strip() + '.' if not s.endswith('.') else s.strip() for s in sentences]
    return [s for s in sentences if len(s) > 20]


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} not found. Run scripts/02_scrape_data.py first.")
        sys.exit(1)

    # Load talks
    print("=" * 60)
    print("Importing Talk Data to Supabase")
    print("=" * 60)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        talks = json.load(f)
    print(f"   Loaded {len(talks)} talks\n")

    # Split into sentence records (no embeddings yet)
    print("Splitting talks into sentences...")
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
                # No 'embedding' field — added in next step
            })

    print(f"✅ Split {len(talks)} talks into {len(sentence_records):,} sentences")
    print(f"   Average: {len(sentence_records) / len(talks):.1f} sentences per talk\n")

    # Connect to Supabase
    public_config, secrets = load_config()
    client = create_client(public_config['SUPABASE_URL'], secrets['SUPABASE_SERVICE_KEY'])

    # Check for existing data and truncate if needed
    print("=" * 60)
    print("Checking for existing data...")
    print("=" * 60)

    try:
        result = client.table('sentence_embeddings').select('id', count='exact').limit(1).execute()
        existing_count = result.count or 0
        if existing_count > 0:
            print(f"   Found {existing_count:,} existing rows. Truncating table...")
            client.table('sentence_embeddings').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print("   ✅ Table truncated.")
        else:
            print("   Table is empty — ready for import.")
    except Exception as e:
        print(f"   ⚠️ Could not check existing data: {e}")
        print("   Proceeding with import anyway...")

    # Import in batches
    print("\n" + "=" * 60)
    print(f"Importing {len(sentence_records):,} records to Supabase")
    print("=" * 60)
    print("   (Text only — embeddings will be added in the next step)\n")

    success = 0
    errors = 0

    for i in tqdm(range(0, len(sentence_records), BATCH_SIZE), desc="Importing"):
        batch = sentence_records[i:i + BATCH_SIZE]
        try:
            client.table('sentence_embeddings').insert(batch).execute()
            success += len(batch)
        except Exception as e:
            print(f"\nError at batch {i // BATCH_SIZE}: {e}")
            errors += len(batch)
        time.sleep(0.1)

    print(f"\n✅ Import complete!")
    print(f"   Success: {success:,}")
    if errors:
        print(f"   Errors:  {errors:,}")

    # Final verification
    result = client.table('sentence_embeddings').select('id', count='exact').limit(1).execute()
    print(f"\n   Total rows in database: {result.count or 0:,}")

    print(f"\n🎉 Keyword Search is now ready!")
    print(f"   Refresh your site — the 🔍 Keyword Search panel should turn GREEN.")
    print(f"\nNext: python scripts/04_embed_and_update.py")


if __name__ == '__main__':
    main()
