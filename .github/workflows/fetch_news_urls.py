# fetch_news_urls.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TIER1_SITES = [
    "https://www.thehindu.com/news/",
    "https://www.ndtv.com/india-news",
    "https://timesofindia.indiatimes.com/india",
    "https://indianexpress.com/section/india/",
    "https://www.hindustantimes.com/india-news",
]

today = datetime.now().strftime('%d %B %Y')  # e.g., "25 May 2025"

def find_today_links(site_url):
    try:
        r = requests.get(site_url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all('a', href=True):
            if today in a.text or today in a.get('title', ''):
                links.append(a['href'])
        return links
    except Exception:
        return []

all_links = set()
for url in TIER1_SITES:
    links = find_today_links(url)
    for l in links:
        if l.startswith('http'):
            all_links.add(l)
        else:
            all_links.add(url.rstrip('/') + '/' + l.lstrip('/'))

with open('today_links.txt', 'w') as f:
    for link in list(all_links)[:10]:
        f.write(link.strip() + '\n')
