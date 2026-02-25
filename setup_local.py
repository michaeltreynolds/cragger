"""
Local setup script for cragger.
Runs the database schema creation, data scraping, embedding generation, and import.
"""

import json
import sys
import os

# Load secrets
with open('config.secret.json', 'r') as f:
    secrets = json.load(f)

SUPABASE_URL = secrets['SUPABASE_URL']
SUPABASE_SERVICE_KEY = secrets['SUPABASE_SERVICE_KEY']
SUPABASE_ANON_KEY = secrets['SUPABASE_ANON_KEY']
SUPABASE_ACCESS_TOKEN = secrets['SUPABASE_ACCESS_TOKEN']
SUPABASE_PROJECT_REF = secrets['SUPABASE_PROJECT_REF']
OPENAI_API_KEY = secrets['OPENAI_API_KEY']

# ============================================
# STEP 1: Create Database Schema
# ============================================

def create_schema():
    import requests

    print("=" * 60)
    print("STEP 1: Creating Database Schema")
    print("=" * 60)

    schema_sql = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create sentence_embeddings table
CREATE TABLE IF NOT EXISTS sentence_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    talk_id UUID NOT NULL,
    title TEXT NOT NULL,
    speaker TEXT,
    calling TEXT,
    year INTEGER,
    season TEXT,
    url TEXT,
    sentence_num INTEGER,
    text TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for talk_id grouping
CREATE INDEX IF NOT EXISTS sentence_embeddings_talk_id_idx 
ON sentence_embeddings(talk_id);

-- Enable Row Level Security
ALTER TABLE sentence_embeddings ENABLE ROW LEVEL SECURITY;

