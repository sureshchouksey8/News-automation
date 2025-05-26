#!/usr/bin/env python3
"""
fetch_news_urls.py  –  RSS-based today’s links extractor
Auto-runs in GitHub Actions to produce today_links.txt
"""

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
    except Exception:
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

    today_links = out[:10]  # limit to 10 links

    # Write to file for workflow
    with open("today_links.txt", "w") as f:
        for u in today_links:
            f.write(u + "\n")

    # Print to logs for visibility
    for u in today_links:
        print(u)

if __name__ == "__main__":
    main()
