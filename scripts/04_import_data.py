"""
Step 4: Import Data to Supabase
=================================
Reads data/sentences_with_embeddings.json and imports all records
into the sentence_embeddings table in Supabase.

If the table already contains data, it will be truncated first
so you can safely re-run this script.

Usage:
    python scripts/04_import_data.py

Input:
    data/sentences_with_embeddings.json  — from Step 3

Prerequisites:
    - config.secret.json with Supabase credentials
    - Database schema created (Step 1)
    - Embeddings generated (Step 3)
"""

import json
import os
import sys
import time

from supabase import create_client
from tqdm import tqdm


INPUT_FILE = os.path.join('data', 'sentences_with_embeddings.json')
BATCH_SIZE = 100


def load_secrets():
    with open('config.secret.json', 'r') as f:
        return json.load(f)


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} not found. Run scripts/03_embed_data.py first.")
        sys.exit(1)

    # Load data
    print("Loading embeddings data...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)
    print(f"   Loaded {len(records):,} sentence records\n")

    # Connect to Supabase
    secrets = load_secrets()
    client = create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_SERVICE_KEY'])

    # Check for existing data and truncate if needed
    print("=" * 60)
    print("Checking for existing data...")
    print("=" * 60)

    try:
        result = client.table('sentence_embeddings').select('id', count='exact').limit(1).execute()
        existing_count = result.count or 0
        if existing_count > 0:
            print(f"   Found {existing_count:,} existing rows. Truncating table...")
            # Delete all rows (Supabase doesn't support TRUNCATE via client, so use delete with a filter that matches all)
            client.table('sentence_embeddings').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print("   ✅ Table truncated.")
        else:
            print("   Table is empty — ready for import.")
    except Exception as e:
        print(f"   ⚠️ Could not check existing data: {e}")
        print("   Proceeding with import anyway...")

    # Import in batches
    print("\n" + "=" * 60)
    print(f"Importing {len(records):,} records to Supabase")
    print("=" * 60)

    # Convert embedding lists (they should already be lists from JSON)
    for record in records:
        if hasattr(record.get('embedding'), 'tolist'):
            record['embedding'] = record['embedding'].tolist()

    success = 0
    errors = 0

    for i in tqdm(range(0, len(records), BATCH_SIZE), desc="Importing"):
        batch = records[i:i + BATCH_SIZE]
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
    print(f"\n🎉 Done! Refresh your site to see search panels light up.")


if __name__ == '__main__':
    main()
