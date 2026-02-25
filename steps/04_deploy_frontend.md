# Step 4: Deploy Frontend to GitHub Pages

## What You'll Learn
- How static site hosting works with GitHub Pages
- How Supabase Auth magic links work
- How the frontend connects to your backend

## What to Do

### 1. Enable GitHub Pages

1. Go to your repository on GitHub (**your fork**, not the original)
2. Click **Settings** → **Pages** (in the left sidebar)
3. Under "Source", select **Deploy from a branch**
4. Set Branch: **main**, Folder: **/ (root)**
5. Click **Save**
6. Wait ~1 minute, then refresh — you'll see your deployment URL

Your site will be live at: `https://YOUR-USERNAME.github.io/conference-rag/`

> ⚠️ Your repo must be **public** for free GitHub Pages hosting.

### 2. Update `config.js` (If Not Already Done)

Make sure `config.js` has your real Supabase URL and anon key (you may have done this in Step 2). Commit and push:

```bash
git add config.js
git commit -m "Add Supabase credentials"
git push
```

Wait ~1 minute for GitHub Pages to redeploy, then visit your site.

### 3. Configure Auth Redirect URL

1. Go to **Supabase Dashboard** → **Authentication** → **URL Configuration**
2. Under "Redirect URLs", click **Add URL**
3. Paste your GitHub Pages URL: `https://YOUR-USERNAME.github.io/conference-rag/`
4. Click **Save**

### 4. Test Login

1. Visit your deployed site
2. Enter your email
3. Click "Sign In with Magic Link"
4. Check your inbox and click the link
5. You should be logged in! ✅

**Expected behavior**: You can log in, but all three search modes show **"Not Ready"** — that's correct! They'll light up as you complete the remaining steps.

> 💡 **Ask your AI assistant**: *"How do magic link logins work? What are the security advantages over passwords?"*

## Verification

- [ ] Site is live at your GitHub Pages URL
- [ ] You can see the Conference Q&A interface
- [ ] Magic link login works (you receive the email and can log in)
- [ ] All three search modes show "Not Ready" (expected at this point)

→ Next: [Step 05: Deploy Edge Functions](05_edge_functions.md)
