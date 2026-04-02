#!/usr/bin/env python3
"""
Energy Intelligence Weekly — Automated Newsletter
Process Engineering Consultancy Edition
Focus: O&G Upstream/Downstream · Hydrogen · CO2 · Circularity

Schedule: Every Monday 07:00 Paris time via GitHub Actions
Requirements: pip install anthropic sendgrid python-dotenv
"""

import os, json, datetime, re
from dotenv import load_dotenv
import anthropic
from json_repair import repair_json
load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
COMPANY_NAME      = os.environ.get("COMPANY_NAME", "Energy Consultancy")
EDITOR_NOTES      = os.environ.get("EDITOR_NOTES", "")
MAX_COMPANIES     = int(os.environ.get("MAX_COMPANIES", "9"))
# ─────────────────────────────────────────────────────────────────────────────


def build_prompt(today: str) -> str:
    return f"""You are an editor for a Paris-based process engineering consultancy's weekly newsletter.
Markets: O&G upstream/downstream, green/blue hydrogen, CO2 capture/transport, circularity (waste-to-chemicals).
Services: technical due diligence, feasibility, conceptual, pre-FEED, FEED engineering.
Today: {today}. Search for real news from the past 7 days.

Return ONLY valid JSON, no markdown, no extra text, starting with {{ and ending with }}:

{{
  "weekOf": "{today}",
  "headline": "8-12 word headline for process engineers",
  "executiveSummary": "3 sentences: what happened, strategic implication for a Paris process engineering consultancy.",
  "stats": [
    {{"value": "...", "label": "...", "theme": "og|h2|co2|circ", "context": "one sentence"}}
  ],
  "ogNews": [
    {{"subcat": "Upstream|Downstream|Refining|Petrochemicals", "headline": "...", "body": "2 sentences", "consultancyAngle": "specific service entry point", "serviceTag": "Due Diligence|Feasibility|Conceptual|Pre-FEED|FEED|Tech Review", "source": "name · date"}}
  ],
  "neNews": [
    {{"subcat": "Green H2|Blue H2|CO2 Capture|CO2 Transport|CCS", "headline": "...", "body": "2 sentences", "consultancyAngle": "...", "serviceTag": "Due Diligence|Feasibility|Conceptual|Pre-FEED|FEED|Tech Review", "source": "..."}}
  ],
  "franceNews": [
    {{"subcat": "Hydrogen|CO2|Circularity|Refining|Policy", "headline": "...", "body": "2 sentences", "consultancyAngle": "...", "serviceTag": "Due Diligence|Feasibility|Conceptual|Pre-FEED|FEED|Tech Review", "source": "..."}}
  ],
  "policyRadar": [
    {{"region": "EU|France|Global", "headline": "...", "body": "2 sentences", "impact": "direct impact on project pipeline", "source": "..."}}
  ],
  "bdTargets": [
    {{"name": "...", "market": "O&G|Hydrogen|CO2|Circularity|Process", "country": "...", "projectPhase": "Conceptual|Feasibility|Pre-FEED|FEED|Due Diligence|Tech Review", "why": "2 sentences: what happened and why it creates a consulting opportunity", "entryPoint": "specific service", "interestLevel": "High|Medium", "projectType": "FEED launch|Funding round|Tender win|Asset acquisition|Feasibility commissioned|Grant awarded"}}
  ],
  "tendersToWatch": [
    {{"title": "...", "body": "1 sentence", "deadline": "...", "source": "..."}}
  ]
}}

Include exactly: 2 ogNews, 2 neNews, 2 franceNews, 2 policyRadar, {MAX_COMPANIES} bdTargets, 2 tendersToWatch.
Use real companies and real news. Be specific with numbers."""

def generate_newsletter() -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.date.today().strftime("%-d %B %Y")
    print(f"Generating newsletter for {today}…")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{"role": "user", "content": build_prompt(today)}],
    )

    raw = re.sub(r"```json|```", "", "".join(b.text for b in response.content if b.type == "text")).strip()

    if "{" not in raw or "}" not in raw:
        print("No JSON found, retrying...")
        import time
        time.sleep(90)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": build_prompt(today)}],
        )
        raw = re.sub(r"```json|```", "", "".join(b.text for b in response.content if b.type == "text")).strip()

    j0, j1 = raw.index("{"), raw.rindex("}")
    clean = raw[j0:j1+1]

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        print("Attempting JSON repair...")
        repaired = repair_json(clean)
        data = json.loads(repaired)
        print("JSON repaired successfully.")

    print(f"Generated — {len(data.get('bdTargets',[]))} BD targets, "
          f"{len(data.get('ogNews',[]))+len(data.get('neNews',[]))+len(data.get('franceNews',[]))} news items.")
    return data


