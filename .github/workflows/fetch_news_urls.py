#!/usr/bin/env python3
"""
fetch_news_urls.py – RSS + HTML fallback today’s links extractor for GitHub Actions
Writes up to 10 URLs (from Tier-1 Indian outlets) published TODAY.
"""

import requests, logging
from datetime import datetime
from dateutil import parser as dparse
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG, format='DEBUG: %(message)s')
TODAY = datetime.now().date()
DATE_SEG = TODAY.strftime("%Y/%m/%d")

# 1) RSS feeds (only those that still work)
RSS_FEEDS = [
    "https://www.thehindu.com/news/national/rssfeed.xml",
    "https://feeds.feedburner.com/ndtvnews-latest",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://indianexpress.com/section/india/feed/",
    # Hindustan Times RSS is now 401; we’ll scrape its HTML section instead
]

# 2) Section pages for HTML fallback (look for /YYYY/MM/DD/ in the URL)
SECTION_URLS = [
    "https://www.thehindu.com/news/national/",
    "https://www.ndtv.com/india-news",
    "https://timesofindia.indiatimes.com/india",
    "https://indianexpress.com/section/india/",
    "https://www.hindustantimes.com/india-news/",
]

def fetch_from_rss(url):
    logging.debug(f"Fetching RSS: {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        links = []
        for item in root.findall(".//item"):
            pub = item.find("pubDate")
            if not pub is None and pub.text:
                if dparse.parse(pub.text).date() == TODAY:
                    link = item.find("link")
                    if link is not None and link.text:
                        links.append(link.text.strip())
        logging.debug(f"{len(links)} links from RSS")
        return links
    except Exception as e:
        logging.debug(f"ERROR RSS {url}: {e}")
        return []

def fetch_from_section(url):
    logging.debug(f"Scraping HTML: {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if DATE_SEG in href:
                if href.startswith("http"):
                    links.add(href)
                else:
                    links.add(url.rstrip("/") + "/" + href.lstrip("/"))
        logging.debug(f"{len(links)} links from HTML")
        return list(links)
    except Exception as e:
        logging.debug(f"ERROR HTML {url}: {e}")
        return []

def main():
    seen, out = set(), []

    # 1) Try RSS
    for feed in RSS_FEEDS:
        for link in fetch_from_rss(feed):
            if link not in seen:
                seen.add(link)
                out.append(link)
        if len(out) >= 10:
            break

    # 2) Fallback to section-page scraping
    if len(out) < 10:
        for sec in SECTION_URLS:
            for link in fetch_from_section(sec):
                if link not in seen:
                    seen.add(link)
                    out.append(link)
            if len(out) >= 10:
                break

    today_links = out[:10]
    if not today_links:
        logging.debug("❗ No links found for TODAY")

    # write for Actions
    with open("today_links.txt", "w") as f:
        for u in today_links:
            f.write(u + "\n")

    # echo into the log
    for u in today_links:
        print(u)


if __name__ == "__main__":
    main()
