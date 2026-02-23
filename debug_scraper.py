"""Debug scraper to find correct selectors for conference talks."""
import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

url = 'https://www.churchofjesuschrist.org/study/general-conference/2024/10?lang=eng'
resp = session.get(url, timeout=15)
print(f'Status: {resp.status_code}')
soup = BeautifulSoup(resp.text, 'html.parser')

# Check various selectors
selectors = [
    'div.talk-list a',
    'a[href*="/study/general-conference/2024/10/"]',
    'a[href*="general-conference"]',
    'li a[href*="general-conference"]',
]

for sel in selectors:
    results = soup.select(sel)
    print(f'\n{sel}: {len(results)} matches')
    for r in results[:5]:
        href = r.get('href', 'n/a')[:80]
        text = r.get_text(strip=True)[:60]
        print(f'  -> {href}  |  {text}')

# Find all links containing /study/general-conference/2024/
all_links = soup.find_all('a', href=True)
gc_links = [a for a in all_links if '/study/general-conference/2024/' in a.get('href', '')]
print(f'\nAll conference links found: {len(gc_links)}')
for link in gc_links[:10]:
    print(f'  -> {link.get("href")[:80]}')
    # Show parent structure
    parent = link.parent
    parents = []
    while parent and parent.name:
        classes = ' '.join(parent.get('class', []))
        parents.append(f'{parent.name}.{classes}' if classes else parent.name)
        if len(parents) >= 3:
            break
        parent = parent.parent
    print(f'     parents: {" > ".join(reversed(parents))}')