# ── HTML BUILDER ──────────────────────────────────────────────────────────────

STAT_COLORS = {
    "og":   ("#FEF3C7", "#D97706", "#92400E"),
    "h2":   ("#F0FAF5", "#00875A", "#005A3C"),
    "co2":  ("#E6F1FB", "#185FA5", "#0C447C"),
    "circ": ("#F3E8FF", "#7C3AED", "#6B21A8"),
}

SERVICE_COLORS = {
    "Due Diligence": ("#EDE9FE", "#4C1D95"),
    "Feasibility":   ("#E6F5EF", "#005A3C"),
    "Conceptual":    ("#FEF3C7", "#92400E"),
    "Pre-FEED":      ("#E6F1FB", "#0C447C"),
    "FEED":          ("#0D1117", "#FFFFFF"),
    "Tech Review":   ("#F3F4F6", "#374151"),
}

MARKET_COLORS = {
    "O&G":        ("#FEF3C7", "#92400E"),
    "Hydrogen":   ("#E6F5EF", "#005A3C"),
    "CO2":        ("#E6F1FB", "#0C447C"),
    "Circularity":("#F3E8FF", "#6B21A8"),
    "Process":    ("#F0F9FF", "#075985"),
}

def stat_card(s):
    bg, border, text = STAT_COLORS.get(s.get("theme","og"), STAT_COLORS["og"])
    return f"""
    <td style="width:33%;vertical-align:top;padding:0 4px;">
      <div style="background:{bg};border-left:3px solid {border};padding:12px 14px;border-radius:0 4px 4px 0;">
        <p style="font-size:20px;font-weight:600;color:{text};margin:0;">{s['value']}</p>
        <p style="font-size:10px;color:{text};line-height:1.5;margin:4px 0 0;font-weight:500;">{s['label']}</p>
        <p style="font-size:10px;color:{text};opacity:0.7;line-height:1.5;margin:3px 0 0;">{s.get('context','')}</p>
      </div>
    </td>"""

def svc_badge(tag):
    bg, fg = SERVICE_COLORS.get(tag, ("#F3F4F6","#374151"))
    return f'<span style="display:inline-block;font-size:8px;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;padding:2px 6px;border-radius:3px;background:{bg};color:{fg};margin-left:6px;vertical-align:middle;">{tag}</span>'

def news_row(item, fr=False):
    cat = item.get('subcat','') + (' · France' if fr else '')
    angle_color = "#005A3C"; angle_bg = "#F0FAF5"
    return f"""
    <div style="padding:12px 0;border-bottom:1px solid #F3F4F6;">
      <p style="font-size:9px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#9CA3AF;margin:0 0 3px;">{cat}</p>
      <p style="font-size:13px;font-weight:600;color:#0D1117;margin:0 0 5px;line-height:1.4;">
        {item['headline']}{svc_badge(item.get('serviceTag',''))}
      </p>
      <p style="font-size:11px;color:#4B5563;line-height:1.7;margin:0;">{item['body']}</p>
      <p style="display:inline-block;margin-top:7px;font-size:10px;color:{angle_color};background:{angle_bg};padding:3px 8px;border-radius:3px;">
        {item.get('consultancyAngle','')}
      </p>
      <p style="font-size:9px;color:#9CA3AF;margin:5px 0 0;">{item.get('source','')}</p>
    </div>"""

def policy_row(item):
    region_colors = {"EU":"#E8EDFF,#003189","France":"#E8EDFF,#003189","Global":"#F3F4F6,#374151"}
    rb, rf = region_colors.get(item.get('region','Global'),"#F3F4F6,#374151").split(",")
    return f"""
    <div style="padding:12px 0;border-bottom:1px solid #F3F4F6;">
      <span style="font-size:8px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;padding:2px 6px;border-radius:3px;background:{rb};color:{rf};">{item.get('region','')}</span>
      <p style="font-size:13px;font-weight:600;color:#0D1117;margin:7px 0 5px;line-height:1.4;">{item['headline']}</p>
      <p style="font-size:11px;color:#4B5563;line-height:1.7;margin:0;">{item['body']}</p>
      <p style="font-size:10px;color:#92400E;background:#FEF3C7;padding:3px 8px;border-radius:3px;display:inline-block;margin-top:7px;">{item.get('impact','')}</p>
      <p style="font-size:9px;color:#9CA3AF;margin:5px 0 0;">{item.get('source','')}</p>
    </div>"""

