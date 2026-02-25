# Cragger — Next Steps to Full Functionality

> **Current state**: Keyword search works against the `sentence_embeddings` table in Supabase. Semantic search and RAG (Ask a Question) are wired up in the frontend but show "🔴 Not Ready" — there are no Edge Functions deployed and embeddings may or may not exist in the database.

---

## Table of Contents

1. [Architecture Gap Analysis](#1-architecture-gap-analysis)
2. [Phase 1 — Database & Data Readiness](#2-phase-1--database--data-readiness)
3. [Phase 2 — Edge Function: embed-question](#3-phase-2--edge-function-embed-question)
4. [Phase 3 — Edge Function: generate-answer](#4-phase-3--edge-function-generate-answer)
5. [Phase 4 — End-to-End Verification](#5-phase-4--end-to-end-verification)
6. [Phase 5 — Security & Credential Hygiene](#6-phase-5--security--credential-hygiene)
7. [Phase 6 — Polish & Hardening](#7-phase-6--polish--hardening)
8. [Phase 7 — Optional Enhancements](#8-phase-7--optional-enhancements)
9. [Testing & Verification Plan](#9-testing--verification-plan)

---

## 1. Architecture Gap Analysis

The frontend (`app.js`) expects three backend capabilities:

| Capability | Frontend Code | Backend Status |
|---|---|---|
| **Keyword Search** | `supabaseClient.from('sentence_embeddings').select(...)` | ✅ Working — table exists, data present |
| **Semantic Search** | `getEmbedding()` → `searchSentences()` → `groupByTalk()` | ❌ Missing: `embed-question` Edge Function + `match_sentences` DB function |
| **RAG (Ask a Question)** | `getEmbedding()` → `searchSentences()` → `generateAnswer()` | ❌ Missing: `generate-answer` Edge Function |

### What the frontend calls

1. **`embed-question` Edge Function** — `POST ${SUPABASE_URL}/functions/v1/embed-question`
   - Body: `{ "question": "..." }`
   - Returns: `{ "embedding": [float, float, ...] }` (1536 dimensions)

2. **`match_sentences` RPC** — `supabaseClient.rpc('match_sentences', { query_embedding, match_threshold: 0.6, match_count: 20 })`
   - Returns rows with: `id`, `talk_id`, `title`, `speaker`, `text`, `similarity`

3. **`generate-answer` Edge Function** — `POST ${SUPABASE_URL}/functions/v1/generate-answer`
   - Body: `{ "question": "...", "context_talks": [{ title, speaker, text }] }`
   - Returns: `{ "answer": "..." }`

### Files that don't exist yet

| File | Purpose |
|---|---|
| `supabase/functions/embed-question/index.ts` | Deno Edge Function: calls OpenAI embeddings API |
| `supabase/functions/generate-answer/index.ts` | Deno Edge Function: calls GPT-4o-mini chat API |
| `supabase/config.toml` | Supabase CLI project config (created by `supabase init`) |

---

## 2. Phase 1 — Database & Data Readiness

### 2a. Verify `match_sentences` function exists

The `setup_local.py` script creates this function as part of schema setup, but it may not have been run. Check in the Supabase Dashboard → SQL Editor:

```sql
SELECT routine_name FROM information_schema.routines
WHERE routine_name = 'match_sentences';
```

If it doesn't exist, run this SQL (from `setup_local.py` lines 67–93):

```sql
CREATE OR REPLACE FUNCTION match_sentences(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
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
  WHERE 1 - (sentence_embeddings.embedding <=> query_embedding) > match_threshold
  ORDER BY sentence_embeddings.embedding <=> query_embedding
  LIMIT match_count;
$$;
```

### 2b. Verify embeddings exist in the data

The keyword search works, which means there are rows in `sentence_embeddings`. But do they have embeddings?

```sql
SELECT
  COUNT(*) as total_rows,
  COUNT(embedding) as rows_with_embedding,
  COUNT(*) - COUNT(embedding) as rows_without_embedding
FROM sentence_embeddings;
```

**If embeddings are missing**, you need to run `setup_local.py` with `python setup_local.py data`, or just the embedding portion. This calls OpenAI's `text-embedding-3-small` model (~$0.60 for 5 years of talks).

### 2c. Create ivfflat index (performance)

The notebook's schema SQL (`03_database_schema.md`) includes an ivfflat index that `setup_local.py` **does not** create:

```sql
CREATE INDEX IF NOT EXISTS sentence_embeddings_embedding_idx
ON sentence_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

> **Note**: ivfflat requires data to exist before creating the index. Only run this after embeddings are populated.

**Verification**:
```sql
SELECT indexname FROM pg_indexes WHERE tablename = 'sentence_embeddings';
```

### 2d. Verify pgvector extension

```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```

If not present: `CREATE EXTENSION IF NOT EXISTS vector;`

---

## 3. Phase 2 — Edge Function: `embed-question`

### 3a. Initialize the Supabase CLI project

```bash
cd c:\repos\cragger
npx supabase init
```

This creates the `supabase/` directory structure and `supabase/config.toml`.

### 3b. Create the function

```bash
npx supabase functions new embed-question
```

Then write `supabase/functions/embed-question/index.ts`:

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { question } = await req.json()
    const openaiKey = Deno.env.get('OPENAI_API_KEY')

    if (!openaiKey) {
      throw new Error('OPENAI_API_KEY not configured')
    }

    const response = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${openaiKey}`
      },
      body: JSON.stringify({
        model: 'text-embedding-3-small',
        input: question
      })
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.error?.message || 'OpenAI API error')
    }

    const data = await response.json()

    return new Response(
      JSON.stringify({ embedding: data.data[0].embedding }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    )
  }
})
```

### 3c. Deploy

```bash
npx supabase link --project-ref ebmgbfsjelwaglysbqym
npx supabase functions deploy embed-question --no-verify-jwt
npx supabase secrets set OPENAI_API_KEY=sk-proj-...
```

> **`--no-verify-jwt`**: The frontend passes the anon key in the Authorization header, but the function itself doesn't verify the JWT. This is fine for this use case — the function just proxies to OpenAI.

### 3d. Test

```bash
curl -X POST "https://ebmgbfsjelwaglysbqym.supabase.co/functions/v1/embed-question" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sb_publishable_wdeYV7W3ywQTHo9ZJK8x6g_WCwrfTUE" \
  -d '{"question": "What is faith?"}'
```

**Expected**: JSON with `{ "embedding": [float, ...] }` of length 1536.

---

## 4. Phase 3 — Edge Function: `generate-answer`

### 4a. Create the function

```bash
npx supabase functions new generate-answer
```

Write `supabase/functions/generate-answer/index.ts`:

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { question, context_talks } = await req.json()
    const openaiKey = Deno.env.get('OPENAI_API_KEY')

    if (!openaiKey) {
      throw new Error('OPENAI_API_KEY not configured')
    }

    // Build context from talks
    const context = context_talks.map((talk, i) =>
      `Talk ${i+1}: "${talk.title}" by ${talk.speaker}\n${talk.text}`
    ).join('\n\n')

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${openaiKey}`
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content: 'You are a helpful assistant answering questions based on conference talks. Use only the provided talks to answer. Cite speakers and talk titles.'
          },
          {
            role: 'user',
            content: `Question: ${question}\n\nRelevant Talks:\n${context}`
          }
        ],
        temperature: 0.7,
        max_tokens: 500
      })
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.error?.message || 'OpenAI API error')
    }

    const data = await response.json()

    return new Response(
      JSON.stringify({ answer: data.choices[0].message.content }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    )
  }
})
```

### 4b. Deploy

```bash
npx supabase functions deploy generate-answer --no-verify-jwt
```

The `OPENAI_API_KEY` secret was already set in Phase 2.

### 4c. Test

```bash
curl -X POST "https://ebmgbfsjelwaglysbqym.supabase.co/functions/v1/generate-answer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sb_publishable_wdeYV7W3ywQTHo9ZJK8x6g_WCwrfTUE" \
  -d '{"question":"What is faith?","context_talks":[{"title":"Test Talk","speaker":"Test Speaker","text":"Faith is belief in things hoped for."}]}'
