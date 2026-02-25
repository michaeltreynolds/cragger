# 🎓 Conference RAG — Overview

## What You'll Build

A **Retrieval Augmented Generation (RAG)** application that lets users ask questions about General Conference talks using semantic search and AI-generated answers.

Your finished app will have three search modes that "light up" as you complete each step:

| Mode | What It Does | Unlocked When |
|------|-------------|---------------|
| 🔍 **Keyword Search** | SQL `ILIKE` query on talk text | Conference data imported |
| 🧠 **Semantic Search** | Vector similarity search with pgvector | Embeddings generated + Edge Function deployed |
| 🤖 **Ask a Question (RAG)** | AI-generated answers with source citations | All Edge Functions deployed |

## Architecture

```
┌─────────────┐
│   Browser   │  Student asks question
│  (GitHub    │
│   Pages)    │
└──────┬──────┘
       │
       ├─── Supabase Auth (magic link login)
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
                ↓ GPT-4o (server-side 🔒)
                ↓ Returns final answer
```

## What You'll Learn

1. **Vector Embeddings** — Representing text as searchable numbers
2. **Semantic Search** — Finding similar content with cosine similarity
3. **RAG Architecture** — Combining retrieval + generation
4. **Edge Functions** — Serverless compute for secure API management
5. **Row Level Security** — Database-level access control
6. **Production Deployment** — Full-stack app on GitHub Pages + Supabase

## Prerequisites

- [GitHub](https://github.com) account
- [Supabase](https://supabase.com) account (free tier)
- [OpenAI API key](https://platform.openai.com/api-keys) (~$0.60 usage)
- Python 3.9+ installed locally
- An AI coding assistant (pick one):
  - **Antigravity** (VS Code extension)
  - **GitHub Copilot** (VS Code extension)
  - **Cursor** (standalone IDE)

## Setting Up Your Environment

### 1. Install Python & Create a Virtual Environment

```bash
# Check Python is installed
python --version

# Create a virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Your AI Assistant

Install one of these in your code editor:

- **Antigravity** — Install from VS Code Marketplace, sign in
- **GitHub Copilot** — Install from VS Code Marketplace, sign in with GitHub
- **Cursor** — Download from [cursor.com](https://cursor.com)

> 💡 **Pro tip**: Throughout this assignment, whenever you're stuck or curious, ask your AI assistant! For example:
> - *"What is a vector embedding?"*
> - *"Why do we use cosine similarity instead of Euclidean distance?"*
> - *"Explain what Row Level Security does in Supabase"*

## Cost Estimate

💰 **~$0.60** in OpenAI API usage (for embedding 5 years of conference talks)

## Time Estimate

⏱️ **~2 hours** total across all steps

Let's get started! → [Step 01: Fork & Setup](01_fork_and_setup.md)
