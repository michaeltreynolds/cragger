# Supabase Edge Functions

## What Are Edge Functions?

They're **Deno-based serverless functions** that run on Supabase's edge infrastructure. Think of them like AWS Lambda or GCP Cloud Functions, but native to Supabase. They give you an HTTPS endpoint where you can run arbitrary server-side code.

## Why They Fit Your Use Case

- **Authenticated endpoint** — Every Edge Function automatically receives the user's JWT from Supabase Auth in the `Authorization` header. You can verify it with a few lines of code.
- **Secrets management** — You store your OpenAI API key as a secret (`supabase secrets set OPENAI_API_KEY=sk-...`), and it's available as an environment variable. It never touches the client.
- **Custom code** — Full Deno runtime, so you can call the OpenAI API, process data, hit your database, whatever you need.

## Quick Overview of the Steps

1. **Initialize** (if you haven't already):
   ```bash
   supabase functions new my-ai-function
   ```
   This creates a folder at `supabase/functions/my-ai-function/index.ts`.

2. **Write your function** (`index.ts`):
   ```typescript
   import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
   import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

   serve(async (req) => {
     // Verify the user is authenticated
     const authHeader = req.headers.get('Authorization')!
     const supabase = createClient(
       Deno.env.get('SUPABASE_URL')!,
       Deno.env.get('SUPABASE_ANON_KEY')!,
       { global: { headers: { Authorization: authHeader } } }
     )
     const { data: { user }, error } = await supabase.auth.getUser()
     if (error || !user) {
       return new Response('Unauthorized', { status: 401 })
     }

     // Call OpenAI with your secret key
     const openaiKey = Deno.env.get('OPENAI_API_KEY')!
     const response = await fetch('https://api.openai.com/v1/chat/completions', {
       method: 'POST',
       headers: {
         'Authorization': `Bearer ${openaiKey}`,
         'Content-Type': 'application/json',
       },
       body: JSON.stringify({
         model: 'gpt-4o',
         messages: [{ role: 'user', content: 'Hello!' }],
       }),
     })

     const data = await response.json()
     return new Response(JSON.stringify(data), {
       headers: { 'Content-Type': 'application/json' },
     })
   })
   ```

3. **Set your secret**:
   ```bash
   supabase secrets set OPENAI_API_KEY=sk-your-key-here
   ```

4. **Deploy**:
   ```bash
   supabase functions deploy my-ai-function
   ```

5. **Call it from your client**:
   ```javascript
   const { data, error } = await supabase.functions.invoke('my-ai-function', {
     body: { prompt: 'Hello!' },
   })
   ```
   The Supabase client library automatically attaches the logged-in user's JWT, so authentication is handled for you.

## Key Details

| Aspect | Detail |
|---|---|
| **Runtime** | Deno (TypeScript/JavaScript) |
| **Auth** | JWT from Supabase Auth, verified server-side |
| **Secrets** | `supabase secrets set` → available via `Deno.env.get()` |
| **Free tier** | 500K invocations/month, 2M on Pro |
| **Cold starts** | Minimal — edge deployment |
| **Docs** | [supabase.com/docs/guides/functions](https://supabase.com/docs/guides/functions) |
