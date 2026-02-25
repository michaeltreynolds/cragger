"""
Step 1: Create Database Schema
================================
Creates the sentence_embeddings table, pgvector extension,
Row Level Security policies, and the match_sentences() function
in your Supabase database.

Usage:
    python scripts/01_create_schema.py

Prerequisites:
    - config.secret.json with valid Supabase credentials
    - Supabase project created
"""

import json
import sys
import time

# Load secrets
with open('config.secret.json', 'r') as f:
    secrets = json.load(f)

SUPABASE_URL = secrets['SUPABASE_URL']
SUPABASE_SERVICE_KEY = secrets['SUPABASE_SERVICE_KEY']
SUPABASE_ACCESS_TOKEN = secrets['SUPABASE_ACCESS_TOKEN']
SUPABASE_PROJECT_REF = secrets['SUPABASE_PROJECT_REF']


def create_schema():
    import requests
    from supabase import create_client

    print("=" * 60)
    print("Creating Database Schema")
    print("=" * 60)

    schema_sql = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create sentence_embeddings table
CREATE TABLE IF NOT EXISTS sentence_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    talk_id UUID NOT NULL,
    title TEXT NOT NULL,
    speaker TEXT,
    calling TEXT,
    year INTEGER,
    season TEXT,
    url TEXT,
    sentence_num INTEGER,
    text TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for talk_id grouping
CREATE INDEX IF NOT EXISTS sentence_embeddings_talk_id_idx 
ON sentence_embeddings(talk_id);

-- Enable Row Level Security
ALTER TABLE sentence_embeddings ENABLE ROW LEVEL SECURITY;

-- RLS policy: authenticated users can read
DROP POLICY IF EXISTS "Allow authenticated users to read" ON sentence_embeddings;
CREATE POLICY "Allow authenticated users to read"
ON sentence_embeddings FOR SELECT
TO authenticated
USING (true);

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_sentences(
  query_embedding vector(1536),
  match_count int DEFAULT 20
)
RETURNS TABLE (
  id uuid,
  talk_id uuid,
  title text,
  speaker text,
  text text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    sentence_embeddings.id,
    sentence_embeddings.talk_id,
    sentence_embeddings.title,
    sentence_embeddings.speaker,
    sentence_embeddings.text,
    1 - (sentence_embeddings.embedding <=> query_embedding) as similarity
  FROM sentence_embeddings
  ORDER BY sentence_embeddings.embedding <=> query_embedding
  LIMIT match_count;
$$;
"""

    url = f"https://api.supabase.com/v1/projects/{SUPABASE_PROJECT_REF}/database/query"
    headers = {
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    resp = requests.post(url, headers=headers, json={"query": schema_sql})
    if resp.status_code in (200, 201):
        print("✅ Database schema created successfully!")
    else:
        print(f"❌ Schema creation failed: {resp.status_code}")
        print(resp.text[:500])
        return False

    # Verify table exists via PostgREST
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    for attempt in range(5):
        try:
            result = client.table('sentence_embeddings').select('id', count='exact').limit(1).execute()
            print(f"✅ Table verified. Current rows: {result.count or 0}")
            return True
        except Exception:
            if attempt < 4:
                print(f"   Waiting for schema cache to refresh... ({attempt + 1}/5)")
                time.sleep(3)
            else:
                print("⚠️  Table created but PostgREST cache hasn't refreshed yet.")
                print("   This is normal — it should be ready by import time.")
                return True


if __name__ == '__main__':
    if not create_schema():
        sys.exit(1)
    print("\n✅ Schema ready! Next: python scripts/02_scrape_data.py")
