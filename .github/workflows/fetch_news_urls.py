#!/usr/bin/env python3
"""
fetch_news_urls.py  –  RSS + HTML-fallback today’s links extractor
Auto-runs in GitHub Actions to produce today_links.txt
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil import parser as dparse
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.DEBUG, format="DEBUG: %(message)s")

# --- RSS feeds for Tier-1 Indian news (today’s top stories / national) ---
RSS_FEEDS = [
    "https://www.thehindu.com/rss/national.xml",
    "https://feeds.feedburner.com/NDTV-News?format=xml",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://indianexpress.com/section/india/feed/",
    "https://www.hindustantimes.com/rss/india/rssfeed.xml",
]

# --- Section pages to scrape if RSS yields nothing ---
HTML_SECTIONS = [
    "https://www.thehindu.com/news/national",
    "https://www.ndtv.com/india-news",
    "https://timesofindia.indiatimes.com/india",
    "https://indianexpress.com/section/india",
    "https://www.hindustantimes.com/india-news",
]

TODAY = datetime.now().date()
PATTERNS = [TODAY.strftime("%Y/%m/%d"), TODAY.strftime("%Y-%m-%d")]


def fetch_from_feed(url):
    try:
        logging.debug(f"Fetching RSS: {url}")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        links = []
        for item in root.findall(".//item"):
            pub = item.find("pubDate")
            if pub is None or not pub.text:
                continue
            if dparse.parse(pub.text).date() == TODAY:
                link = item.find("link")
                if link is not None and link.text:
                    links.append(link.text.strip())
        logging.debug(f"{len(links)} links from RSS")
        return links
    except Exception as e:
        logging.debug(f"ERROR fetching {url}: {e}")
        return []


def fetch_from_section(url):
    try:
        logging.debug(f"Scraping HTML: {url}")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(p in href for p in PATTERNS):
                full = href if href.startswith("http") else url.rstrip("/") + "/" + href.lstrip("/")
                links.append(full)
        logging.debug(f"{len(links)} links from HTML")
        return links
    except Exception as e:
        logging.debug(f"ERROR scraping {url}: {e}")
        return []


def main():
    seen = set()
    out = []

    # 1) Try RSS feeds first
    for feed in RSS_FEEDS:
        for link in fetch_from_feed(feed):
            if link not in seen:
                seen.add(link)
                out.append(link)
        if len(out) >= 10:
            break

    # 2) If still nothing, fall back to HTML scraping
    if not out:
        for section in HTML_SECTIONS:
            for link in fetch_from_section(section):
                if link not in seen:
                    seen.add(link)
                    out.append(link)
            if len(out) >= 10:
                break

    today_links = out[:10]
    if not today_links:
        logging.debug("❗ No links found for TODAY")

    # Write to file for Actions
    with open("today_links.txt", "w") as f:
        for u in today_links:
            f.write(u + "\n")

    # Echo to the log so you can see them in GitHub Actions
    for u in today_links:
        print(u)


if __name__ == "__main__":
    main()
