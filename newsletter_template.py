"""
Newsletter HTML template.
Renders structured newsletter data into an email-safe HTML document.
Design: editorial / print-inspired (serif headings, warm palette, sienna accent).
"""

from html import escape


INK = "#1a1a1a"
BODY = "#2d2d2d"
MUTED = "#6b6b6b"
BG = "#faf6f0"
CARD = "#ffffff"
ACCENT = "#14366e"
RULE = "#e8e2d5"
ITEM_RULE = "#f0ebe0"

SERIF = "Georgia, 'Times New Roman', Times, serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def render_newsletter(data: dict, date_str: str, week_num: int) -> str:
    """Render newsletter data into an email-compatible HTML document."""

    sections_html = ""
    idx = 0
    for section in data.get("sections", []):
        # Guard against malformed model output (e.g. a section returned as a
        # plain string instead of an object) so one bad item can't crash the send.
        if not isinstance(section, dict):
            continue

        items_html = ""
        for item in section.get("items", []):
            if not isinstance(item, dict):
                continue
            title = escape(item.get("title", ""))
            summary = escape(item.get("summary", ""))

            link_html = ""
            link = item.get("link", "")
            if link and link.startswith("http"):
                link_html = (
                    f' <a href="{escape(link, quote=True)}" '
                    f'style="color: {ACCENT}; text-decoration: none; '
                    f'font-weight: 600; white-space: nowrap;">Read &rarr;</a>'
                )

            items_html += f"""
            <tr>
                <td style="padding: 18px 0; border-bottom: 1px solid {ITEM_RULE};">
                    <p style="margin: 0 0 6px 0; font-family: {SANS}; font-weight: 600; color: {INK}; font-size: 16px; line-height: 1.35;">
                        {title}
                    </p>
                    <p style="margin: 0; font-family: {SANS}; color: {BODY}; font-size: 14.5px; line-height: 1.6;">
                        {summary}{link_html}
                    </p>
                </td>
            </tr>"""

        # Skip a section that has no valid items after filtering.
        if not items_html:
            continue

        idx += 1
        section_num = f"{idx:02d}"
        emoji = escape(section.get("emoji", ""))
        sec_title = escape(section.get("title", ""))

        sections_html += f"""
        <tr>
            <td style="padding: 36px 0 6px 0;">
                <p style="margin: 0 0 8px 0; font-family: {SANS}; color: {ACCENT}; font-size: 11px; font-weight: 700; letter-spacing: 1.8px; text-transform: uppercase;">
                    Section {section_num}
                </p>
                <h2 style="margin: 0; font-family: {SERIF}; font-size: 22px; color: {INK}; font-weight: 700; line-height: 1.25;">
                    {emoji} {sec_title}
                </h2>
            </td>
        </tr>
        {items_html}"""

    one_liner = escape(data.get("one_liner", "Another week, another breakthrough."))
    issue_label = f"Issue {week_num:02d} &middot; {escape(date_str)}"

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The AI Weekly &middot; Issue {week_num:02d}</title>
</head>
<body style="margin: 0; padding: 0; background-color: {BG}; font-family: {SANS}; -webkit-font-smoothing: antialiased;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: {BG}; padding: 40px 16px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%; background-color: {CARD}; border: 1px solid {RULE};">

                    <!-- Masthead -->
                    <tr>
                        <td style="padding: 44px 40px 28px 40px;">
                            <p style="margin: 0 0 12px 0; font-family: {SANS}; color: {ACCENT}; font-size: 11px; font-weight: 700; letter-spacing: 2.4px; text-transform: uppercase;">
                                {issue_label}
                            </p>
                            <h1 style="margin: 0; font-family: {SERIF}; color: {INK}; font-size: 38px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.1;">
                                The AI Weekly
                            </h1>
                        </td>
                    </tr>

                    <!-- Pull quote -->
                    <tr>
                        <td style="padding: 4px 40px 32px 40px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="border-left: 3px solid {ACCENT}; padding: 4px 0 4px 18px;">
                                        <p style="margin: 0; font-family: {SERIF}; color: {INK}; font-size: 17px; font-style: italic; line-height: 1.5;">
                                            {one_liner}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Top rule -->
                    <tr>
                        <td style="padding: 0 40px;">
                            <div style="height: 1px; background-color: {RULE}; line-height: 1px; font-size: 1px;">&nbsp;</div>
                        </td>
                    </tr>

                    <!-- Sections -->
                    <tr>
                        <td style="padding: 4px 40px 40px 40px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                {sections_html}
                            </table>
                        </td>
                    </tr>

                    <!-- Bottom rule -->
                    <tr>
                        <td style="padding: 0 40px;">
                            <div style="height: 1px; background-color: {RULE}; line-height: 1px; font-size: 1px;">&nbsp;</div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 28px 40px 40px 40px; text-align: center;">
                            <p style="margin: 0 0 6px 0; font-family: {SANS}; color: {INK}; font-size: 13px; font-weight: 600; letter-spacing: 0.2px;">
                                Created by Jasper Valk
                            </p>
                            <p style="margin: 0; font-family: {SANS}; color: {MUTED}; font-size: 12px; line-height: 1.5;">
                                Curated weekly with Claude.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
