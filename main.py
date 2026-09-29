"""
AI Newsletter Agent
Uses Claude API with web search + web fetch to find the week's genuinely new
AI developments, then sends a formatted newsletter to your Gmail.

Usage:
    python main.py            # research, render, send, record issue history
    python main.py --dry-run  # research and render only (no email, no history)
"""

import anthropic
import json
import smtplib
import os
import sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from newsletter_template import render_newsletter


MODEL = "claude-sonnet-5"
HISTORY_FILE = "last_issue.json"
MAX_CONTINUATIONS = 8

_ITEM = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string", "description": "2-3 sentences with concrete specifics."},
        "why_it_matters": {
            "type": "string",
            "description": "One sentence on what this changes in the field. Omit if there's nothing concrete to say.",
        },
        "link": {"type": "string", "description": "Primary source URL."},
    },
    "required": ["title", "summary", "link"],
}

NEWSLETTER_TOOL = {
    "name": "submit_newsletter",
    "description": "Submit the finished weekly newsletter. Call this exactly once, after research is complete.",
    "eager_input_streaming": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "one_liner": {"type": "string", "description": "A single witty line capturing this week in AI."},
            "deep_dives": {
                "type": "array",
                "description": "The 1-3 most genuinely new developments of the week, explained in depth.",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "link": {"type": "string", "description": "Primary source URL (paper, lab blog, model card, repo)."},
                        "what_happened": {"type": "string", "description": "2-3 sentences: who released or found what, when."},
                        "how_it_works": {
                            "type": "string",
                            "description": "The technical substance: architecture, method, training setup, key numbers. 1-2 paragraphs, separated by a blank line.",
                        },
                        "why_it_matters": {
                            "type": "string",
                            "description": "What this changes technically or for the field: what becomes feasible, cheaper, or newly understood.",
                        },
                        "caveats": {"type": "string", "description": "Limits, self-reported results, open questions."},
                    },
                    "required": ["title", "link", "what_happened", "how_it_works", "why_it_matters", "caveats"],
                },
            },
            "sections": {
                "type": "array",
                "description": "Shorter items grouped into 2-4 sections. Only include sections that have news.",
                "items": {
                    "type": "object",
                    "properties": {
                        "emoji": {"type": "string"},
                        "title": {"type": "string"},
                        "items": {"type": "array", "description": "2-5 items.", "items": _ITEM},
                    },
                    "required": ["emoji", "title", "items"],
                },
            },
        },
        "required": ["one_liner", "deep_dives", "sections"],
    },
}