-- RLS policy: authenticated users can read
DROP POLICY IF EXISTS "Allow authenticated users to read" ON sentence_embeddings;
CREATE POLICY "Allow authenticated users to read"
ON sentence_embeddings FOR SELECT
TO authenticated
USING (true);

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_sentences(
  query_embedding vector(1536),
  match_count int DEFAULT 20
)
RETURNS TABLE (
  id uuid,
  talk_id uuid,
  title text,
  speaker text,
  text text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    sentence_embeddings.id,
    sentence_embeddings.talk_id,
    sentence_embeddings.title,
    sentence_embeddings.speaker,
    sentence_embeddings.text,
    1 - (sentence_embeddings.embedding <=> query_embedding) as similarity
  FROM sentence_embeddings
  ORDER BY sentence_embeddings.embedding <=> query_embedding
  LIMIT match_count;
$$;
"""

    url = f"https://api.supabase.com/v1/projects/{SUPABASE_PROJECT_REF}/database/query"
    headers = {
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    resp = requests.post(url, headers=headers, json={"query": schema_sql})
    if resp.status_code == 200 or resp.status_code == 201:
        print("✅ Database schema created successfully!")
    else:
        print(f"❌ Schema creation failed: {resp.status_code}")
        print(resp.text[:500])
        return False

    # Verify (PostgREST cache may need a moment to refresh)
    import time
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    for attempt in range(5):
        try:
            result = client.table('sentence_embeddings').select('id', count='exact').limit(1).execute()
            print(f"✅ Table verified. Current rows: {result.count or 0}")
            return True
        except Exception as e:
            if attempt < 4:
                print(f"   Waiting for schema cache to refresh... ({attempt + 1}/5)")
                time.sleep(3)
            else:
                print(f"⚠️  Table created but PostgREST cache hasn't refreshed yet.")
                print(f"   This is normal. Proceeding anyway - it should be ready by import time.")
                return True


# ============================================
# STEP 2: Scrape Conference Talks
# ============================================

def scrape_talks():
    import requests as req
    from bs4 import BeautifulSoup
    import pandas as pd
    import re
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm

    print("\n" + "=" * 60)
    print("STEP 2: Scraping Conference Talks")
    print("=" * 60)

    YEARS_TO_SCRAPE = 5
    START_YEAR = 2025 - YEARS_TO_SCRAPE
    END_YEAR = 2025

    session = req.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    base_url = 'https://www.churchofjesuschrist.org/study/general-conference/{year}/{month}?lang=eng'
    conference_urls = [(base_url.format(year=year, month=month), str(year), month)
                       for year in range(START_YEAR, END_YEAR + 1)
                       for month in ['04', '10']]

    session_slugs = [
        'saturday-morning', 'saturday-afternoon', 'sunday-morning', 'sunday-afternoon',
        'priesthood-session', 'women-session', 'womens-session', 'session', 'video'
    ]

    def get_talk_urls(conf_url, year, month):
        try:
            response = session.get(conf_url, timeout=10)
            response.raise_for_status()
        except:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        talk_urls = []
        seen = set()
        month_path = f'/study/general-conference/{year}/{month}/'
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href or month_path not in href or 'lang=eng' not in href:
                continue
            canonical = 'https://www.churchofjesuschrist.org' + href
            if canonical in seen:
                continue
            seen.add(canonical)
            if any(slug in canonical.lower() for slug in session_slugs):
                continue
            # Skip the conference index page itself
            if href.rstrip('?lang=eng').endswith(f'/{month}'):
                continue
            talk_urls.append(canonical)
        return talk_urls

    def scrape_talk(talk_url):
        try:
            response = session.get(talk_url, timeout=10)
            response.raise_for_status()
        except:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find("h1").text.strip() if soup.find("h1") else "No Title"
        speaker_tag = soup.find("p", {"class": "author-name"})
        speaker = speaker_tag.text.strip() if speaker_tag else "Unknown"
        calling_tag = soup.find("p", {"class": "author-role"})
        calling = calling_tag.text.strip() if calling_tag else ""
        content_div = soup.find("div", {"class": "body-block"})
        if not content_div:
            return None
        content = " ".join(p.text.strip() for p in content_div.find_all("p"))
        year_match = re.search(r'/(\d{4})/', talk_url)
        year = int(year_match.group(1)) if year_match else None
        season_val = "April" if "/04/" in talk_url else "October"
        return {
            "title": title, "speaker": speaker, "calling": calling,
            "year": year, "season": season_val, "url": talk_url, "text": content
        }

    print(f"Scraping {YEARS_TO_SCRAPE} years ({START_YEAR}-{END_YEAR})...")
    all_talk_urls = []
    for conf_url, year, month in tqdm(conference_urls, desc="Finding talks"):
        urls = get_talk_urls(conf_url, year, month)
        all_talk_urls.extend(urls)
    print(f"Found {len(all_talk_urls)} talks")

    print("Scraping content...")
    talks_data = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scrape_talk, url): url for url in all_talk_urls}
        for future in tqdm(as_completed(futures), total=len(all_talk_urls), desc="Scraping"):
            talk = future.result()
            if talk:
                talks_data.append(talk)

    talks_df = pd.DataFrame(talks_data)
    if len(talks_df) == 0:
        print("\n❌ No talks scraped! Check your internet connection or website structure.")
        return talks_df
    print(f"\n✅ Scraped {len(talks_df)} talks!")
    print(f"   Years: {talks_df['year'].min()} - {talks_df['year'].max()}")
    return talks_df


# ============================================
# STEP 3: Split into Sentences & Generate Embeddings
# ============================================

def process_and_import(talks_df):
    import uuid
    import re
    import time
    import pandas as pd
    from tqdm import tqdm
    from openai import OpenAI
    from supabase import create_client

    print("\n" + "=" * 60)
    print("STEP 3: Splitting into Sentences")
    print("=" * 60)

    def split_into_sentences(text):
        sentences = re.split(r'\. (?=[A-Z])', text)
        sentences = [s.strip() + '.' if not s.endswith('.') else s.strip() for s in sentences]
        return [s for s in sentences if len(s) > 20]

    sentence_records = []
    for _, talk in tqdm(talks_df.iterrows(), total=len(talks_df), desc="Splitting"):
        talk_id = str(uuid.uuid4())
        sentences = split_into_sentences(talk['text'])
        for i, sentence in enumerate(sentences, 1):
            sentence_records.append({
                'talk_id': talk_id, 'title': talk['title'], 'speaker': talk['speaker'],
                'calling': talk['calling'], 'year': int(talk['year']) if talk['year'] else None,
                'season': talk['season'], 'url': talk['url'],
                'sentence_num': i, 'text': sentence
            })

    sentences_df = pd.DataFrame(sentence_records)
    print(f"✅ Split {len(talks_df)} talks into {len(sentences_df):,} sentences")

    # Generate Embeddings
    print("\n" + "=" * 60)
    print("STEP 4: Generating OpenAI Embeddings")
    print("=" * 60)

    client = OpenAI(api_key=OPENAI_API_KEY)
    BATCH_SIZE = 100
    embeddings = []

    print(f"Generating embeddings for {len(sentences_df):,} sentences...")
    for i in tqdm(range(0, len(sentences_df), BATCH_SIZE), desc="Embedding"):
        batch_texts = sentences_df['text'].iloc[i:i+BATCH_SIZE].tolist()
        try:
            response = client.embeddings.create(model='text-embedding-3-small', input=batch_texts)
            embeddings.extend([item.embedding for item in response.data])
        except Exception as e:
            print(f"\nError at batch {i//BATCH_SIZE}: {e}")
            embeddings.extend([None] * len(batch_texts))
        time.sleep(0.1)

    sentences_df['embedding'] = embeddings
    sentences_df = sentences_df[sentences_df['embedding'].notna()]
    print(f"✅ Generated {len(sentences_df):,} embeddings")

    # Import to Supabase
    print("\n" + "=" * 60)
    print("STEP 5: Importing to Supabase")
    print("=" * 60)

    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    records = sentences_df.to_dict('records')
    for record in records:
        if hasattr(record['embedding'], 'tolist'):
            record['embedding'] = record['embedding'].tolist()

    BATCH_SIZE = 100
    success = 0
    errors = 0

    for i in tqdm(range(0, len(records), BATCH_SIZE), desc="Importing"):
        batch = records[i:i+BATCH_SIZE]
        try:
            supabase_admin.table('sentence_embeddings').insert(batch).execute()
            success += len(batch)
        except Exception as e:
            print(f"\nError at batch {i//BATCH_SIZE}: {e}")
            errors += len(batch)
        time.sleep(0.1)

    print(f"\n✅ Import complete! Success: {success:,}, Errors: {errors}")
    return success


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if step in ('all', 'schema'):
        if not create_schema():
            sys.exit(1)

    if step in ('all', 'data'):
        talks_df = scrape_talks()
        if len(talks_df) == 0:
            print("No talks to process. Exiting.")
            sys.exit(1)
        process_and_import(talks_df)

    if step == 'schema':
        print("\nSchema created! Run again with 'data' to scrape and import.")
    elif step in ('all', 'data'):
        print("\n" + "=" * 60)
        print("🎉 ALL DONE! Refresh your site to see search panels light up.")
        print("=" * 60)
