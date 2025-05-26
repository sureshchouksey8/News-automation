#!/usr/bin/env python3
"""
fetch_news_urls.py  –  RSS-based today’s links extractor
Auto-runs in GitHub Actions to produce today_links.txt
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil import parser as dparse

# ——— Updated RSS feeds for Tier-1 Indian news (today’s top stories) ———
RSS_FEEDS = [
    "https://www.thehindu.com/news/national/rssfeed.xml",
    "https://feeds.feedburner.com/ndtvnews-latest",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://indianexpress.com/section/india/feed/",
    "https://www.hindustantimes.com/rss/rssfeed.xml",
    # you can add more working RSS URLs here as you find them
]

TODAY = datetime.now().date()

def fetch_from_feed(url):
    print(f"DEBUG: Fetching {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        links = []
        for item in root.findall(".//item"):
            pub = item.find("pubDate")
            if pub is None or not pub.text:
                continue
            pub_date = dparse.parse(pub.text).date()
            if pub_date == TODAY:
                link = item.find("link")
                if link is not None and link.text:
                    links.append(link.text.strip())
        print(f"DEBUG: {len(links)} links from {url}")
        return links
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")
        return []

def main():
    seen = set()
    out = []

    for feed in RSS_FEEDS:
        for link in fetch_from_feed(feed):
            if link not in seen:
                seen.add(link)
                out.append(link)
        if len(out) >= 10:
            break

    if not out:
        print("DEBUG: ❗ No links found for TODAY")

    today_links = out[:10]  # limit to 10 links

    # Write to file for the workflow step
    with open("today_links.txt", "w") as f:
        for u in today_links:
            f.write(u + "\n")

    # Also echo them in the Actions log
    for u in today_links:
        print(u)

if __name__ == "__main__":
    main()
