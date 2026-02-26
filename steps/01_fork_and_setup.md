# Step 1: Fork the Repository & Set Up Locally

## What You'll Learn
- How forking works in Git and open-source workflows
- Setting up a Python virtual environment
- Organizing a project with secrets management

## What to Do

### 1. Fork the Repository

1. Go to: **https://github.com/byu-cs-452/conference-rag**
2. Click **"Fork"** in the top right → **"Create fork"**
3. Make sure your fork is **public** (required for free GitHub Pages hosting)

You now have your own copy at: `https://github.com/YOUR-USERNAME/conference-rag`

> 💡 **Why fork?** Forking is a fundamental open-source workflow. Your fork is your own copy that you can freely modify.

### 2. Clone Your Fork Locally

```bash
git clone https://github.com/YOUR-USERNAME/conference-rag.git
cd conference-rag
```

### 3. Set Up Python Environment

```bash
python -m venv .venv

# Activate:
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Create Your Secrets File

Copy the example file and fill in your real credentials (you'll get these in Step 2):

```bash
cp config.secret.example.json config.secret.json
```

> ⚠️ **`config.secret.json` is in `.gitignore`** — it will never be committed to your repo. This is how we keep API keys safe!

## Verification

- [ ] You have your own fork on GitHub
- [ ] Repo is cloned locally
- [ ] Virtual environment is activated (`(.venv)` appears in your terminal prompt)
- [ ] `pip install -r requirements.txt` completed without errors

## → Next: [Step 02: Create Supabase Project](02_supabase_project.md)

> 🤖 **AI coding assistant?** Read [ai_agent_instructions.md](../ai_agent_instructions.md) for guidance on helping students with this assignment.
