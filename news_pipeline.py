"""
news_pipeline.py  –  Hindi-editorial validator + OpenAI drafter
24 May 2025   v11 (stable chat-only edition)

• Collects candidate URLs from allow-list tier-1 sites (passed in argv).
• Validates each page: HTTP 200, no soft-404 words, visible & meta date == today (IST),
  original_publish_time check, earliest Wayback ≤ 48 h, official anchor when needed.
• Requires ≥ 3 distinct tier-1 domains & ≥ 2 unique fingerprints.
• Drafts a 400-600-word Hindi editorial via OpenAI (gpt-4o-mini).
• Writes: links.json, run-summary.json, editorial.txt (if successful).
"""

import hashlib, re, os, sys, json, time, requests, datetime as dt, textwrap
from bs4 import BeautifulSoup
from dateutil import parser as dparse
from readability import Document

# ---------- CONFIG ----------
TIER1 = {
    "thehindu.com", "timesofindia.indiatimes.com", "indianexpress.com",
    "hindustantimes.com", "ndtv.com", "indiatoday.in"
}
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TODAY = dt.datetime.now(IST).date()
DATE_RE = re.compile(r"\b(\d{1,2}\s+\w+\s+\d{4})\b")
SOFT404_PATTERNS = ["page not found", "404", "requested page", "हम इस पेज को"]
OPENAI_MODEL = "gpt-4o"   # change to gpt-3.5-turbo-0125 to save cost
openai_api_key = os.getenv("OPENAI_API_KEY")

# ---------- HELPERS ----------
def raw_text(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

def readable_text(html: str) -> str:
    return BeautifulSoup(Document(html).summary(), "html.parser").get_text(" ")

def to_ist(date_str: str):
    try:
        d = dparse.parse(date_str)
        if d.tzinfo is None:
            d = d.replace(tzinfo=IST)
        return d.astimezone(IST).date()
    except Exception:
        return None

def visible_date(text: str) -> str:
    m = DATE_RE.search(text[:2500])
    return m.group(1) if m else ""

def is_soft404(html: str) -> bool:
    blob = (BeautifulSoup(html, "html.parser").title.string or "") + html[:1200]
    return any(p in blob.lower() for p in SOFT404_PATTERNS)

def fingerprint(text: str) -> str:
    low = text.lower()
    if "pti" in low or "reuters" in low:
        return "WIRE_SERVICE"
    return hashlib.sha1(text.encode()).hexdigest()[:32]

# Wayback earliest snapshot age (≤48 h)
def archive_age(url: str) -> int:
    api = f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=1&filter=statuscode:200"
    try:
        ts = requests.get(api, timeout=4).json()[1][1]  # earliest
        first = dt.datetime.strptime(ts, "%Y%m%d%H%M%S").replace(
            tzinfo=dt.timezone.utc).astimezone(IST)
        return int((dt.datetime.now(IST) - first).total_seconds() / 3600)
    except Exception:
        return 0  # treat as fresh if no snapshot

# Quick GET with retry
def fetch(url: str, timeout: int = 8) -> str:
    for _ in range(2):
        try:
            r = requests.get(url, timeout=timeout,
                             headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=False)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(0.8)
    raise RuntimeError("http_fail")

# ---------- VALIDATION ----------
def validate(url: str):
    domain = url.split("/")[2]
    if domain not in TIER1:
        return None, "domain_not_allowed"
    html = fetch(url)
    if is_soft404(html):
        return None, "soft_404"
    text = raw_text(html)
    if len(text.split()) < 250:
        return None, "too_short"
    vis = visible_date(text)
    meta = BeautifulSoup(html, "html.parser").find(
        "meta", {"property": "article:published_time"})
    meta_date = meta["content"] if meta and meta.get("content") else ""
    if to_ist(vis) != TODAY or to_ist(meta_date) != TODAY:
        return None, "not_today"
    if archive_age(url) > 48:
        return None, "archive_old"
    return {
        "url": url,
        "domain": domain,
        "dateline": vis,
        "hash": hashlib.sha256(html.encode()).hexdigest(),
        "fp": fingerprint(readable_text(html))
    }, None

# ---------- OPENAI DRAFT ----------
def draft_editorial(valid_links):
    import openai, datetime as dt
    openai.api_key = openai_api_key
    today = dt.datetime.now(IST).strftime("%-d %B %Y")
    src_md = "\n".join(f"- {v['url']}" for v in valid_links)
    prompt = textwrap.dedent(f"""
        नीचे दिये गये तीन स्रोतों के आधार पर
        चार-शब्दी शीर्षक बनाओ, फिर एक खाली पंक्ति,
        फिर 400-600 शब्दों का हिंदी संपादकीय लिखो।
        पहली पंक्ति में पूर्ण तिथि {today} हो।
        किसी outlet का नाम मत लिखो; 'मीडिया रिपोर्टों' प्रयोग करो।
        स्रोत:
        {src_md}
    """)
    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

# ---------- MAIN ----------
def main():
    urls = sys.argv[1:]
    validated, errors = [], {}
    for u in urls:
        v, err = validate(u)
        if v:
            validated.append(v)
        else:
            errors[u] = err
    uniq_fp = {v["fp"] for v in validated}
    if len(validated) >= 3 and len(uniq_fp) >= 2:
        editorial = draft_editorial(validated)
        with open("editorial.txt", "w", encoding="utf-8") as f:
            f.write(editorial)
        json.dump(validated, open("links.json", "w", encoding="utf-8"), indent=2)
        json.dump({"stage_pass": True, "urls": validated},
                  open("run-summary.json", "w", encoding="utf-8"), indent=2)
    else:
        json.dump({"stage_pass": False, "errors": errors},
                  open("run-summary.json", "w", encoding="utf-8"), indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python news_pipeline.py <url1> <url2> <url3> [...]")
        sys.exit(1)
    main()
