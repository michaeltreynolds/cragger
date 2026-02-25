"""
Compare Option A (runtime scraping) vs Option C (query all sentences from DB).
Tests against a real talk URL and the same talk's sentences in the database.
"""
import requests
from bs4 import BeautifulSoup
import time
import json

# Load secrets
with open('config.secret.json', 'r') as f:
    secrets = json.load(f)

from supabase import create_client
client = create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_SERVICE_KEY'])

# ============================================
# Find a talk that exists in both DB and has a URL
# ============================================
print("=" * 60)
print("Finding a talk in the DB with a URL...")
print("=" * 60)

result = client.table('sentence_embeddings') \
    .select('url, talk_id, title, speaker') \
    .neq('url', '') \
    .limit(1) \
    .execute()

if not result.data:
    print("No URLs found in database!")
    exit(1)

sample = result.data[0]
talk_id = sample['talk_id']
talk_url = sample['url']
print(f"Talk: {sample['title']}")
print(f"Speaker: {sample['speaker']}")
print(f"URL: {talk_url}")
print(f"talk_id: {talk_id}")

# Also test the user-provided URL
user_url = "https://www.churchofjesuschrist.org/study/general-conference/2025/04/31stevenson?lang=eng"

# ============================================
# OPTION C: Query all sentences for this talk_id
# ============================================
print("\n" + "=" * 60)
print("OPTION C: Query all sentences from DB (ordered by sentence_num)")
print("=" * 60)

start_c = time.time()
all_sentences = client.table('sentence_embeddings') \
    .select('sentence_num, text') \
    .eq('talk_id', talk_id) \
    .order('sentence_num') \
    .execute()
time_c = time.time() - start_c

if all_sentences.data:
    option_c_text = " ".join(row['text'] for row in all_sentences.data)
    print(f"  Sentences found: {len(all_sentences.data)}")
    print(f"  sentence_num range: {all_sentences.data[0]['sentence_num']} - {all_sentences.data[-1]['sentence_num']}")
    print(f"  Total text length: {len(option_c_text):,} chars")
    print(f"  Query time: {time_c:.3f}s")
    print(f"\n  First 300 chars:\n  {option_c_text[:300]}...")
    print(f"\n  Last 300 chars:\n  ...{option_c_text[-300:]}")
else:
    option_c_text = ""
    print("  No sentences found!")

# ============================================
# OPTION A: Scrape full talk at runtime
# ============================================
print("\n" + "=" * 60)
print("OPTION A: Scrape talk at runtime (DB URL)")
print("=" * 60)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

def scrape_talk(url):
    start = time.time()
    response = session.get(url, timeout=15)
    fetch_time = time.time() - start
    
    print(f"  HTTP Status: {response.status_code}")
    print(f"  Fetch time: {fetch_time:.3f}s")
    
    if response.status_code != 200:
        print(f"  ❌ Non-200 response!")
        return None, fetch_time
    
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find("h1")
    speaker = soup.find("p", {"class": "author-name"})
    body = soup.find("div", {"class": "body-block"})
    
    print(f"  Title found: {'YES ' + title.text.strip()[:60] if title else 'NO'}")
    print(f"  Speaker found: {'YES ' + speaker.text.strip() if speaker else 'NO'}")
    print(f"  body-block found: {'YES' if body else 'NO'}")
    
    if body:
        paragraphs = body.find_all("p")
        full_text = " ".join(p.text.strip() for p in paragraphs)
        print(f"  Paragraphs: {len(paragraphs)}")
        print(f"  Full text length: {len(full_text):,} chars")
        return full_text, fetch_time
    return None, fetch_time

option_a_text, time_a = scrape_talk(talk_url)

if option_a_text:
    print(f"\n  First 300 chars:\n  {option_a_text[:300]}...")
    print(f"\n  Last 300 chars:\n  ...{option_a_text[-300:]}")

# Now test the user-provided URL
print("\n" + "=" * 60)
print(f"OPTION A: Scrape user-provided URL")
print("=" * 60)
print(f"  URL: {user_url}")
user_text, time_user = scrape_talk(user_url)
if user_text:
    print(f"\n  First 200 chars:\n  {user_text[:200]}...")

# ============================================
# COMPARISON
# ============================================
print("\n" + "=" * 60)
print("COMPARISON: Option A vs Option C")
print("=" * 60)

if option_a_text and option_c_text:
    print(f"\n  Option A (scrape): {len(option_a_text):,} chars | {time_a:.3f}s")
    print(f"  Option C (DB):     {len(option_c_text):,} chars | {time_c:.3f}s")
    print(f"  Speed advantage:   Option C is {time_a/time_c:.1f}x faster")
    
    # Check overlap
    # Simple: how many of Option C's sentences appear in Option A's text?
    matches = 0
    total = len(all_sentences.data)
    for row in all_sentences.data:
        sent = row['text'][:50]  # first 50 chars of each sentence
        if sent in option_a_text:
            matches += 1
    print(f"  Content overlap:   {matches}/{total} DB sentences found in scraped text ({matches/total*100:.0f}%)")
    print(f"\n  Length difference:  {abs(len(option_a_text) - len(option_c_text)):,} chars")
    if len(option_a_text) > len(option_c_text):
        print(f"  Winner (coverage): Option A has {len(option_a_text) - len(option_c_text):,} more chars")
    else:
        print(f"  Winner (coverage): Option C has {len(option_c_text) - len(option_a_text):,} more chars")

# Check if match_sentences returns url
print("\n" + "=" * 60)
print("Does match_sentences return 'url'?")
print("=" * 60)
print("Current match_sentences SQL returns: id, talk_id, title, speaker, text, similarity")
print("'url' is NOT in the return columns — needs SQL update to include it")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
