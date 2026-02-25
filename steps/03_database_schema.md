# Step 3: Create Database Schema

## What You'll Learn
- What pgvector is and why it's useful for AI applications
- How vector similarity search works at the database level
- What Row Level Security (RLS) is and why it matters
- How database functions (stored procedures) work
- **The difference between public and protected data access**

## Background

Your database needs:
1. **pgvector extension** — Adds vector data type and similarity operators to PostgreSQL
2. **`sentence_embeddings` table** — Stores talk sentences with their embedding vectors (🔒 **auth-only**)
3. **`page_views` table** — Records every page visit (🌍 **public**)
4. **RLS policies** — Controls who can access each table
5. **`match_sentences()` function** — A stored procedure that performs vector similarity search

> 💡 **Ask your AI assistant**: *"What is pgvector and how does cosine similarity search work?"*

## What to Do

Run the schema creation script:

```bash
python scripts/01_create_schema.py
```

This script creates both tables, their RLS policies, and the search function.

### Two Tables, Two Access Levels

The schema creates two tables with **very different** security policies:

| Table | Who can read? | Who can write? | Why? |
|-------|--------------|----------------|------|
| `page_views` | 🌍 Anyone (anon + authenticated) | 🌍 Anyone | Public analytics — no secrets here |
| `sentence_embeddings` | 🔒 Authenticated users only | 🔒 Service role only | Protected content — requires login |

This is **Row Level Security (RLS)** in action. Both tables have RLS enabled, but their *policies* define very different access rules.

### Understanding the Schema

```sql
-- sentence_embeddings: Protected data
CREATE POLICY "Allow authenticated users to read"
ON sentence_embeddings FOR SELECT
TO authenticated          -- ← Only logged-in users
USING (true);

-- page_views: Public data
CREATE POLICY "Allow public reads"
ON page_views FOR SELECT
TO anon, authenticated    -- ← Anyone, even without login
USING (true);
```

> 💡 **Ask your AI assistant**: *"Explain Row Level Security in PostgreSQL. Why is it more secure than checking permissions in application code?"*

### 🧪 Hands-On: See RLS in Action

After the script completes, try this experiment. Ask your AI assistant to help you write a quick Python snippet that uses **just the anon key** (not the service key) to:

1. **Query `page_views`** → ✅ Should work! The anon key can read this table.
2. **Query `sentence_embeddings`** → ❌ Should return **zero rows**! RLS blocks unauthenticated access.

Here's a starting point:

```python
from supabase import create_client
import json

with open('config.secret.json') as f:
    secrets = json.load(f)

# Connect with the ANON key (not service key!)
client = create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_ANON_KEY'])

# This works — page_views has a public SELECT policy
result = client.table('page_views').select('*').limit(5).execute()
print(f"page_views: {len(result.data)} rows ✅")

# This returns nothing — sentence_embeddings requires authentication
# When RLS policy restricts access you get zero results, no error is returned.
# Why do you think they chose to implement it that way?
result = client.table('sentence_embeddings').select('*').limit(5).execute()
print(f"sentence_embeddings: {len(result.data)} rows (expected: 0) 🔒")
```

> 💡 **Try it!** Ask your AI assistant to run this snippet for you. Seeing the output first-hand makes the RLS concept click — and your assistant can explain *why* it works this way.

> 🤔 **Think about it**: The anon key is in your client-side JavaScript (`config.js`). Anyone can see it by viewing your page source. So why is your data still safe?

### The Security Model

```
┌────────────────────────────────────────┐
│ Supabase-Managed Security              │
│                                        │
│  anon key → RLS decides what you see   │
│  ┌─────────────────┐  ┌────────────┐  │
│  │ page_views      │  │ embeddings │  │
│  │ 🌍 public read  │  │ 🔒 auth    │  │
│  │ 🌍 public write │  │   only     │  │
│  └─────────────────┘  └────────────┘  │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Self-Built Security (Edge Functions)   │
│                                        │
│  OpenAI API key → Supabase can't       │
│  protect this for you — YOU build      │
│  the secure layer with Edge Functions  │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ embed-       │  │ generate-    │   │
│  │ question     │  │ answer       │   │
│  │ 🔒 auth +    │  │ 🔒 auth +    │   │
│  │    API key   │  │    API key   │   │
│  └──────────────┘  └──────────────┘   │
└────────────────────────────────────────┘
```

**Key insight**: Supabase protects your *database* with RLS, but it can't protect *third-party API keys* like OpenAI. That's why you build Edge Functions — they're the secure intermediary you control.

## Verification

- [ ] Script prints "✅ Database schema created successfully!"
- [ ] Script prints "✅ Table verified" with a row count
- [ ] You can see both `sentence_embeddings` and `page_views` in Supabase Dashboard → Table Editor
- [ ] (Optional) The RLS test snippet shows `page_views` is readable but `sentence_embeddings` returns 0 rows

→ Next: [Step 04: Deploy Frontend](04_deploy_frontend.md)
