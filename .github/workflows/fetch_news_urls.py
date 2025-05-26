#!/usr/bin/env python3
"""
fetch_news_urls.py – RSS/HTML-based today’s links extractor for GitHub Actions
Auto-runs to produce today_links.txt
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil import parser as dparse
from bs4 import BeautifulSoup
import logging

# configure debug logging
logging.basicConfig(level=logging.DEBUG, format='DEBUG: %(message)s')

# Tier-1 Indian news sources: RSS feeds
RSS_FEEDS = [
    "https://www.thehindu.com/news/national/rssfeed.xml",
    "https://feeds.feedburner.com/NDTV-LatestNews",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://indianexpress.com/section/india/feed/",
    "https://www.hindustantimes.com/rss/india/rssfeed.xml",
]

# Fallback homepages (for date-coded URL sniffing)
SITE_URLS = [
    "https://www.thehindu.com/",
    "https://www.ndtv.com/",
    "https://timesofindia.indiatimes.com/",
    "https://indianexpress.com/",
    "https://www.hindustantimes.com/",
]

TODAY = datetime.now().date()
DATE_SEG = TODAY.strftime("%Y/%m/%d")

def fetch_from_feed(url):
    logging.debug(f"Fetching RSS: {url}")
    try:
        resp = requests.get(url, timeout=10)
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
        logging.debug(f"{len(links)} links from RSS: {url}")
        return links
    except Exception as e:
        logging.debug(f"ERROR fetching RSS {url}: {e}")
        return []

def fetch_date_links(site_url):
    logging.debug(f"Fallback HTML fetch: {site_url}")
    links = []
    try:
        resp = requests.get(site_url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all('a', href=True):
            href = a['href']
            if DATE_SEG in href:
                if href.startswith('http'):
                    links.append(href)
                else:
                    links.append(site_url.rstrip('/') + '/' + href.lstrip('/'))
        logging.debug(f"{len(links)} date-coded links from HTML: {site_url}")
    except Exception as e:
        logging.debug(f"ERROR fetching HTML {site_url}: {e}")
    return links

def main():
    seen = set()
    out = []

    # 1) Try RSS feeds
    for feed in RSS_FEEDS:
        for link in fetch_from_feed(feed):
            if link not in seen:
                seen.add(link)
                out.append(link)
        if len(out) >= 10:
            break

    # 2) Fallback to date-coded URLs if needed
    if len(out) < 10:
        for site in SITE_URLS:
            for link in fetch_date_links(site):
                if link not in seen:
                    seen.add(link)
                    out.append(link)
            if len(out) >= 10:
                break

    today_links = out[:10]  # cap at 10

    if not today_links:
        logging.debug("❗ No links found for TODAY")

    # Write for GitHub Actions
    with open("today_links.txt", "w") as f:
        for u in today_links:
            f.write(u + "\n")

    # Print them into the Actions log
    for u in today_links:
        print(u)

if __name__ == "__main__":
    main()