def bd_card(c):
    mbg, mfg = MARKET_COLORS.get(c.get('market','Process'), ("#F3F4F6","#374151"))
    sbg, sfg = SERVICE_COLORS.get(c.get('projectPhase','Feasibility'), ("#F3F4F6","#374151"))
    border = "1.5px solid #00875A" if c.get('interestLevel') == 'High' else "1px solid #E5E7EB"
    high_badge = '<span style="font-size:9px;padding:2px 6px;border-radius:99px;background:#0D1117;color:#fff;margin-left:4px;">High</span>' if c.get('interestLevel') == 'High' else ''
    return f"""
    <td style="width:50%;vertical-align:top;padding:4px;">
      <div style="border:{border};border-radius:5px;padding:11px 13px;">
        <p style="font-size:12px;font-weight:600;color:#0D1117;margin:0;">{c['name']}</p>
        <p style="font-size:9px;color:#9CA3AF;margin:2px 0 7px;">{c.get('country','')} · {c.get('projectType','')}</p>
        <p style="font-size:10px;color:#4B5563;line-height:1.65;margin:0;">{c['why']}</p>
        <p style="font-size:10px;color:#005A3C;font-weight:600;margin:5px 0 0;">{c.get('entryPoint','')}</p>
        <div style="margin-top:7px;">
          <span style="font-size:9px;padding:2px 6px;border-radius:99px;background:{mbg};color:{mfg};">{c.get('market','')}</span>
          <span style="font-size:9px;padding:2px 6px;border-radius:3px;background:{sbg};color:{sfg};margin-left:4px;">{c.get('projectPhase','')}</span>
          {high_badge}
        </div>
      </div>
    </td>"""

def tender_row(t):
    return f"""
    <div style="display:flex;gap:12px;padding:11px 0;border-bottom:1px solid #F3F4F6;">
      <div style="width:7px;height:7px;border-radius:50%;background:#00875A;margin-top:4px;flex-shrink:0;"></div>
      <div>
        <p style="font-size:12px;font-weight:600;color:#0D1117;margin:0 0 3px;">{t['title']}</p>
        <p style="font-size:10px;color:#4B5563;line-height:1.6;margin:0;">{t['body']}</p>
        <p style="font-size:9px;color:#D97706;font-weight:600;margin:3px 0 0;">{t.get('deadline','')} · {t.get('source','')}</p>
      </div>
    </div>"""

