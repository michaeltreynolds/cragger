# Step 8: Test the Complete System

## What You'll Learn
- How to verify a full-stack application works end-to-end
- How the RAG pipeline flows from question to answer
- How to debug common issues

## What to Do

### Test from Your Deployed Site

1. Go to your site: `https://YOUR-USERNAME.github.io/conference-rag/`
2. Make sure you're logged in
3. Test each search mode:

#### 🔍 Keyword Search
Try: `"faith"` or `"temple"`
- Should return talks containing that exact word
- Results show title, speaker, and matching text

#### 🧠 Semantic Search
Try: `"How can I find peace during hard times?"`
- Should return talks about peace, trials, and comfort — even if they don't contain those exact words
- Notice the **similarity scores** — higher means more relevant

#### 🤖 Ask a Question (RAG)
Try: `"What have church leaders taught about prayer?"`
- Should return an AI-generated answer with citations
- The answer draws from the most relevant talks

### What's Happening Behind the Scenes

```
Your Question: "How can I find peace during hard times?"
    ↓
1. embed-question Edge Function
    → Sends question to OpenAI
    → Returns 1,536-dimensional embedding
    ↓
2. Vector Search (match_sentences)
    → pgvector finds 20 most similar sentences
    → Groups by talk_id, ranks by relevance
    → Returns top 3 talks
    ↓
3. generate-answer Edge Function
    → Sends question + talk context to GPT-4o
    → Returns a natural language answer with citations
    ↓
4. Display in UI ✨
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Search shows "Not Ready" | Make sure you completed the relevant step (data import, edge function deployment) |
| "Failed to get embedding" | Check Edge Function deployment (Step 5) and that OPENAI_API_KEY secret is set |
| No search results | Verify data was imported (check row count in Supabase Dashboard) |
| Login doesn't work | Check redirect URL in Supabase Auth settings (Step 4) |
| Changes don't appear | Hard refresh (Ctrl+Shift+R) or try incognito window |

> 💡 **Ask your AI assistant**: *"My RAG search is returning irrelevant results. What factors affect the quality of RAG search results?"*

## Verification

- [ ] All three search modes show green status indicators
- [ ] Keyword search returns relevant results
- [ ] Semantic search returns results even for non-exact-match queries
- [ ] RAG question returns an AI-generated answer with talk citations
- [ ] Take a screenshot of a working RAG query — you'll need this for submission!

→ Next: [Step 09: Reflection](09_reflection.md)
