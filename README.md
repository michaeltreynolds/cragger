# Conference RAG

A Retrieval Augmented Generation (RAG) application that lets users ask questions about General Conference talks using semantic search and AI-generated answers.

## 🚀 Quick Start

### 1. Fork this repo

Click **"Fork"** in the top right → **"Create fork"**

> Make sure your fork is **public** (required for free GitHub Pages hosting & Colab).

### 2. Deploy to GitHub Pages

In your fork: **Settings** → **Pages** → Source: **Deploy from a branch** → Branch: **main**, Folder: **/ (root)** → **Save**

Your site will be live at: `https://YOUR-USERNAME.github.io/conference-rag/`

### 3. Open the Setup Notebook

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/byu-cs-452/conference-rag/blob/main/setup.ipynb)

The notebook walks you through every step (~85 minutes):
- Configure Supabase credentials
- Set up the database schema
- Deploy Edge Functions
- Import & embed conference data
- Test all three search modes

**Prerequisites:**
- [Supabase](https://supabase.com) account (free tier)
- [GitHub](https://github.com) account
- [OpenAI API key](https://platform.openai.com/api-keys) (~$0.60 usage)

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │  Student asks question
│  (GitHub    │
│   Pages)    │
└──────┬──────┘
       │
       ├─── Supabase Auth (magic link)
       │
       ├─── Edge Function: embed-question
       │         ↓ OpenAI API (server-side 🔒)
       │         ↓ Returns embedding vector
       │
       ├─── Supabase Database (pgvector)
       │         ↓ match_sentences()
       │         ↓ Returns similar sentences
       │         ↓ Grouped by talk, ranked
       │
       └─── Edge Function: generate-answer
                 ↓ GPT-4o-mini (server-side 🔒)
                 ↓ Returns final answer
```

## 🔍 Three Search Modes

The app features three search capabilities that "light up" as you complete each section of the notebook:

| Mode | What it does | Requires |
|------|-------------|----------|
| **🔍 Keyword Search** | SQL `ILIKE` query on talk text | Conference data imported |
| **🧠 Semantic Search** | Vector similarity with pgvector | Embeddings + `embed-question` Edge Function |
| **🤖 Ask a Question (RAG)** | AI-generated answers with sources | All Edge Functions deployed |

## 📚 Learning Objectives

1. **Vector Embeddings** — Representing text as searchable numbers
2. **Semantic Search** — Finding similar content with cosine similarity
3. **RAG Architecture** — Combining retrieval + generation
4. **Edge Functions** — Serverless compute for secure API management
5. **Row Level Security** — User-level data access control
6. **Production Deployment** — Full-stack app on GitHub Pages

## 🔒 Security Model

| Component | Security Approach |
|-----------|------------------|
| Supabase anon key | Safe to expose (protected by RLS) |
| OpenAI API key | Server-side only via Edge Functions |
| Database access | Row Level Security policies |
| Transport | HTTPS enforced by GitHub Pages |

## 📁 Project Structure

```
conference-rag/
├── index.html              # Main application UI
├── app.js                  # Three search modes + auth logic
├── styles.css              # Dark theme styling
├── config.js               # Supabase credentials (you edit this)
├── setup.ipynb             # Setup notebook (run in Colab)
├── notebook_content/       # Markdown sources for notebook
│   ├── 00_welcome.md
│   ├── ...
│   └── 09_reflection.md
├── convert_to_notebook.py  # Regenerate setup.ipynb from markdown
└── .nojekyll               # Tells GitHub Pages not to use Jekyll
```

## 🎓 Assignment Deliverables

1. GitHub repository URL (your fork)
2. Live deployment URL (GitHub Pages)
3. Screenshot of a working query + answer
4. Brief reflection on embedding strategies

## ⚠️ Important Notes

- Update `config.js` with your Supabase credentials before testing
- Deploy Edge Functions before testing semantic search & RAG
- Add your GitHub Pages URL to Supabase redirect URLs
- Never commit real API keys to public repositories

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Please configure Supabase" | Update `config.js` with your project URL and anon key |
| Magic link not working | Add your site URL to Supabase → Authentication → URL Configuration |
| Changes don't appear | Hard refresh (Ctrl+Shift+R) or try incognito window |
| Search shows "Not Ready" | Complete the corresponding notebook section first |
| "Failed to get embedding" | Deploy Edge Functions (see notebook Part 5) |
| "Database search failed" | Run the database schema SQL (see notebook Part 3) |
| No search results | Import data first (see notebook Parts 6-7) |

## 📄 License

Educational use only. Conference talk content is used under fair use for educational purposes.

---

Built with ❤️ for CS 452
