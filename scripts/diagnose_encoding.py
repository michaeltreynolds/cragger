"""Verify the re-imported data has correct UTF-8 encoding."""
import json
from supabase import create_client

with open('config.secret.json', 'r') as f:
    secrets = json.load(f)

client = create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_SERVICE_KEY'])

# Count total rows
result = client.table('sentence_embeddings').select('*', count='exact').limit(1).execute()
print(f"Total rows: {result.count}")

# Check for Caussé (accented name)
r2 = client.table('sentence_embeddings').select('speaker,title,text').ilike('speaker', '%auss%').limit(3).execute()
print(f"\nCaussé results: {len(r2.data)}")
for row in r2.data:
    print(f"  Speaker: {row['speaker']}")
    print(f"  Title:   {row['title'][:60]}")
    print(f"  Text:    {row['text'][:100]}")
    print()

# Check for smart quotes (the other mojibake example)
r3 = client.table('sentence_embeddings').select('text').ilike('text', "%Savior's%").limit(2).execute()
print(f"Smart quote results: {len(r3.data)}")
for row in r3.data[:2]:
    print(f"  {row['text'][:120]}")

# Check for mojibake indicators in all data
r4 = client.table('sentence_embeddings').select('text').ilike('text', '%Ã©%').limit(5).execute()
print(f"\nMojibake check (Ã©): {len(r4.data)} rows found {'⚠️ STILL CORRUPTED' if r4.data else '✅ CLEAN'}")

r5 = client.table('sentence_embeddings').select('speaker').ilike('speaker', '%Ã%').limit(5).execute()
print(f"Mojibake check (speaker Ã): {len(r5.data)} rows found {'⚠️ STILL CORRUPTED' if r5.data else '✅ CLEAN'}")
