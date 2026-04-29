"""
AI Newsletter Agent
Uses Claude API with web_search to find the latest AI news,
then sends a formatted newsletter to your Gmail.
"""

import anthropic
import smtplib
import os
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from newsletter_template import render_newsletter


def gather_ai_news() -> str:
    """Use Claude with web search to find and summarize the latest AI news."""
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    today = datetime.now().strftime("%B %d, %Y")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%B %d, %Y")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            }
        ],
        system=f"""You are an AI news curator writing a weekly newsletter for an AI Engineer & Data Scientist.
Today's date: {today}. Cover the period from {week_ago} to {today}.

Your job:
1. Search for the most important AI developments from the past 7 days
2. Focus on: new model releases, research breakthroughs, open-source tools,
   frameworks, practical engineering insights, and industry moves
3. Write the newsletter content in the exact JSON format specified

Search multiple queries to get broad coverage:
- New AI model releases and benchmarks
- AI research papers and breakthroughs
- AI tools, frameworks, and open-source releases
- Major AI industry news and company announcements

Be specific with version numbers, model names, and concrete details.
Include links where available.""",
        messages=[
            {
                "role": "user",
                "content": f"""Find the most important AI news from {week_ago} to {today}.

Respond ONLY with a JSON object (no markdown, no backticks) in this exact format:
{{
    "sections": [
        {{
            "emoji": "🚀",
            "title": "New Models & Releases",
            "items": [
                {{
                    "title": "Item title",
                    "summary": "2-3 sentence summary with specific details.",
                    "link": "https://..."
                }}
            ]
        }},
        {{
            "emoji": "🔬",
            "title": "Research & Breakthroughs",
            "items": [...]
        }},
        {{
            "emoji": "🛠️",
            "title": "Tools & Frameworks",
            "items": [...]
        }},
        {{
            "emoji": "💼",
            "title": "Industry & Business",
            "items": [...]
        }},
        {{
            "emoji": "💡",
            "title": "Worth Reading",
            "items": [...]
        }}
    ],
    "one_liner": "A single witty one-liner summarizing this week in AI"
}}

Include 2-4 items per section. Only include sections that have news.""",
            }
        ],
    )

    # Extract the text content from the response
    text_parts = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)

    full_text = "\n".join(text_parts)

    # Clean up and parse the JSON
    full_text = full_text.strip()
    if full_text.startswith("```"):
        full_text = full_text.split("\n", 1)[1]  # Remove first line
        full_text = full_text.rsplit("```", 1)[0]  # Remove last backticks

    return full_text


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

    print(f"✅ Newsletter sent to {recipient_email}" + (f" (+ {len(bcc_emails)} on BCC)" if bcc_emails else ""))


def main():
    print("🔍 Gathering AI news with Claude + web search...")
    raw_json = gather_ai_news()

    try:
        newsletter_data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse JSON, attempting to extract...")
        # Try to find JSON in the text
        import re
        match = re.search(r'\{[\s\S]*\}', raw_json)
        if match:
            newsletter_data = json.loads(match.group())
        else:
            print(f"❌ Could not parse newsletter data: {e}")
            print(f"Raw output:\n{raw_json[:500]}")
            return

    today = datetime.now().strftime("%B %d, %Y")
    week_num = datetime.now().isocalendar()[1]

    subject = f"🤖 Weekly AI Newsletter — Week {week_num} ({today})"
    html = render_newsletter(newsletter_data, today, week_num)

    # Save a local copy
    with open("latest_newsletter.html", "w") as f:
        f.write(html)
    print("💾 Saved local copy to latest_newsletter.html")

    # Send via email
    send_newsletter(html, subject)


if __name__ == "__main__":
    main()