```

**Expected**: `{ "answer": "..." }` with a coherent response.

---

## 5. Phase 4 — End-to-End Verification

After all three backend pieces are in place, verify the complete pipeline:

### 5a. Readiness checks

1. Open the deployed site (GitHub Pages)
2. Log in with magic link
3. All three panels should show "🟢 Ready":
   - **Keyword Search**: ✅ (was already working)
   - **Semantic Search**: ✅ (embed-question responds + embeddings exist)
   - **RAG**: ✅ (generate-answer responds)

### 5b. Keyword search test

- Query: `"faith"`
- Expected: Result cards with talk titles, speakers, and highlighted text

### 5c. Semantic search test

- Query: `"How can I find peace during difficult times?"`
- Expected: Result cards ranked by semantic similarity (not exact keyword match)
- Should return talks about peace, comfort, trials — even if those exact words aren't used

### 5d. RAG test

- Query: `"What do conference speakers teach about prayer?"`
- Expected: AI-generated answer with source citations, followed by source talk cards

### 5e. Edge case tests

| Test | Expected Behavior |
|---|---|
| Empty query | No action (buttons should be disabled or input validation) |
| Very long query (500+ chars) | Graceful handling — OpenAI may truncate |
| Special characters (`<script>alert(1)</script>`) | `escapeHtml()` in `app.js` should prevent XSS |
| Multiple rapid searches | Loading spinner, no race conditions |
| Network error mid-search | Error message displayed in result area |

---

## 6. Phase 5 — Security & Credential Hygiene

### 6a. ⚠️ CRITICAL: `config.secret.json` is committed

The `.gitignore` lists `config.secret.json` (line 44) and `*.secret.json` (line 43), but the file **is currently tracked by git**. This means it was committed before the gitignore rule was added.

**Immediate action**:
```bash
git rm --cached config.secret.json
git commit -m "Remove config.secret.json from tracking"
```

> **Warning**: The secrets in this file (OpenAI API key, Supabase service key, Supabase access token) may already be exposed in git history. Consider:
> 1. Rotating the OpenAI API key at https://platform.openai.com/api-keys
> 2. Rotating the Supabase access token at https://supabase.com/dashboard/account/tokens
> 3. Regenerating the Supabase service role key (this requires database reconfiguration)

### 6b. Edge Function security

The Edge Functions are deployed with `--no-verify-jwt`, meaning any caller can invoke them. This is acceptable for a demo/educational project, but for production:

- **Consider**: Add JWT verification so only authenticated users can call the functions
- **To enable**: Remove `--no-verify-jwt` flag, and the Supabase client will automatically include the user's JWT

### 6c. CORS headers

Both Edge Functions use `'Access-Control-Allow-Origin': '*'`. For production, restrict to the actual GitHub Pages domain:

```typescript
'Access-Control-Allow-Origin': 'https://YOUR-USERNAME.github.io'
```

### 6d. Rate limiting

Currently, there's no rate limiting on the Edge Functions. A malicious user could spam the OpenAI API through them. Consider:
- Supabase's built-in rate limiting for Edge Functions
- Tracking usage per user in a database table
- Setting spending limits on the OpenAI account

---

## 7. Phase 6 — Polish & Hardening

### 7a. Frontend error handling improvements

In `app.js`, the `searchSentences()` function (line 585) doesn't handle the case where `match_sentences` returns zero results gracefully — the semantic search and RAG flows handle this correctly with the `if (!results || results.length === 0)` check, but the error message could be more specific (e.g., "No semantically similar content found — try a broader query").

### 7b. Loading state per-panel

Currently, there's a single global loading spinner (`showLoading(true/false)`) that covers the entire screen. Consider per-panel loading indicators so users can still interact with other panels while one is searching.

### 7c. The `groupByTalk` function uses `text` property

In `app.js` line 611, `groupByTalk` accesses `sent.text` and `sent.talk_id` — these must match the column names returned by the `match_sentences` function exactly. The SQL function returns `text` and `talk_id`, so this is correct. However, if the schema ever changes, this coupling will break silently.

### 7d. Add a "No data" guidance message

When the database has no rows (fresh setup), the keyword panel shows "Not Ready" but doesn't explain *how* to get it ready. Consider adding a link to the setup notebook or README.

### 7e. Update `<title>` and branding

- `index.html` title is `"Supabase RAG - Conference Q&A"` — consider renaming to "Cragger" or "Conference RAG"
- The heading says "Conference Q&A" — should this be personalized?

### 7f. Consistency between `setup_local.py` and notebook

| Feature | `setup_local.py` | Notebook (`03_database_schema.md`) |
|---|---|---|
| ivfflat index | ❌ Not included | ✅ Included |
| `match_threshold` default | `0.7` | `0.7` |
| `match_count` default | `20` | `20` |

The local setup script should include the ivfflat index creation for consistency.

---

## 8. Phase 7 — Optional Enhancements

These are not required for functionality but would improve the application significantly:

### 8a. Streaming RAG answers

Instead of waiting for the full GPT-4o-mini response, stream the answer token-by-token:
- Use `stream: true` in the OpenAI API call
- Return a `ReadableStream` from the Edge Function
- Use `fetch()` with streaming in `app.js` to display tokens as they arrive

### 8b. Caching embeddings for repeated questions

Cache question embeddings to avoid redundant OpenAI calls:
```sql
CREATE TABLE IF NOT EXISTS embedding_cache (
    question_hash TEXT PRIMARY KEY,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 8c. Question history

Track what users ask (see notebook's `09_reflection.md` for ideas):
```sql
CREATE TABLE IF NOT EXISTS question_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    question TEXT NOT NULL,
    answer TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 8d. Better chunking strategy

The current sentence splitting (`re.split(r'\. (?=[A-Z])', text)`) is naive:
- Misses abbreviations (e.g., "Dr. Smith" splits incorrectly)
- Doesn't handle semicolons, colons, or list items
- Consider paragraph-level chunks or semantic chunking via LangChain

### 8e. Add full-text search (FTS) as an alternative to ILIKE

The current keyword search uses `ILIKE` which is slow on large datasets. PostgreSQL full-text search is much faster:
```sql
ALTER TABLE sentence_embeddings ADD COLUMN fts tsvector
  GENERATED ALWAYS AS (to_tsvector('english', text)) STORED;

CREATE INDEX sentence_embeddings_fts_idx ON sentence_embeddings USING gin(fts);
```

Then query with: `fts @@ plainto_tsquery('english', $query)`

---

## 9. Testing & Verification Plan

### Step-by-step execution order

```
┌─────────────────────────────────────────────────┐
│ Phase 1: Database                               │
│  1. Verify pgvector extension                   │
│  2. Check sentence_embeddings table has data     │
│  3. Check embeddings exist (not all NULL)        │
│  4. Verify/create match_sentences function       │
│  5. Create ivfflat index (if data exists)        │
│  6. Test: supabase.rpc('match_sentences', ...)   │
├─────────────────────────────────────────────────┤
│ Phase 2: embed-question Edge Function           │
│  1. supabase init (creates project structure)    │
│  2. Create function file                         │
│  3. supabase link (connect to remote project)    │
│  4. supabase secrets set OPENAI_API_KEY=...      │
│  5. supabase functions deploy embed-question     │
│  6. Test: curl POST to embed-question            │
│  7. Test: browser console fetch to embed-question│
├─────────────────────────────────────────────────┤
│ Phase 3: generate-answer Edge Function          │
│  1. Create function file                         │
│  2. supabase functions deploy generate-answer    │
│  3. Test: curl POST to generate-answer           │
│  4. Test: browser console fetch                  │
├─────────────────────────────────────────────────┤
│ Phase 4: End-to-End                             │
│  1. Load site, log in                            │
│  2. Verify all 3 panels show "Ready"             │
│  3. Test keyword search                          │
│  4. Test semantic search                         │
│  5. Test RAG question                            │
│  6. Test error cases                             │
├─────────────────────────────────────────────────┤
│ Phase 5: Security                               │
│  1. Remove config.secret.json from git tracking  │
│  2. Rotate exposed credentials                   │
│  3. Consider JWT verification on Edge Functions  │
└─────────────────────────────────────────────────┘
```

### Automated verification script (run after each phase)

```python
# verify_setup.py — run locally to check system health
import requests
import json

with open('config.secret.json') as f:
    secrets = json.load(f)

url = secrets['SUPABASE_URL']
anon = secrets['SUPABASE_ANON_KEY']
service = secrets['SUPABASE_SERVICE_KEY']

checks = {}

# 1. Database: table has data
from supabase import create_client
client = create_client(url, service)
result = client.table('sentence_embeddings').select('id', count='exact').limit(1).execute()
checks['Table has data'] = (result.count or 0) > 0
print(f"{'✅' if checks['Table has data'] else '❌'} Table has {result.count or 0} rows")

# 2. Database: embeddings exist
result = client.table('sentence_embeddings').select('embedding').not_('embedding', 'is', None).limit(1).execute()
checks['Embeddings exist'] = len(result.data) > 0
print(f"{'✅' if checks['Embeddings exist'] else '❌'} Embeddings exist")

# 3. Database: match_sentences works
if checks['Embeddings exist']:
    try:
        # Get a sample embedding
        sample = client.table('sentence_embeddings').select('embedding').not_('embedding', 'is', None).limit(1).execute()
        result = client.rpc('match_sentences', {
            'query_embedding': sample.data[0]['embedding'],
            'match_threshold': 0.5,
            'match_count': 5
        }).execute()
        checks['match_sentences works'] = len(result.data) > 0
    except Exception as e:
        checks['match_sentences works'] = False
        print(f"   Error: {e}")
    print(f"{'✅' if checks['match_sentences works'] else '❌'} match_sentences function")

# 4. Edge Function: embed-question
try:
    r = requests.post(f"{url}/functions/v1/embed-question",
        headers={"Authorization": f"Bearer {anon}", "Content-Type": "application/json"},
        json={"question": "test"}, timeout=10)
    checks['embed-question'] = r.ok and 'embedding' in r.json()
except:
    checks['embed-question'] = False
print(f"{'✅' if checks['embed-question'] else '❌'} embed-question Edge Function")

# 5. Edge Function: generate-answer
try:
    r = requests.post(f"{url}/functions/v1/generate-answer",
        headers={"Authorization": f"Bearer {anon}", "Content-Type": "application/json"},
        json={"question": "test", "context_talks": [{"title": "T", "speaker": "S", "text": "Test."}]},
        timeout=15)
    checks['generate-answer'] = r.ok and 'answer' in r.json()
except:
    checks['generate-answer'] = False
print(f"{'✅' if checks['generate-answer'] else '❌'} generate-answer Edge Function")

# Summary
print(f"\n{'='*50}")
passed = sum(1 for v in checks.values() if v)
print(f"Result: {passed}/{len(checks)} checks passed")
if all(checks.values()):
    print("🎉 All systems operational!")
else:
    failed = [k for k, v in checks.items() if not v]
    print(f"⚠️  Failed: {', '.join(failed)}")
```

---

## Summary of Required Work

| # | Task | Difficulty | Time Est. | Blocking? |
|---|---|---|---|---|
| 1 | Verify/create `match_sentences` SQL function | Easy | 5 min | Yes — semantic search + RAG |
| 2 | Verify embeddings exist in data | Easy | 5 min | Yes — semantic search + RAG |
| 3 | Generate embeddings (if missing) | Medium | 15-20 min | Yes — semantic search + RAG |
| 4 | Create ivfflat index | Easy | 2 min | No — performance only |
| 5 | Create + deploy `embed-question` Edge Function | Medium | 15 min | Yes — semantic search + RAG |
| 6 | Create + deploy `generate-answer` Edge Function | Medium | 15 min | Yes — RAG only |
| 7 | Set `OPENAI_API_KEY` as Supabase secret | Easy | 2 min | Yes — both Edge Functions |
| 8 | Remove `config.secret.json` from git tracking | Easy | 2 min | No — security hygiene |
| 9 | End-to-end testing | Medium | 15 min | No |
| **Total** | | | **~75 min** | |

### Critical path

```
Embeddings exist? ──No──> Run setup_local.py data ──> Embeddings generated
       │ Yes
       ▼
match_sentences exists? ──No──> Run SQL ──> Function created
       │ Yes
       ▼
supabase init + link ──> Create embed-question ──> Deploy ──> Test
                              │
                              ▼
                     Create generate-answer ──> Deploy ──> Test
                              │
                              ▼
                     Set OPENAI_API_KEY secret
                              │
                              ▼
                     End-to-end testing ──> All panels green ✅
```

---

## Things Not Yet Considered (Self-Review)

After multiple review passes, here are additional items to keep in mind:

### Supabase Free Tier Limits
- Edge Functions: 500,000 invocations/month, 2M total edge function invocations
- Database: 500 MB storage
- ~80,000 sentence embeddings × 1536 floats × 4 bytes ≈ ~490 MB of vector data alone
- **Risk**: May hit storage limits on the free tier. Monitor usage in the Supabase dashboard.

### OpenAI API Costs
- `text-embedding-3-small`: $0.020 per 1M tokens (cheap)
- `gpt-4o-mini`: $0.150 per 1M input tokens, $0.600 per 1M output tokens
- Each RAG query costs ~$0.001-$0.005 depending on context size
- **Recommendation**: Set spending limits on the OpenAI account

### Deno Runtime Compatibility
- Edge Functions run on Deno, not Node.js
- The import URLs (`https://deno.land/std@0.168.0/http/server.ts`) may be outdated
- Supabase may have moved to a newer Deno version — check their docs for current import patterns
- Consider using `Deno.serve()` (newer API) instead of `serve()` from `std/http`

### Edge Function Cold Starts
- First invocation after idle period may take 1-3 seconds
- Users may see a delay on first semantic search or RAG query
- Consider adding a "shimmer" or skeleton loading state in the UI

### Browser Compatibility
- The `fetch()` API is used throughout — works in all modern browsers
- The Supabase JS client is loaded from CDN — ensure it's the correct version
- The `supabase-js@2` CDN import in `index.html` doesn't pin a specific version — could break if v3 is released

### RLS Policy Scope
- The current RLS policy allows all authenticated users to read all sentences
- This is fine for a shared dataset, but means any authenticated user can see all data
- If multi-tenancy is needed in the future, the RLS policy needs per-user scoping

### Error Messages Expose Implementation Details
- The `getEmbedding()` function in `app.js` (line 577) passes through OpenAI error messages to the user
- This could expose API key issues or rate limit details
- Consider sanitizing error messages before display

### The `setup_local.py` Hardcoded Year Range
- `START_YEAR = 2025 - YEARS_TO_SCRAPE` means if you run this in 2027, you get 2022-2027
- This is probably fine for an educational project, but worth noting

### No Offline/Fallback Mode
- If Supabase is down, the entire app is non-functional
- If OpenAI is down, semantic search and RAG fail
- Keyword search only requires Supabase (more resilient)

### The `escapeHtml` Function
- The RAG answer is escaped with `escapeHtml()` (line 540), which prevents XSS but also prevents rendering any markdown in the AI's response
- Consider using a markdown renderer (e.g., `marked.js`) for the RAG answer panel to support formatted responses

### `--no-verify-jwt` on Edge Functions
- Both functions are deployed without JWT verification
- This means anyone with the Supabase URL can call them without authentication
- While the anon key is needed (CORS preflight passes it), this is still a concern for abuse
- A determined attacker could call the Edge Functions directly and burn through OpenAI credits
