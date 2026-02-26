# Step 6: Scrape Conference Talks

## What You'll Learn
- How web scraping works (HTTP requests + HTML parsing)
- What BeautifulSoup does and how CSS selectors find data
- How concurrent scraping speeds up data collection
- How to structure scraped data as JSON for downstream processing

## Background

Before we can search conference talks, we need the data! The scraping script:

1. **Finds conference index pages** for the last 5 years (April + October each year)
2. **Extracts talk URLs** from each conference page
3. **Scrapes each talk** in parallel (title, speaker, calling, year, season, URL, full text)
4. **Saves structured JSON** to `data/talks.json`

> 💡 **Ask your AI assistant**: *"What is web scraping? How does BeautifulSoup parse HTML?"*

## What to Do

Make sure your virtual environment is activated, then run:

```bash
python scripts/02_scrape_data.py
```

This takes a few minutes — it's downloading and parsing ~400 web pages.

### What the Output Looks Like

The script creates `data/talks.json` with records like:

```json
{
    "title": "The Prodigal and the Road That Leads Home",
    "speaker": "President Dallin H. Oaks",
    "calling": "First Counselor in the First Presidency",
    "year": 2024,
    "season": "April",
    "url": "https://www.churchofjesuschrist.org/study/...",
    "text": "The full text of the talk as one string..."
}
```

### Understanding the Scraper

Take a look at `scripts/02_scrape_data.py`:

| Function | What It Does |
|----------|-------------|
| `setup_session()` | Creates an HTTP session with a browser-like user agent |
| `get_conference_urls()` | Generates URLs for each conference (April + October per year) |
| `get_talk_urls()` | Extracts individual talk URLs from a conference index page |
| `scrape_talk()` | Scrapes a single talk page and returns structured data |

> 💡 **Ask your AI assistant**: *"Why does the scraper use `ThreadPoolExecutor`? What is concurrent scraping?"*

## Verification

- [ ] Script completes without errors
- [ ] `data/talks.json` exists and contains talk objects
- [ ] Script reports scraping ~300-400+ talks
- [ ] Spot-check: open `data/talks.json` and verify a few entries have proper titles, speakers, and text

## → Next: [Step 07: Generate Embeddings & Import](07_embed_and_import.md)

> 🤖 **AI coding assistant?** Read [ai_agent_instructions.md](../ai_agent_instructions.md) for guidance on helping students with this assignment.
