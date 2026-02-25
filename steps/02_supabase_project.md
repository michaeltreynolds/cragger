# Step 2: Create Supabase Project & Get Credentials

## What You'll Learn
- What Supabase is and why we use it (Postgres + Auth + Edge Functions as a service)
- How API keys and access tokens work
- The difference between `anon` (public) and `service_role` (admin) keys

## What to Do

### 1. Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and sign up / sign in
2. Click **"New Project"**
3. Fill in:
   - **Name**: `conference-rag` (or anything you like)
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Choose the one closest to you
4. Click **"Create new project"** — takes ~2 minutes to provision

### 2. Collect Your Credentials

You'll need **six values**. Here's where to find each one:

| Credential | Where to Find It |
|-----------|------------------|
| `SUPABASE_URL` | Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Settings → API → `anon` `public` key |
| `SUPABASE_SERVICE_KEY` | Settings → API → `service_role` key (click "Reveal") |
| `SUPABASE_PROJECT_REF` | Extract from your URL: `https://XXXXX.supabase.co` → `XXXXX` |
| `SUPABASE_ACCESS_TOKEN` | [Account Tokens page](https://supabase.com/dashboard/account/tokens) → Generate new token |
| `OPENAI_API_KEY` | [OpenAI API Keys](https://platform.openai.com/api-keys) → Create new secret key |

### 3. Fill in `config.secret.json`

Open `config.secret.json` (you created it in Step 1) and paste in your real values:

```json
{
    "OPENAI_API_KEY": "sk-proj-...",
    "SUPABASE_ACCESS_TOKEN": "sbp_...",
    "SUPABASE_ANON_KEY": "eyJ...",
    "SUPABASE_PROJECT_REF": "xyzabc123",
    "SUPABASE_SERVICE_KEY": "eyJ...",
    "SUPABASE_URL": "https://xyzabc123.supabase.co"
}
```

### 4. Update `config.js` (Frontend Config)

Open `config.js` in the project root and replace the placeholder values with your **URL** and **anon key**:

```javascript
const SUPABASE_CONFIG = {
    url: 'https://xyzabc123.supabase.co',
    anonKey: 'eyJ...'
};
```

> 💡 **Ask your AI assistant**: *"What is the difference between the Supabase anon key and the service role key? Why is one safe to put in client-side code?"*

## Verification

- [ ] Supabase project is created and accessible at your dashboard
- [ ] All six credentials are filled into `config.secret.json`
- [ ] `config.js` has your URL and anon key

→ Next: [Step 03: Create Database Schema](03_database_schema.md)