def load_previous_titles() -> list[str]:
    """Titles from the previous issue, so the agent doesn't repeat itself."""
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f).get("titles", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_issue_history(data: dict, date_str: str):
    titles = [d.get("title", "") for d in data.get("deep_dives", []) if isinstance(d, dict)]
    for section in data.get("sections", []):
        if isinstance(section, dict):
            titles += [i.get("title", "") for i in section.get("items", []) if isinstance(i, dict)]
    with open(HISTORY_FILE, "w") as f:
        json.dump({"date": date_str, "titles": [t for t in titles if t]}, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_system_prompt(today: str, week_ago: str, two_weeks_ago: str, previous_titles: list[str]) -> str:
    if previous_titles:
        previous = "\n".join(f"- {t}" for t in previous_titles)
        history = f"""
The previous issue already covered these stories:
{previous}
Don't repeat them. The one exception: a story that got only a short mention last
time may come back as a deep dive if it's among the most significant developments,
in which case lead with what's new since.
"""
    else:
        history = ""

    return f"""You write "The AI Weekly", a newsletter for technical readers: AI engineers who
build agents and products on top of models, several of whom also train or fine-tune
their own. It's shared with a group of colleagues and friends, so write for that
group; don't address a single reader or assume one person's projects.

Today's date: {today}. Cover mainly {week_ago} to {today}. A story from as far back as
{two_weeks_ago} still qualifies if the previous issue didn't cover it and it matters;
new developments often get proper coverage days after release.
Your training data is older than this week's news, so find what's new by searching;
don't rely on memory for which models or companies are current.

## What this newsletter is for

Readers can get the headline model launches anywhere. What they want from this
newsletter is the week's genuinely new things, explained well enough to understand
how they work and what they unlock: a new kind of model or architecture, a capability
that wasn't possible before, a technique others can reproduce, an AI system producing
a real scientific result, a shift in what's cheap or feasible to build.

Apply this test to every candidate: what can someone do or understand now that they
couldn't last week? "Slightly higher benchmark scores", "company raised money" and
"company acquired startup" usually fail it. Such stories belong in only if they change
the landscape (a large price step-change, frontier-class open weights, a lab exiting
a market).

These stories often come from outside the big labs: startups launching a new type of
model, university and independent research groups, open-source releases on Hugging
Face, AI-for-science results. They surface in outlets like Bloomberg, The Information,
TechCrunch, VentureBeat and Hacker News, on company and lab research blogs, on the
Hugging Face hub and papers pages, and on arXiv. Search these deliberately, with
queries aimed at novelty (new model types, new approaches, alternatives to LLMs,
discoveries made with AI), not only at lab names.

Also check whether the major labs (Anthropic, OpenAI, Google DeepMind, Meta, Mistral,
xAI, DeepSeek, Alibaba Qwen and other major Chinese labs) shipped, withdrew or repriced
a model in the covered period. Those go in a compact frontier roundup, unless a release
contains something genuinely new, in which case it can be a deep dive.
{history}
## Research

Search broadly first, then use web_fetch to read the primary source for every deep
dive (the paper, lab blog post, model card, or repo) and for short items where the
search snippet leaves the substance unclear. Link to primary sources; use a news
article or aggregator only when there's no primary source. Treat company claims as
claims: say when benchmarks are self-reported, when results depend on fine-tuning,
or when access is limited.

## Output

When research is done, call submit_newsletter once:
- The tone is informative and analytical, like a good technical trade publication:
  report what happened and explain how it works and why it's significant. Don't
  give advice, how-to steps or product recommendations, and don't address the
  reader directly ("you can now...").
- deep_dives: the 1-3 most genuinely new developments, each explained with real
  technical substance (how it works, key numbers, why it's significant, caveats).
  Aim for 250-450 words per deep dive.
- sections: 2-4 sections of shorter items. Suggested sections:
  🚀 Frontier Roundup · 🔬 Research & Techniques · 🛠️ Open Models & Tools · 💡 Worth Knowing
  Give each item a why_it_matters line when there's something concrete to say.
- The sections are printed first and the deep dives at the end, so readers scan
  the news before reading further. Give each deep-dive story a short item in the
  fitting section too, ending its summary with "(Deep dive below.)", so the most
  important news is visible at the top.
- Be specific: version numbers, parameter counts, prices, dates, names."""


def gather_ai_news(previous_titles: list[str]) -> dict:
    """Research the week with Claude + web tools; return structured newsletter data."""
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    now = datetime.now()
    today = now.strftime("%B %d, %Y")
    week_ago = (now - timedelta(days=7)).strftime("%B %d, %Y")
    two_weeks_ago = (now - timedelta(days=14)).strftime("%B %d, %Y")

    # Every search result and fetched page is re-read on each later step of the
    # agent loop, so these limits are the main cost lever (~$17/run at 30/15/12k on Opus).
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 15},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 6, "max_content_tokens": 5000},
        NEWSLETTER_TOOL,
    ]
    messages = [
        {
            "role": "user",
            "content": (
                f"Research what was genuinely new in AI from {week_ago} to {today}, "
                "read the primary sources for the strongest candidates, then call "
                "submit_newsletter."
            ),
        }
    ]
    system = build_system_prompt(today, week_ago, two_weeks_ago, previous_titles)

    for _ in range(MAX_CONTINUATIONS):
        with client.messages.stream(
            model=MODEL,
            max_tokens=64000,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            tools=tools,
            system=system,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        usage = response.usage
        searches = getattr(getattr(usage, "server_tool_use", None), "web_search_requests", None)
        print(
            f"   stop_reason={response.stop_reason} input={usage.input_tokens} "
            f"output={usage.output_tokens} web_searches={searches}"
        )

        if response.stop_reason == "refusal":
            raise RuntimeError(f"Request declined: {response.stop_details}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Hit max_tokens before the newsletter was submitted.")

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_newsletter":
                data = block.input
                if not isinstance(data, dict) or not isinstance(data.get("sections"), list):
                    raise RuntimeError(f"submit_newsletter input is malformed: {data!r:.500}")
                return data

        if response.stop_reason != "pause_turn":
            break
        # Server-side tool loop paused; resend so the server resumes where it left off.
        messages = messages[:1] + [{"role": "assistant", "content": response.content}]

    raise RuntimeError(
        f"Model did not call submit_newsletter. stop_reason={response.stop_reason}. "
        "Check ANTHROPIC_API_KEY or rerun."
    )


def send_newsletter(html_content: str, subject: str):
    """Send the newsletter via Gmail SMTP."""
    sender_email = os.environ["GMAIL_ADDRESS"]
    recipient_email = os.environ.get("RECIPIENT_EMAIL", sender_email)
    bcc_emails = [e.strip() for e in os.environ.get("BCC_EMAILS", "").split(",") if e.strip()]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI Newsletter Agent <{sender_email}>"
    msg["To"] = recipient_email

    # Attach HTML version
    msg.attach(MIMEText(html_content, "html"))

    all_recipients = [recipient_email] + bcc_emails
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg, to_addrs=all_recipients)

    print(f"✅ Newsletter sent to {recipient_email}" + (f"\n   BCC ({len(bcc_emails)}): {', '.join(bcc_emails)}" if bcc_emails else ""))


def main():
    dry_run = "--dry-run" in sys.argv

    previous_titles = load_previous_titles()
    print(f"🔍 Researching AI news with Claude ({len(previous_titles)} titles from last issue to skip)...")
    newsletter_data = gather_ai_news(previous_titles)

    today = datetime.now().strftime("%B %d, %Y")
    week_num = datetime.now().isocalendar()[1]

    subject = f"The AI Weekly · Issue {week_num:02d} · {today}"
    html = render_newsletter(newsletter_data, today, week_num)

    # Save a local copy
    with open("latest_newsletter.html", "w") as f:
        f.write(html)
    with open("latest_newsletter.json", "w") as f:
        json.dump(newsletter_data, f, indent=2, ensure_ascii=False)
    print("💾 Saved local copy to latest_newsletter.html")

    if dry_run:
        print("🧪 Dry run: not sending, not updating issue history.")
        return

    # Send via email
    send_newsletter(html, subject)
    save_issue_history(newsletter_data, today)


if __name__ == "__main__":
    main()
