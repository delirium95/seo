# SEO Automation

Fully automated pipeline: drop a keyword + GEO into a Google Sheet and get back a Google Doc with competitor analysis and AI-generated, ready-to-publish meta tags. No manual work, no copy-paste, no excuses.

---

## What it does

```
Google Sheets
  (Keyword | GEO | Language)
         │
         ▼
   SerpAPI — TOP-10 Google results for keyword×GEO
         │
         ▼ (filter: affiliate/review sites only)
   Scraper — fetch H1, Meta Title, Meta Description,
             site headings for up to 3 competitors
         │
         ▼
   Claude (claude-opus-4-7) — analyze competitors,
         generate optimized H1 + Title + Description
         in the specified language
         │
         ▼
   Google Docs — create "{Keyword}-{GEO}" document
         with Competitor Reports + Optimized Content
         set to "Anyone with link = Commenter"
         │
         ▼
   Google Sheets — write doc URL back to Result column
```

One command, full cycle, multiple keywords in one run.

---

## Architecture

| File | Responsibility |
|---|---|
| `main.py` | Orchestrator — reads sheet rows, calls each module, handles errors |
| `models.py` | Pydantic data models: `SheetRow`, `SerpResult`, `ScrapedPage`, `GeneratedMeta` |
| `config.py` | `pydantic-settings` config — all env vars in one place, validated at startup |
| `serp_client.py` | SerpAPI call, affiliate-signal filtering, returns `SerpResult[]` |
| `scraper.py` | `httpx` + `BeautifulSoup` page scraping, fault-tolerant (blocked → `error` field) |
| `ai_client.py` | Claude API call with structured prompt, returns `GeneratedMeta` as JSON |
| `sheets_client.py` | Google Sheets read (rows) + write (result URL) |
| `docs_client.py` | Google Docs creation + `batchUpdate` for content + Drive permission set |
| `google_auth.py` | OAuth2 flow — first run opens browser, saves `token.json` for subsequent runs |

---

## Setup

### 1. Clone and install

```bash
git clone <repo>
cd seo-automation
uv sync
```

### 2. Google Cloud credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → create or select a project
2. Enable these three APIs: **Google Sheets API**, **Google Docs API**, **Google Drive API**
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**
4. Configure consent screen if prompted (External, add your email as Test User)
5. Application type: **Desktop app** → download the JSON → save as `credentials.json` in project root
6. **First run** opens a browser window for Google login — authorize once, token saved to `token.json` automatically. All subsequent runs are fully headless.

### 3. API keys

| Key | Where to get |
|---|---|
| `SERP_API_KEY` | [serpapi.com](https://serpapi.com) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |

### 4. Configure

```bash
cp .env.example .env
# fill in all values
```

### 5. Google Sheet format

| A: Keyword | B: GEO | C: Language | D: Result |
|---|---|---|---|
| casino en ligne | FR | fr | _(filled automatically)_ |
| aviator game | IN | en | |
| novibet casino | IE | en | |

---

## Run

### Local (uv)

```bash
uv run python main.py
```

### Docker

```bash
docker compose up
```

The container reads `.env` and mounts `credentials.json` as read-only. No extra setup needed.

---

## Rules enforced on generated meta

- **Keyword first** — H1 and Title always start with the exact keyword
- **No emojis** anywhere
- **Banned words** — Discover, Thrilling, Enjoy, Excitement, "Dive into", Experience
- **Title** 40–60 characters, every word capitalized
- **Description** < 160 characters, sentence capitalization
- **Language** — Claude writes in whatever ISO 639-1 code you put in the Language column

---

## Error handling

- Blocked/timeout site → logged as failed, moves to next in TOP-10
- If fewer than 3 succeed — continues with what it has, reports failures in the doc
- Sheet rows with a non-empty `Result` column are skipped (idempotent reruns)
- Any row-level error is logged and printed at the end; exit code 1 if any row failed

---

## Submission checklist 

- [x] GitHub repo: https://github.com/delirium95/seo
- [x] Google Sheet: https://docs.google.com/spreadsheets/d/1gX2tOxA5Excpn4zwedneiJAZ5sf7y37Rqo7T5--wDOg/edit
- [ ] Video demo: 2-3 keywords × different GEOs
- [x] README with architecture + launch instructions
