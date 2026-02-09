# Part 5: Deploy Edge Functions (10 min)

Edge Functions let us call OpenAI's API server-side, keeping our API keys secret. We'll deploy two functions:
1. `embed-question` - Converts user questions to embeddings
2. `generate-answer` - Calls GPT-4 to generate final answers

## Step 5a: Install Supabase CLI

```python
# @title 📦 Install Supabase CLI

# Download and install the Supabase CLI binary directly
!curl -sSL "https://github.com/supabase/cli/releases/latest/download/supabase_linux_amd64.tar.gz" -o /tmp/supabase.tar.gz
!tar -xzf /tmp/supabase.tar.gz -C /usr/local/bin supabase

# Verify installation
!supabase --version

print("✅ Supabase CLI installed!")
```

## Step 5b: Create Edge Function Files

```python
# @title 📝 Create Edge Function Code

import os

# Create directories
!mkdir -p supabase/functions/embed-question
!mkdir -p supabase/functions/generate-answer

# Edge Function 1: embed-question
embed_function_code = '''import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

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
    
    // Call OpenAI embeddings API
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
'''

# Edge Function 2: generate-answer
answer_function_code = '''import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

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
    
    // Build context from talks
    const context = context_talks.map((talk, i) => 
      `Talk ${i+1}: "${talk.title}" by ${talk.speaker}\\n${talk.text}`
    ).join('\\n\\n')
    
    // Call OpenAI GPT-4
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
            content: `Question: ${question}\\n\\nRelevant Talks:\\n${context}`
          }
        ],
        temperature: 0.7,
        max_tokens: 500
      })
    })
    
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
'''

# Write files
with open('supabase/functions/embed-question/index.ts', 'w') as f:
    f.write(embed_function_code)

with open('supabase/functions/generate-answer/index.ts', 'w') as f:
    f.write(answer_function_code)

print("✅ Edge Function code created!")
print("   - supabase/functions/embed-question/index.ts")
print("   - supabase/functions/generate-answer/index.ts")
```

## Step 5c: Deploy Edge Functions

```python
# @title 🚀 Deploy Edge Functions to Supabase

# Link to your project
!supabase link --project-ref {SUPABASE_PROJECT_REF}

# Deploy embed-question function
print("Deploying embed-question...")
!supabase functions deploy embed-question --no-verify-jwt

# Deploy generate-answer function
print("\\nDeploying generate-answer...")
!supabase functions deploy generate-answer --no-verify-jwt

# Set OpenAI API key as secret
print("\\nSetting OpenAI API key secret...")
!supabase secrets set OPENAI_API_KEY={OPENAI_API_KEY}

print("\\n✅ Edge Functions deployed successfully!")
```

## Step 5d: Test Edge Functions

```python
# ✅ CHECKPOINT 3: Test Edge Functions

import requests
import json

print("Testing Edge Functions...\\n")

# Test embed-question
test_question = "What is faith?"
embed_url = f"{SUPABASE_URL}/functions/v1/embed-question"

try:
    response = requests.post(
        embed_url,
        headers={
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        },
        json={"question": test_question}
    )
    result = response.json()
    
    if 'embedding' in result:
        print("✅ embed-question function works!")
        print(f"   Embedding length: {len(result['embedding'])} dimensions")
    else:
        print(f"❌ Error: {result}")
except Exception as e:
    print(f"❌ Test failed: {e}")

print()

# Test generate-answer
answer_url = f"{SUPABASE_URL}/functions/v1/generate-answer"
test_talks = [
    {
        "title": "Test Talk",
        "speaker": "Test Speaker",
        "text": "This is a test talk about faith. Faith is belief in things hoped for."
    }
]

try:
    response = requests.post(
        answer_url,
        headers={
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        },
        json={"question": test_question, "context_talks": test_talks}
    )
    result = response.json()
    
    if 'answer' in result:
        print("✅ generate-answer function works!")
        print(f"   Answer: {result['answer'][:100]}...")
    else:
        print(f"❌ Error: {result}")
except Exception as e:
    print(f"❌ Test failed: {e}")
```

### 💡 Learning Checkpoint

**Why Edge Functions instead of client-side API calls?**

🔒 **Security**: API keys stay on the server, never exposed to users

**Compare:**
- ❌ Bad: API key in browser → anyone can steal it
- ✅ Good: API key in Edge Function → only Supabase can access it

This is a **production best practice**!
