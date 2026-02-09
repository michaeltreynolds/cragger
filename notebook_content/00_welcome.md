# 🎓 Conference RAG - Complete Setup Guide

Welcome! In this notebook, you'll build a **Retrieval Augmented Generation (RAG) application** that lets users ask questions about conference talks using semantic search and AI-generated answers.

## What You'll Build

A web application with three progressively unlocked search modes:

1. **🔍 Keyword Search** — Find talks by keyword (SQL queries via Supabase)
2. **🧠 Semantic Search** — Find similar content by meaning (vector embeddings + pgvector)
3. **🤖 Ask a Question (RAG)** — Get AI-generated answers with sources (full RAG pipeline)

## How It Works

As you complete each section of this notebook, a search mode will "light up" on your deployed site:

| You complete... | This unlocks... |
|----------------|-----------------|
| Parts 1-4: Fork repo, deploy site, configure Supabase | Login works, but all searches show "Not Ready" |
| Parts 5-6: Import conference data | 🔍 **Keyword Search** turns green |
| Part 7: Generate embeddings + deploy `embed-question` | 🧠 **Semantic Search** turns green |
| Part 8: Deploy `generate-answer` Edge Function | 🤖 **Ask a Question** turns green |

## Architecture

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
       │         ↓ OpenAI API (server-side key 🔒)
       │         ↓ Returns embedding vector
       │
       ├─── Supabase Database (pgvector)
       │         ↓ Vector similarity search
       │         ↓ Returns top matching sentences
       │
       └─── Edge Function: generate-answer
                 ↓ OpenAI GPT-4 (server-side key 🔒)
                 ↓ Returns final answer
```

## Learning Objectives

You'll learn:
1. **Vector Embeddings** - How to represent text as numbers
2. **Semantic Search** - Finding similar content without exact keyword matches
3. **RAG Architecture** - Combining retrieval + generation
4. **Server-side Security** - Protecting API keys with Edge Functions
5. **Row Level Security** - User-specific data isolation
6. **Production Deployment** - Real-world application architecture

## Time Estimate
⏱️ **~85 minutes** (grab a coffee!)

## Cost Estimate
💰 **~$0.60** in OpenAI API usage (for 5 years of conference talks)

Let's get started! 🚀
