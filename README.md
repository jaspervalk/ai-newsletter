# AI Newsletter Agent

Every Monday at 8 AM, an AI agent reads the internet, figures out what actually mattered in AI that week, and emails me a clean, well-structured newsletter. Then it goes back to sleep until next Monday.

I built this because the AI space moves too fast to keep up with manually. Twitter is noise, Hacker News is hit-or-miss, and most newsletters are either too shallow or written days late. So I let Claude do the reading for me.

## What it does

- Uses Claude (Sonnet 4) with the `web_search` tool to scan the web for the past 7 days of AI news
- Asks Claude to curate, summarize, and structure the findings into 5 categories: new models, research, tools, industry moves, and worth-reading deep dives
- Returns the result as structured JSON, which gets rendered into a clean HTML email
- Ships it to my inbox via Gmail SMTP
- Runs automatically every Monday morning via GitHub Actions — zero servers, zero maintenance

The whole thing is ~170 lines of Python. The agent makes its own search queries, decides what's important, and writes the copy. I just read the email.

## Why I think it's interesting

A few design choices worth calling out:

- **Agentic by design.** Claude isn't just summarizing a feed, it decides what to search for, follows up on what it finds, and judges what's worth including. The newsletter changes shape week to week based on what actually happened.
- **Structured output, not prompt-and-pray.** The agent returns strict JSON, which decouples the "thinking" from the "rendering." if you want a different email design, you change the template, not the prompt.
- **Cheap to run.** ~$0.12 per newsletter, including web searches. About 50 cents a month for something I'd otherwise pay a human curator for.
- **Free hosting.** GitHub Actions handles the schedule. No cron server, no Lambda, no deploy pipeline.

## Stack

- **Claude API** (`claude-sonnet-4`) with the `web_search_20250305` tool
- **Python 3.11**, single file, one dependency (`anthropic`)
- **Gmail SMTP** for delivery
- **GitHub Actions** for scheduling

## Run it yourself

```bash
git clone https://github.com/jaspervalk/ai-newsletter.git
cd ai-newsletter
cp .env.example .env   # fill in your keys
pip install -r requirements.txt
export $(cat .env | xargs) && python main.py
```

You'll need:

| Variable             | What it is                                                                 |
|----------------------|----------------------------------------------------------------------------|
| `ANTHROPIC_API_KEY`  | From [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `GMAIL_ADDRESS`      | The Gmail you're sending from                                              |
| `GMAIL_APP_PASSWORD` | A 16-char [App Password](https://myaccount.google.com/apppasswords) — not your real password |
| `RECIPIENT_EMAIL`    | Where the newsletter lands (can be the same address)                       |

To deploy on a schedule, push to GitHub, drop those four values into **Settings → Secrets and variables → Actions**, and the workflow in [`.github/workflows/newsletter.yml`](.github/workflows/newsletter.yml) takes it from there.

## Making it your own

The whole agent personality lives in the `system` prompt in [`main.py`](main.py). Want a newsletter focused on healthcare AI, robotics, or open-source models specifically? Edit the prompt. Want different sections? Edit the JSON schema in the user message. Want a different email design? Edit [`newsletter_template.py`](newsletter_template.py).

To change when it runs, edit the cron line in the workflow:

```yaml
- cron: "0 7 * * 1"     # Mondays at 8 AM CET (default)
- cron: "0 7 * * 1,4"   # Mondays + Thursdays
- cron: "0 7 * * *"     # Daily
```

## Project layout

```
ai-newsletter/
├── main.py                   # The agent — Claude + web search → JSON → email
├── newsletter_template.py    # HTML email template
├── requirements.txt
├── .env.example
└── .github/workflows/
    └── newsletter.yml        # Weekly schedule
```

---

Built by [Jasper Valk](https://github.com/jaspervalk). If you build something fun on top of this, I'd love to hear about it.