def section_head(icon, label, icon_bg, icon_fg):
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:26px 0 12px;">
      <tr>
        <td style="width:22px;vertical-align:middle;">
          <div style="width:20px;height:20px;border-radius:3px;background:{icon_bg};display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:{icon_fg};text-align:center;line-height:20px;">{icon}</div>
        </td>
        <td style="width:10px;"></td>
        <td style="vertical-align:middle;">
          <p style="font-size:9px;font-weight:600;letter-spacing:0.13em;text-transform:uppercase;color:#9CA3AF;margin:0;">{label}</p>
        </td>
        <td style="padding-left:10px;vertical-align:middle;">
          <div style="height:1px;background:#E5E7EB;"></div>
        </td>
      </tr>
    </table>"""


def build_html(nl: dict) -> str:
    today_str = nl.get("weekOf", datetime.date.today().strftime("%-d %B %Y"))

    # Stats row
    stats = nl.get("stats", [])
    stats_html = ""
    if stats:
        cells = "".join(stat_card(s) for s in stats[:3])
        stats_html = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;"><tr>{cells}</tr></table>'

    # News sections
    og_html   = "".join(news_row(n) for n in nl.get("ogNews",[]))
    ne_html   = "".join(news_row(n) for n in nl.get("neNews",[]))
    fr_html   = "".join(news_row(n, fr=True) for n in nl.get("franceNews",[]))
    pol_html  = "".join(policy_row(p) for p in nl.get("policyRadar",[]))
    tend_html = "".join(tender_row(t) for t in nl.get("tendersToWatch",[]))

    # BD targets grid
    targets = nl.get("bdTargets", [])
    bd_rows = ""
    for i in range(0, len(targets), 2):
        pair = targets[i:i+2]
        cells = "".join(bd_card(c) for c in pair)
        if len(pair) == 1:
            cells += '<td style="width:50%;"></td>'
        bd_rows += f'<tr>{cells}</tr>'
    bd_html = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{bd_rows}</table>'

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Energy Intelligence Weekly — {today_str}</title>
</head>
<body style="margin:0;padding:0;background:#E8E5E0;font-family:Georgia,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:28px 16px 40px;">
<table role="presentation" width="620" style="max-width:620px;background:#ffffff;border-radius:3px;overflow:hidden;">

  <!-- MASTHEAD -->
  <tr><td style="background:#0B1320;padding:36px 36px 28px;">
    <p style="font-size:9px;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:#3DD68C;margin:0 0 18px;">
      Energy Intelligence Weekly &nbsp;·&nbsp; {today_str}
    </p>
    <p style="font-family:Georgia,serif;font-size:26px;font-weight:400;color:#ffffff;line-height:1.25;margin:0 0 18px;letter-spacing:-0.01em;">
      {nl.get('headline','Weekly Energy Intelligence')}
    </p>
    <p style="font-size:12px;color:rgba(255,255,255,0.5);line-height:1.75;padding-top:16px;border-top:1px solid rgba(255,255,255,0.08);margin:0;">
      {nl.get('executiveSummary','')}
    </p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.07);">
      <tr>
        <td style="font-size:10px;color:rgba(255,255,255,0.28);">O&amp;G · Hydrogen · CO₂ · Circularity</td>
        <td style="font-size:10px;color:rgba(255,255,255,0.28);text-align:center;">{len(targets)} BD targets this week</td>
        <td style="font-size:10px;color:rgba(255,255,255,0.28);text-align:right;">{COMPANY_NAME} · Paris</td>
      </tr>
    </table>
  </td></tr>

  <!-- BODY -->
  <tr><td style="padding:0 36px;">

    {stats_html}

    {section_head('O&G','Oil &amp; Gas — Upstream &amp; Downstream','#FEF3C7','#92400E')}
    {og_html}

    {section_head('H₂','New Energies — Hydrogen &amp; CO₂','#E6F5EF','#005A3C')}
    {ne_html}

    {section_head('FR','France — Industrial decarbonisation','#E8EDFF','#003189')}
    {fr_html}

    {section_head('!','Policy radar — what to track','#FCE7F3','#9D174D')}
    {pol_html}

    {section_head('★','BD targets — process engineering opportunities this week','#F0FAF5','#005A3C')}
    {bd_html}

    {section_head('⏱','Tenders &amp; calls to watch','#FEF3C7','#D97706')}
    {tend_html}

    <div style="height:28px;"></div>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="background:#F9FAFB;border-top:1px solid #E5E7EB;padding:20px 36px;">
    <p style="font-size:9px;color:#9CA3AF;line-height:1.8;margin:0;">
      You are receiving Energy Intelligence Weekly from {COMPANY_NAME} · Paris.<br>
      Focus: O&amp;G · Hydrogen · CO₂ · Circularity · Process Engineering · AI-assisted research · {today_str}<br>
      <a href="{{{{unsubscribe}}}}" style="color:#9CA3AF;">Unsubscribe</a> &nbsp;·&nbsp;
      <a href="{{{{weblink}}}}" style="color:#9CA3AF;">View in browser</a>
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""


def save_output(nl: dict, html: str):
    date_slug = datetime.date.today().strftime("%Y-%m-%d")
    os.makedirs("output", exist_ok=True)
    with open(f"output/{date_slug}_newsletter.json", "w", encoding="utf-8") as f:
        json.dump(nl, f, indent=2, ensure_ascii=False)
    with open(f"output/{date_slug}_newsletter.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved → output/{date_slug}_newsletter.{{json,html}}")


def send_via_sendgrid(nl, html):
    print("Email sending disabled — newsletter published to GitHub Pages only.")

def main():
    print("=" * 60)
    print(f"  Energy Intelligence Weekly — {datetime.date.today()}")
    print(f"  Company: {COMPANY_NAME}")
    print("=" * 60)

    nl   = generate_newsletter()
    html = build_html(nl)
    save_output(nl, html)
    send_via_sendgrid(nl, html)
    print("Done.")


if __name__ == "__main__":
    main()
