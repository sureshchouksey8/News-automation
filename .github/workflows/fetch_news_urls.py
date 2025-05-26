#!/usr/bin/env python3
"""
fetch_news_urls.py – RSS robust today’s links extractor using feedparser.
"""

import logging
import feedparser
from datetime import datetime
from dateutil import tz
from dateutil.parser import parse as dtparse

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

RSS_FEEDS = [
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://feeds.feedburner.com/ndtvnews-latest",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.indianexpress.com/section/india/feed/",
    "https://www.hindustantimes.com/feeds/rss/latest/rssfeed.xml",
]

IST = tz.gettz("Asia/Kolkata")
TODAY = datetime.now(IST).date()

def is_today(entry):
    for key in ("published", "updated", "created"):
        val = entry.get(key)
        if val:
            try:
                dt = dtparse(val).astimezone(IST)
                if dt.date() == TODAY:
                    return True
            except Exception as e:
                logging.debug(f"Date parse error in {entry.get('link', 'no link')}: {e}")
    return False

def main():
    seen = set()
    links = []

    for url in RSS_FEEDS:
        logging.debug(f"Parsing RSS feed: {url}")
        d = feedparser.parse(url)
        if d.bozo:
            logging.debug(f"Feed parse error for {url}: {d.bozo_exception}")
        for entry in d.entries:
            pub = entry.get("published") or entry.get("updated") or entry.get("created") or ""
            logging.debug(f"  entry: {entry.get('link','NO_LINK')} | date: {pub}")
            if is_today(entry) and entry.get("link"):
                link = entry["link"]
                if link not in seen:
                    seen.add(link)
                    links.append(link)
            if len(links) >= 10:
                break
        if len(links) >= 10:
            break

    if links:
        with open("today_links.txt", "w") as f:
            for link in links:
                f.write(link + "\n")
        for link in links:
            print(link)
    else:
        logging.debug("❗ No links found for TODAY")

if __name__ == "__main__":
    main()
