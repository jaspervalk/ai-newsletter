"""
AI Newsletter Agent
Uses Claude API with web_search to find the latest AI news,
then sends a formatted newsletter to your Gmail.
"""

import anthropic
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from newsletter_template import render_newsletter


NEWSLETTER_TOOL = {
    "name": "submit_newsletter",
    "description": "Submit the final curated weekly AI newsletter. Call this exactly once after web searches are complete.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sections": {
                "type": "array",
                "description": "Newsletter sections (typically 3-5). Only include sections that have news.",
                "items": {
                    "type": "object",
                    "properties": {
                        "emoji": {"type": "string"},
                        "title": {"type": "string"},
                        "items": {
                            "type": "array",
                            "description": "2-4 news items.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "summary": {"type": "string", "description": "2-3 sentence summary with specific details."},
                                    "link": {"type": "string"},
                                },
                                "required": ["title", "summary", "link"],
                            },
                        },
                    },
                    "required": ["emoji", "title", "items"],
                },
            },
            "one_liner": {"type": "string", "description": "A single witty one-liner summarizing this week in AI."},
        },
        "required": ["sections", "one_liner"],
    },
}


def gather_ai_news() -> dict:
    """Use Claude with web search to find AI news; return structured newsletter data."""
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    today = datetime.now().strftime("%B %d, %Y")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%B %d, %Y")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            },
            NEWSLETTER_TOOL,
        ],
        system=f"""You are an AI news curator writing a weekly newsletter for an AI Engineer & Data Scientist.
Today's date: {today}. Cover the period from {week_ago} to {today}.

Your job:
1. Search for the most important AI developments from the past 7 days
2. Focus on: new model releases, research breakthroughs, open-source tools,
   frameworks, practical engineering insights, and industry moves
3. After your searches, call the submit_newsletter tool with the final newsletter content

Search multiple queries to get broad coverage:
- New AI model releases and benchmarks
- AI research papers and breakthroughs
- AI tools, frameworks, and open-source releases
- Major AI industry news and company announcements

Be specific with version numbers, model names, and concrete details. Include links where available.
Suggested sections (only include those that have news):
🚀 New Models & Releases · 🔬 Research & Breakthroughs · 🛠️ Tools & Frameworks · 💼 Industry & Business · 💡 Worth Reading""",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Find the most important AI news from {week_ago} to {today}, "
                    "then call submit_newsletter with 2-4 items per section."
                ),
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_newsletter":
            return block.input

    raise RuntimeError(
        f"Model did not call submit_newsletter. stop_reason={response.stop_reason}. "
        "Check ANTHROPIC_API_KEY, max_tokens, or rerun."
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
    print("🔍 Gathering AI news with Claude + web search...")
    newsletter_data = gather_ai_news()

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
