#!/usr/bin/env python3
"""
fetch_news_urls.py  –  RSS‐based today’s links extractor
Auto-runs in GitHub Actions to produce today_links.txt
(with debug logging to stderr)
"""

import sys
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil import parser as dparse

# --- RSS feeds for Tier-1 Indian news (today’s top stories / national) ---
RSS_FEEDS = [
    "https://www.thehindu.com/news/national/?service=rss",
    "https://feeds.feedburner.com/NDTV-News",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://indianexpress.com/section/india/feed/",
    "https://www.hindustantimes.com/rss/india/rssfeed.xml",
]

TODAY = datetime.now().date()

def fetch_from_feed(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        links = []
        for item in root.findall(".//item"):
            pub = item.find("pubDate")
            if not pub or not pub.text:
                continue
            pub_date = dparse.parse(pub.text).date()
            if pub_date == TODAY:
                link = item.find("link")
                if link is not None and link.text:
                    links.append(link.text.strip())
        return links
    except Exception as e:
        print(f"ERROR fetching {url}: {e}", file=sys.stderr)
        return []

def main():
    seen = set()
    out = []

    for feed in RSS_FEEDS:
        print(f"DEBUG: Fetching {feed}", file=sys.stderr)
        links = fetch_from_feed(feed)
        print(f"DEBUG: {len(links)} links from {feed}", file=sys.stderr)
        for u in links:
            if u not in seen:
                seen.add(u)
                out.append(u)
        if len(out) >= 10:
            break

    if not out:
        print("DEBUG: ❗ No links found for TODAY", file=sys.stderr)

    # write the actual list for the next step
    with open("today_links.txt", "w") as f:
        for u in out[:10]:
            f.write(u + "\n")

    # and echo them to stdout so they show up in the Actions log
    for u in out[:10]:
        print(u)

if __name__ == "__main__":
    main()
