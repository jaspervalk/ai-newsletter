"""
Newsletter HTML template.
Renders the structured newsletter data into a clean, email-compatible HTML format.
"""


def render_newsletter(data: dict, date_str: str, week_num: int) -> str:
    """Render newsletter data into HTML email."""

    sections_html = ""
    for section in data.get("sections", []):
        items_html = ""
        for item in section.get("items", []):
            link_html = ""
            if item.get("link") and item["link"].startswith("http"):
                link_html = f' <a href="{item["link"]}" style="color: #6366f1; text-decoration: none; font-size: 13px;">Read more →</a>'

            items_html += f"""
            <tr>
                <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9;">
                    <p style="margin: 0 0 4px 0; font-weight: 600; color: #1e293b; font-size: 15px;">
                        {item.get("title", "")}
                    </p>
                    <p style="margin: 0; color: #475569; font-size: 14px; line-height: 1.5;">
                        {item.get("summary", "")}{link_html}
                    </p>
                </td>
            </tr>"""

        sections_html += f"""
        <tr>
            <td style="padding: 24px 0 8px 0;">
                <h2 style="margin: 0; font-size: 18px; color: #1e293b; font-weight: 700;">
                    {section.get("emoji", "")} {section.get("title", "")}
                </h2>
            </td>
        </tr>
        {items_html}"""

    one_liner = data.get("one_liner", "Another week, another breakthrough.")

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 24px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%;">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 32px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="margin: 0 0 8px 0; color: white; font-size: 26px; font-weight: 800;">
                                🤖 Weekly AI Newsletter
                            </h1>
                            <p style="margin: 0; color: rgba(255,255,255,0.85); font-size: 14px;">
                                Week {week_num} · {date_str}
                            </p>
                        </td>
                    </tr>

                    <!-- One-liner -->
                    <tr>
                        <td style="background-color: #eef2ff; padding: 16px 32px; border-bottom: 1px solid #e0e7ff;">
                            <p style="margin: 0; color: #4338ca; font-size: 14px; font-style: italic; text-align: center;">
                                "{one_liner}"
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 8px 32px 32px 32px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                {sections_html}
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f1f5f9; padding: 24px 32px; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="margin: 0 0 8px 0; color: #64748b; font-size: 13px;">
                                Curated by Claude · Powered by Anthropic API + Web Search
                            </p>
                            <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                                This newsletter is auto-generated weekly using AI.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
