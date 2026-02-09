# Part 4: Frontend Deployment (15 min)

Now let's get your site live! You'll deploy first, then configure Supabase credentials.

## Step 4a: Enable GitHub Pages

Your forked repo needs GitHub Pages turned on:

1. Go to your repository on GitHub (your fork, not the original!)
2. Click **Settings** (gear icon near the top)
3. Click **Pages** in the left sidebar
4. Under **"Source"**, select **Deploy from a branch**
5. Set Branch to **main** and Folder to **/ (root)**
6. Click **Save**
7. Wait ~1 minute, then refresh the page

> ⚠️ **Your repo must be public** for free GitHub Pages hosting. If it's private, go to Settings → General → Danger Zone → Change visibility → Make public.

Your site will be live at: `https://YOUR-USERNAME.github.io/conference-rag/`

🎉 **Visit your URL now!** You should see the Conference Q&A app with a "Setup Required" banner. That's expected — we'll configure it next.

## Step 4b: Update config.js

Now let's connect your app to Supabase:

1. Go to your repository on GitHub
2. Click on `config.js`
3. Click the pencil icon (✏️) to edit
4. Replace the placeholder values:

```javascript
const SUPABASE_CONFIG = {
    url: 'YOUR_SUPABASE_URL',      // Replace with your actual URL
    anonKey: 'YOUR_ANON_KEY'       // Replace with your actual anon key
};
```

5. Click **"Commit changes"**
6. Wait ~1 minute for GitHub Pages to redeploy, then refresh your site

> 💡 **If changes don't appear:** Try a hard refresh (Ctrl+Shift+R) or open in an incognito window. GitHub Pages can sometimes cache old files.

## Step 4c: Configure Auth Redirect

Copy your deployed URL and add it to Supabase:

1. Go to Supabase Dashboard → **Authentication** → **URL Configuration**
2. Under "Redirect URLs", click **Add URL**
3. Paste: `https://YOUR-USERNAME.github.io/conference-rag/`
4. Click **Save**

> 💡 **Quick link:** Once you've configured `config.js`, your site's setup banner will show a direct link to your Supabase URL Configuration page.

## Step 4d: Test Login

1. Visit your deployed site
2. Enter your email
3. Click "Sign In with Magic Link"
4. Check your inbox
5. Click the magic link
6. You should be logged in! ✅

**Expected behavior**: You can log in, but the search features will show as "not ready" — we haven't imported data or deployed Edge Functions yet.

## ✅ Checkpoint 2

```python
# Verify your deployment

print("🌐 Check list:")
print("")
print("1. ✅ Site deployed to GitHub Pages?")
print("2. ✅ config.js updated with your credentials?")
print("3. ✅ Redirect URL added to Supabase?")
print("4. ✅ Successfully logged in?")
print("")
print("If yes to all, continue! If not, review the steps above.")
print("")
print("Your deployed URL should be:")
print(f"https://YOUR-USERNAME.github.io/conference-rag/")
```

### 💡 Learning Checkpoint

**Why do the search features show "not ready"?**

The app checks for three capabilities that you'll build in the upcoming steps:
1. **Keyword Search** — Needs conference data imported into the database
2. **Semantic Search** — Needs embeddings generated and the `embed-question` Edge Function deployed
3. **RAG (Ask a Question)** — Needs the `generate-answer` Edge Function deployed

Each one will "light up" as you complete the corresponding notebook section!
