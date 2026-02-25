# Part 3: Database Schema (10 min)

## Step 3a: Create Database Schema

Now we'll create the database table with pgvector support for semantic search.

**What's pgvector?** It's a PostgreSQL extension that lets you store and search vector embeddings efficiently using vector similarity (cosine distance).

```python
# @title 🗄️ Create Database Schema

# Install Supabase Python client
!pip install -q supabase

from supabase import create_client

# Create admin client (uses service_role key)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# SQL to create schema
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

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS sentence_embeddings_embedding_idx 
ON sentence_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

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

print("📝 Running SQL script...")
print("   This creates:")
print("   - pgvector extension")
print("   - sentence_embeddings table")
print("   - Vector similarity search index")
print("   - Row Level Security policies")
print("   - match_sentences() function")
print()

# Execute via Supabase SQL editor (manual step for now)
print("⚠️  Please run this SQL manually:")
print("")
print("1. Go to your Supabase Dashboard")
print("2. Click 'SQL Editor' in the left sidebar")
print("3. Click 'New Query'")
print("4. Paste the SQL below and click 'Run'")
print("")
print("="*60)
print(schema_sql)
print("="*60)
print("")
print("5. Come back here and run the checkpoint below")
```

## Step 3b: Verify Schema

```python
# ✅ CHECKPOINT 1: Verify Database Setup

try:
    result = supabase_admin.table('sentence_embeddings').select('id', count='exact').limit(1).execute()
    print("✅ Database connection successful!")
    print(f"   Table 'sentence_embeddings' exists")
    print(f"   Current rows: {result.count or 0}")
except Exception as e:
    print(f"❌ Database check failed: {e}")
    print("   Make sure you ran the SQL above before continuing")
    raise
```

### 💡 Learning Checkpoint

**What is Row Level Security (RLS)?**

RLS lets you control who can access which rows in a table. In our case:
- ✅ Authenticated users can **read** all sentences
- ❌ Unauthenticated users cannot read anything
- This protects your data even if someone gets your anon key!

**Why sentence-level chunks?**
- Higher precision for fact-based queries
- Natural semantic boundaries
- Can aggregate by talk for context
