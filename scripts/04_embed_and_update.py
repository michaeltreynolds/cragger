"""
Step 4: Generate Embeddings & Update Database
================================================
Generates OpenAI embeddings for sentences already in the database
and updates each row with its embedding vector.

After this step, SEMANTIC SEARCH will light up green on your site!

Usage:
    python scripts/04_embed_and_update.py

Prerequisites:
    - config.public.json with Supabase URL and anon key
    - config.secret.json with OpenAI API key and Supabase service key
    - Database populated with text data (Step 3)
"""

import json
import os
import sys
import time

from openai import OpenAI
from supabase import create_client
from tqdm import tqdm


BATCH_SIZE = 100


def load_config():
    with open('config.public.json', 'r') as f:
        public_config = json.load(f)
    with open('config.secret.json', 'r') as f:
        secrets = json.load(f)
    return public_config, secrets


def main():
    public_config, secrets = load_config()

    # Connect to Supabase
    client = create_client(public_config['SUPABASE_URL'], secrets['SUPABASE_SERVICE_KEY'])
    openai_client = OpenAI(api_key=secrets['OPENAI_API_KEY'])

    # Fetch all rows that don't have embeddings yet
    print("=" * 60)
    print("Checking for sentences without embeddings...")
    print("=" * 60)

    # Count rows needing embeddings
    total_result = client.table('sentence_embeddings').select('id', count='exact').limit(1).execute()
    total_rows = total_result.count or 0

    embedded_result = client.table('sentence_embeddings') \
        .select('id', count='exact') \
        .not_('embedding', 'is', 'null') \
        .limit(1).execute()
    embedded_rows = embedded_result.count or 0

    needs_embedding = total_rows - embedded_rows

    if total_rows == 0:
        print("❌ No data in the database. Run scripts/03_import_data.py first.")
        sys.exit(1)

    if needs_embedding == 0:
        print(f"✅ All {total_rows:,} rows already have embeddings. Nothing to do!")
        return

    print(f"   Total rows:        {total_rows:,}")
    print(f"   Already embedded:  {embedded_rows:,}")
    print(f"   Need embedding:    {needs_embedding:,}\n")

    # Fetch rows without embeddings in pages
    print("=" * 60)
    print(f"Generating embeddings for {needs_embedding:,} sentences")
    print("=" * 60)
    print(f"   Model: text-embedding-3-small (1,536 dimensions)")
    print(f"   Batch size: {BATCH_SIZE}\n")

    # Process in pages to avoid memory issues
    page_size = 1000
    total_updated = 0
    total_errors = 0
    offset = 0

    while True:
        # Fetch a page of rows without embeddings
        result = client.table('sentence_embeddings') \
            .select('id, text') \
            .is_('embedding', 'null') \
            .limit(page_size) \
            .execute()

        rows = result.data
        if not rows:
            break

        # Process this page in embedding batches
        for i in tqdm(range(0, len(rows), BATCH_SIZE),
                      desc=f"Embedding (batch {offset // page_size + 1})",
                      total=(len(rows) + BATCH_SIZE - 1) // BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            batch_texts = [r['text'] for r in batch]

            try:
                response = openai_client.embeddings.create(
                    model='text-embedding-3-small',
                    input=batch_texts
                )

                # Update each row with its embedding
                for row, item in zip(batch, response.data):
                    try:
                        client.table('sentence_embeddings') \
                            .update({'embedding': item.embedding}) \
                            .eq('id', row['id']) \
                            .execute()
                        total_updated += 1
                    except Exception as e:
                        print(f"\n   ⚠️ Failed to update row {row['id']}: {e}")
                        total_errors += 1

            except Exception as e:
                print(f"\n   ❌ Embedding batch error: {e}")
                total_errors += len(batch)

            time.sleep(0.1)

        offset += page_size

    # Summary
    print(f"\n✅ Embedding complete!")
    print(f"   Updated:  {total_updated:,}")
    if total_errors:
        print(f"   Errors:   {total_errors:,}")

    # Estimate cost
    est_tokens = total_updated * 25 / 4  # ~25 chars per sentence, ~4 chars per token
    cost = (est_tokens / 1_000_000) * 0.020
    print(f"   💰 Estimated cost: ${cost:.2f}")

    # Verify
    final = client.table('sentence_embeddings') \
        .select('id', count='exact') \
        .not_('embedding', 'is', 'null') \
        .limit(1).execute()
    print(f"\n   Rows with embeddings: {final.count or 0:,} / {total_rows:,}")

    print(f"\n🎉 Semantic Search is now ready!")
    print(f"   Refresh your site — the 🧠 Semantic Search panel should turn GREEN.")
    print(f"\nNext: Deploy edge functions to light up 🤖 RAG!")


if __name__ == '__main__':
    main()
