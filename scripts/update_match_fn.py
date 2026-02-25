"""
Update match_sentences SQL function to remove threshold filtering.
"""
import json
import requests

with open('config.secret.json', 'r') as f:
    secrets = json.load(f)

SUPABASE_ACCESS_TOKEN = secrets['SUPABASE_ACCESS_TOKEN']
SUPABASE_PROJECT_REF = secrets['SUPABASE_PROJECT_REF']

sql = """
DROP FUNCTION IF EXISTS match_sentences(vector, integer);
DROP FUNCTION IF EXISTS match_sentences(vector, double precision, integer);

CREATE OR REPLACE FUNCTION match_sentences(
  query_embedding vector(1536),
  match_count int DEFAULT 20
)
RETURNS TABLE (
  id uuid,
  talk_id uuid,
  title text,
  speaker text,
  url text,
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
    sentence_embeddings.url,
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

resp = requests.post(url, headers=headers, json={"query": sql})
if resp.status_code in (200, 201):
    print("✅ match_sentences function updated successfully!")
else:
    print(f"❌ Failed: {resp.status_code}")
    print(resp.text[:500])
