# Step 7: Generate Embeddings & Import Data

## What You'll Learn
- What vector embeddings are and how they represent meaning
- Why we split text into sentences (chunking strategy)
- How OpenAI's embedding API works
- How data gets imported into a vector database

## Background

This is the **core of RAG**. We need to:

1. **Split talks into sentences** — Each sentence becomes a searchable unit
2. **Generate embeddings** — Convert each sentence into a 1,536-dimensional vector
3. **Import to Supabase** — Store sentences + embeddings in pgvector

### Why Sentence-Level Chunking?

```
Full talk: 3,000 words → too big for precise search
Paragraph: 100-200 words → okay but mixed topics
Sentence: 10-30 words → precise semantic unit ✅
```

Research shows that sentence-level chunks give higher precision for factual queries, and we can always reconstruct full talk context by aggregating sentences with the same `talk_id`.

> 💡 **Ask your AI assistant**: *"What are the trade-offs between different chunking strategies in RAG systems? What is semantic chunking?"*

### How Embeddings Work

```
"Faith is the assurance of things hoped for"
    ↓ OpenAI text-embedding-3-small
[0.012, -0.034, 0.089, ... 1,536 dimensions]
```

Similar sentences produce similar vectors. This is what enables semantic search — finding content by **meaning** rather than exact keywords.

## What to Do

### Step 7a: Generate Embeddings

```bash
python scripts/03_embed_data.py
```

This script:
1. Reads `data/talks.json` (from Step 6)
2. Splits ~400 talks into ~80,000 sentences
3. Generates an embedding for each sentence via OpenAI
4. Saves everything to `data/sentences_with_embeddings.json`

> ⏱️ **This takes 10-15 minutes** and costs ~$0.60 in OpenAI API usage.

### Step 7b: Import to Supabase

```bash
python scripts/04_import_data.py
```

This script:
1. Reads `data/sentences_with_embeddings.json`
2. Truncates any existing data in the table (safe to re-run!)
3. Imports all records in batches of 100
4. Verifies the final row count

> 💡 After this step, **Keyword Search** on your site should turn green! Refresh your deployed site and try a keyword search.

## Verification

- [ ] `03_embed_data.py` completes and reports ~80,000 embeddings generated
- [ ] `data/sentences_with_embeddings.json` exists (will be large, ~500+ MB)
- [ ] `04_import_data.py` completes and reports successful import
- [ ] Supabase Dashboard → Table Editor → `sentence_embeddings` shows data
- [ ] On your site: **🔍 Keyword Search** turns green and returns results
- [ ] On your site: **🧠 Semantic Search** turns green and returns results

→ Next: [Step 08: Test the System](08_testing.md)
