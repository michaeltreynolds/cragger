# Step 5: Deploy Edge Functions

## What You'll Learn
- What Edge Functions (serverless functions) are and why we need them
- How to keep API keys secure by running code server-side
- How the Supabase CLI works
- How CORS and authentication work in Edge Functions

## Background

Your app needs to call OpenAI's API, but you can't put your API key in client-side JavaScript (anyone could steal it). Edge Functions solve this:

```
❌ Bad:  Browser → OpenAI API (API key exposed in browser!)
✅ Good: Browser → Edge Function → OpenAI API (API key stays on server)
```

We need two Edge Functions:
1. **`embed-question`** — Takes a user's question, calls OpenAI to get an embedding vector
2. **`generate-answer`** — Takes a question + context talks, calls GPT-4o to generate an answer

The code for both functions is already in your repo at `supabase/functions/`. Take a look!

## What to Do

### 1. Install the Supabase CLI

The Supabase CLI lets you deploy Edge Functions from your terminal.

> 💡 **Ask your AI assistant**: *"How do I install the Supabase CLI on my operating system?"*

Common installation methods:
- **npm**: `npm install -g supabase`
- **Homebrew (macOS)**: `brew install supabase/tap/supabase`
- **Scoop (Windows)**: `scoop bucket add supabase https://github.com/supabase/scoop-bucket.git` then `scoop install supabase`

Verify: `supabase --version`

### 2. Link to Your Project

```bash
supabase link --project-ref YOUR_PROJECT_REF
```

Replace `YOUR_PROJECT_REF` with the value from your `config.secret.json`.

### 3. Set Your OpenAI Key as a Secret

```bash
supabase secrets set OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
```

### 4. Deploy the Functions

```bash
supabase functions deploy embed-question --no-verify-jwt
supabase functions deploy generate-answer --no-verify-jwt
```

> 💡 **Why `--no-verify-jwt`?** We handle authentication ourselves inside the function (see `_shared/auth.ts`), so we disable the API gateway's default JWT verification. This gives us more control over the auth flow.

### 5. Understand the Code

Take a moment to read through the Edge Function code:

- `supabase/functions/_shared/cors.ts` — CORS headers for cross-origin requests
- `supabase/functions/_shared/auth.ts` — Authentication helper that verifies the user's JWT
- `supabase/functions/embed-question/index.ts` — Embedding function
- `supabase/functions/generate-answer/index.ts` — Answer generation function

> 💡 **Ask your AI assistant**: *"Walk me through the embed-question Edge Function code. What does each part do?"*

### Key Concepts in the Code

| Concept | Where | Why |
|---------|-------|-----|
| CORS headers | `_shared/cors.ts` | Allows your GitHub Pages site to call the function |
| JWT authentication | `_shared/auth.ts` | Verifies the user is logged in before processing |
| Environment variables | `Deno.env.get()` | Accesses the OpenAI key securely |
| Error handling | `try/catch` blocks | Returns clear error messages |

## Verification

Test your functions with curl or your AI assistant:

```bash
# Test embed-question (replace YOUR_URL and YOUR_ANON_KEY)
curl -X POST 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/embed-question' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is faith?"}'
```

- [ ] `supabase --version` shows a version number
- [ ] Both functions deployed without errors
- [ ] You can see the functions in Supabase Dashboard → Edge Functions

## → Next: [Step 06: Scrape Data](06_scrape_data.md)

> 🤖 **AI coding assistant?** Read [ai_agent_instructions.md](../ai_agent_instructions.md) for guidance on helping students with this assignment.
