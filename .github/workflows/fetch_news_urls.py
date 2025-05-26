#!/usr/bin/env python3
"""
fetch_news_urls.py  –  RSS + HTML-fallback today’s links extractor
Auto-runs in GitHub Actions to produce today_links.txt
"""

import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil import parser as dparse
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

# --- source lists ---
RSS_FEEDS = [
    "https://www.thehindu.com/news/national/rss.xml",
    "https://feeds.feedburner.com/ndtvnews-latest",      # official NDTV
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://indianexpress.com/section/india/feed/",
    "https://www.hindustantimes.com/rss/india/rssfeed.xml",
]

HTML_SECTIONS = [
    "https://www.thehindu.com/news/national",
    "https://www.ndtv.com/india-news",
    "https://timesofindia.indiatimes.com/india",
    "https://indianexpress.com/section/india",
    "https://www.hindustantimes.com/india-news",
]

TODAY = datetime.now().date()
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36"

def fetch_from_rss(url):
    logging.debug(f"Fetching RSS: {url}")
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        links = []
        for item in items:
            pub = item.find("pubDate")
            if not pub or not pub.text:
                continue
            pub_date = dparse.parse(pub.text).date()
            if pub_date == TODAY:
                link = item.find("link")
                if link is not None and link.text:
                    links.append(link.text.strip())
        logging.debug(f"{len(links)} links from RSS")
        return links
    except Exception as e:
        logging.debug(f"ERROR fetching {url}: {e}")
        return []

def fetch_from_html(url):
    logging.debug(f"Scraping HTML: {url}")
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        today_str = TODAY.strftime("%d %B %Y")
        links = []
        for a in soup.find_all("a", href=True):
            text = (a.get_text(" ", strip=True) or "") + " " + (a.get("title") or "")
            if today_str in text:
                href = a["href"]
                if href.startswith("/"):
                    href = url.rstrip("/") + href
                links.append(href)
        logging.debug(f"{len(links)} links from HTML")
        return links
    except Exception as e:
        logging.debug(f"ERROR scraping {url}: {e}")
        return []

def main():
    seen = set()
    out = []

    # 1. Try RSS feeds
    for feed in RSS_FEEDS:
        for link in fetch_from_rss(feed):
            if link not in seen:
                seen.add(link)
                out.append(link)
        if len(out) >= 10:
            break

    # 2. If still none, try HTML sections
    if not out:
        logging.debug("❗ RSS gave 0 — falling back to HTML scraping")
        for sec in HTML_SECTIONS:
            for link in fetch_from_html(sec):
                if link not in seen:
                    seen.add(link)
                    out.append(link)
            if len(out) >= 10:
                break

    today_links = out[:10]
    if not today_links:
        logging.debug("❗ No links found for TODAY")
    else:
        # write file + print
        with open("today_links.txt", "w") as f:
            for u in today_links:
                f.write(u + "\n")
        for u in today_links:
            print(u)

if __name__ == "__main__":
    main()
