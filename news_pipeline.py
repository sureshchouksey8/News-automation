#!/usr/bin/env python3
import sys
import os
import re
import requests
import datetime
import openai
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

# ====== CONFIGURABLE ======
OPENAI_MODEL   = "gpt-4o"
EDITORIAL_STYLE =  (
    "इस समाचार को पढ़कर एक लेखनी तैयार करें जो "
    "– निष्पक्ष लेकिन स्पष्ट रुख़ अपनाए, "
    "– समस्या को जागरूक कर खुले तौर पर उसका समाधान सुझाने का प्रयास करे, "
    "– कोई उपशीर्षक, ब्रेक या श्रेणियाँ न हों, केवल एक हिंदी शीर्षक, "
    "  फिर एक लाइन रिक्त छोड़ गर्भित संपादकीय जो कम से कम 600 शब्दों में हो, "
    "  ITDC News की तर्ज़ पर, तथ्यात्मक, स्पष्ट, और रचनात्मक।"
)


def fetch_article(url):
    """Fetch title, main content, and publication date (if any) from the given URL."""
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # Title
        title = soup.title.string.strip() if soup.title else "No Title"

        # Main content selectors
        main_content = ""
        for sel in [
            "article",
            'div[itemprop="articleBody"]',
            'div[class*="content"]',
            'div[class*="story"]',
            'section[class*="article"]',
            "div#content",
        ]:
            block = soup.select_one(sel)
            if block and block.get_text(strip=True):
                main_content = block.get_text(separator="\n", strip=True)
                break

        # Fallback to all <p>
        if not main_content:
            paragraphs = [
                p.get_text(strip=True)
                for p in soup.find_all("p")
                if p.get_text(strip=True)
            ]
            main_content = "\n".join(paragraphs) or "[No main content found]"

        # Try to extract a pub date from meta tags
        pub_date = None
        for meta in soup.find_all("meta"):
            for attr in ("property", "name", "itemprop"):
                val = meta.get(attr, "").lower()
                if val in (
                    "article:published_time",
                    "date",
                    "publishdate",
                    "datepublished",
                    "modified_time",
                ):
                    content = meta.get("content") or meta.get("value") or ""
                    # look for YYYY-MM-DD
                    m = re.search(r"\d{4}-\d{2}-\d{2}", content)
                    if m:
                        pub_date = m.group(0)
                        break
            if pub_date:
                break

        return {
            "url": url,
            "title": title,
            "content": main_content,
            "date": pub_date,
        }

    except Exception as e:
        return {
            "url": url,
            "title": url,
            "content": f"[ERROR fetching: {e}]",
            "date": None,
        }


def select_best_article(articles):
    """
    Pick the article with the newest valid date.
    If none have a valid date, fallback to the first in list.
    """
    dated_articles = []
    for art in articles:
        date_str = art.get("date")
        if not date_str:
            continue
        try:
            parsed = date_parser.parse(date_str)
        except Exception:
            continue
        dated_articles.append({"article": art, "parsed_date": parsed})

    if dated_articles:
        # sort descending by parsed_date
        dated_articles.sort(key=lambda x: x["parsed_date"], reverse=True)
        return dated_articles[0]["article"]

    # fallback
    return articles[0]


def draft_editorial(article, api_key):
    """
    Call OpenAI ChatCompletion to draft a Hindi editorial.
    Returns the editorial text, or raises on error.
    """
    prompt = (
        f"समाचार का शीर्षक: {article['title']}\n\n"
        f"पूरा समाचार:\n{article['content']}\n\n"
        f"{EDITORIAL_STYLE}"
    )

    openai.api_key = api_key
    response = openai.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "आप एक अनुभवी हिंदी समाचार संपादक हैं।"},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.4,
        max_tokens=1000,
    )
    return response.choices[0].message.content.strip()


def main():
    # 1) Collect URLs from CLI args or fallback to today_links.txt
    urls = sys.argv[1:]
    if not urls:
        # try the mounted workspace (/out)
        link_file = "/out/today_links.txt" if os.path.exists("/out/today_links.txt") else "today_links.txt"
        if not os.path.exists(link_file):
            print("No links provided and today_links.txt not found.")
            exit(1)
        with open(link_file, "r") as f:
            urls = [ln.strip() for ln in f if ln.strip()]

    if not urls:
        print("No URLs to process.")
        exit(1)

    # 2) Fetch all articles
    articles = []
    for u in urls:
        print(f"Fetching: {u}")
        articles.append(fetch_article(u))

    # 3) Select the best (most recent) article
    best = select_best_article(articles)
    print(f"Chosen for editorial: {best['title']} | date={best.get('date')}")

    # 4) Draft via OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Missing OPENAI_API_KEY in environment.")
        exit(1)

    editorial_text = draft_editorial(best, api_key)

    # 5) Write editorial to the mounted workspace
    out_path = "/out/editorial.txt"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(editorial_text)
        print(f"Editorial saved: {out_path}")
    except Exception as e:
        print(f"ERROR writing editorial: {e}")
        print("Contents of /out for debugging:", os.listdir("/out"))
        exit(1)

    # 6) Debug listing
    print("=== /out directory listing ===")
    for fn in os.listdir("/out"):
        print(" -", fn)


if __name__ == "__main__":
    main()
