"""
End-to-end test: use the scraper's own URL discovery to find a real talk,
then verify encoding + selectors work.
"""
import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# Step 1: Discover talk URLs (same logic as setup_local.py get_talk_urls)
conf_url = 'https://www.churchofjesuschrist.org/study/general-conference/2024/04?lang=eng'
print("Discovering talk URLs from:", conf_url)
response = session.get(conf_url, timeout=15)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

session_slugs = ['saturday-morning', 'saturday-afternoon', 'sunday-morning', 
                 'sunday-afternoon', 'priesthood-session', 'women-session', 
                 'womens-session', 'session', 'video']
talk_urls = []
seen = set()
for link in soup.find_all('a', href=True):
    href = link.get('href')
    if not href or '/study/general-conference/2024/04/' not in href or 'lang=eng' not in href:
        continue
    canonical = 'https://www.churchofjesuschrist.org' + href
    if canonical in seen:
        continue
    seen.add(canonical)
    if any(slug in canonical.lower() for slug in session_slugs):
        continue
    if href.rstrip('?lang=eng').endswith('/04'):
        continue
    talk_urls.append(canonical)

print(f"Found {len(talk_urls)} talks")
for u in talk_urls[:5]:
    print(f"  {u}")

# Step 2: Scrape a talk and test encoding
if talk_urls:
    # Pick a talk — try to find Caussé's talk
    causse_url = None
    for u in talk_urls:
        if 'causse' in u.lower():
            causse_url = u
            break
    
    test_url = causse_url or talk_urls[0]
    print(f"\nTesting scrape of: {test_url}")
    
    resp = session.get(test_url, timeout=15)
    resp.encoding = 'utf-8'
    s = BeautifulSoup(resp.text, 'html.parser')
    
    title = s.find("h1")
    speaker = s.find("p", {"class": "author-name"})
    body = s.find("div", {"class": "body-block"})
    
    print(f"  Title:      {title.text.strip()[:80] if title else 'NOT FOUND'}")
    print(f"  Speaker:    {speaker.text.strip() if speaker else 'NOT FOUND'}")
    print(f"  Body:       {'FOUND (' + str(len(body.find_all('p'))) + ' paragraphs)' if body else 'NOT FOUND'}")
    
    if body:
        text = ' '.join(p.text.strip() for p in body.find_all('p'))
        has_mojibake = any(bad in text for bad in ['Ã©', 'Ã', 'â\u0080\u0099', 'Â'])
        print(f"  Mojibake:   {'YES ⚠️' if has_mojibake else 'NO ✅'}")
        print(f"  Sample:     {text[:200]}")
    
    if speaker:
        has_mojibake_speaker = any(bad in speaker.text for bad in ['Ã©', 'Ã', 'â\u0080\u0099', 'Â'])
        print(f"  Speaker mojibake: {'YES ⚠️' if has_mojibake_speaker else 'NO ✅'}")
