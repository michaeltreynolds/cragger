# Step 3: Create Database Schema

## What You'll Learn
- What pgvector is and why it's useful for AI applications
- How vector similarity search works at the database level
- What Row Level Security (RLS) is and why it matters
- How database functions (stored procedures) work

## Background

Your database needs:
1. **pgvector extension** — Adds vector data type and similarity operators to PostgreSQL
2. **`sentence_embeddings` table** — Stores talk sentences with their embedding vectors
3. **RLS policies** — Controls who can read data (only authenticated users)
4. **`match_sentences()` function** — A stored procedure that performs vector similarity search

> 💡 **Ask your AI assistant**: *"What is pgvector and how does cosine similarity search work?"*

## What to Do

Run the schema creation script:

```bash
python scripts/01_create_schema.py
```

This script:
- Connects to your Supabase project using the Management API
- Runs SQL to create the table, indexes, RLS policies, and search function
- Verifies the table exists

### What the Schema Looks Like

```sql
CREATE TABLE sentence_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    talk_id UUID NOT NULL,          -- Groups sentences from the same talk
    title TEXT NOT NULL,
    speaker TEXT,
    calling TEXT,
    year INTEGER,
    season TEXT,
    url TEXT,
    sentence_num INTEGER,
    text TEXT NOT NULL,
    embedding vector(1536),         -- 1,536-dimensional embedding vector
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

> 💡 **Why `vector(1536)`?** OpenAI's `text-embedding-3-small` model produces 1,536-dimensional vectors. Each dimension is a float number that captures some aspect of the text's meaning.

### Understanding Row Level Security

RLS lets you control data access at the database level:
- ✅ **Authenticated users** can read all sentences
- ❌ **Unauthenticated users** cannot access anything
- This means even if someone gets your anon key, they can't read data without logging in

> 💡 **Ask your AI assistant**: *"Explain Row Level Security in PostgreSQL. Why is it better than checking permissions in application code?"*

## Verification

- [ ] Script prints "✅ Database schema created successfully!"
- [ ] Script prints "✅ Table verified" with a row count
- [ ] You can see the `sentence_embeddings` table in your Supabase Dashboard → Table Editor

→ Next: [Step 04: Deploy Frontend](04_deploy_frontend.md)
