import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import datetime
import openai
from dateutil import parser as date_parser

# ====== CONFIGURABLE ======
OPENAI_MODEL = "gpt-4o"
EDITORIAL_STYLE = (
    "इस समाचार को पढ़कर एक संक्षिप्त, सरल, और सटीक संपादकीय लिखिए। "
    "संपादकीय में किसी उपशीर्षक, ब्रेक, या श्रेणी का प्रयोग न करें। "
    "केवल एक हिंदी शीर्षक दें, फिर एक लाइन छोड़कर संपादकीय शुरू करें। "
    "यह सब कुछ पूरी तरह हिंदी में हो, और ITDC News की तर्ज़ पर निष्पक्ष, तथ्यात्मक, और स्पष्ट रहे।"
)

# === Step 1: Fetch Article ===
def fetch_article(url):
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No Title'

        # Extract main content
        main_content = ""
        for selector in [
            'article',
            'div[itemprop="articleBody"]',
            'div[class*="content"]',
            'div[class*="story"]',
            'section[class*="article"]',
            'div#content',
        ]:
            el = soup.select_one(selector)
            if el and el.text.strip():
                main_content = el.get_text(separator="\n", strip=True)
                break
        if not main_content:
            main_content = "\n".join([p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)])

        # Extract dateline from meta tags (The Hindu, etc.)
        pub_date = None
        for meta in soup.find_all('meta'):
            for key in ('property', 'name', 'itemprop'):
                if meta.get(key, "").lower() in ['article:published_time', 'date', 'publishdate', 'article:modified_time', 'datepublished']:
                    date_val = meta.get('content', '') or meta.get('value', '')
                    # Try to extract full ISO timestamp or YYYY-MM-DD
                    match = re.search(r'\d{4}-\d{2}-\d{2}(T[0-9:.Z+-]+)?', date_val)
                    if match:
                        pub_date = match.group(0)
                        break
            if pub_date:
                break

        return {
            'title': title,
            'content': main_content or "[No main content found]",
            'url': url,
            'date': pub_date
        }
    except Exception as e:
        return {
            'title': url,
            'content': f"[ERROR fetching: {e}]",
            'url': url,
            'date': None
        }

# === Step 2: Select Most Recent Article (or fallback to first) ===
def select_best_article(articles):
    """
    Select the article with the most recent date.
    If dates are missing/unparseable, fallback to the first article.
    """
    dated_articles = []
    for art in articles:
        date_str = art.get("date")
        parsed = None
        if date_str:
            try:
                parsed = date_parser.parse(date_str)
            except Exception:
                pass
        if parsed:
            dated_articles.append({"article": art, "parsed_date": parsed})

    if dated_articles:
        # Sort by parsed date descending (newest first)
        dated_articles.sort(key=lambda x: x["parsed_date"], reverse=True)
        return dated_articles[0]["article"]
    return articles[0]

# === Step 3: Build Editorial via OpenAI ===
def draft_editorial(article, api_key):
    prompt = (
        f"समाचार का शीर्षक: {article['title']}\n"
        f"पूरा समाचार:\n{article['content']}\n\n"
        f"{EDITORIAL_STYLE}"
    )
    try:
        openai.api_key = api_key
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "आप एक अनुभवी हिंदी समाचार संपादक हैं।"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR: GPT API failed]\n{e}"

def main():
    # ==== 1. Read URLs ====
    urls = sys.argv[1:]
    if not urls:
        if os.path.exists('/out/today_links.txt'):
            with open('/out/today_links.txt', 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        elif os.path.exists('today_links.txt'):
            with open('today_links.txt', 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        else:
            print("No links provided and today_links.txt (in /out/ or current dir) does not exist.")
            exit(1)
    if not urls:
        print("No links found.")
        exit(1)

    # ==== 2. Fetch All Articles ====
    articles = []
    for url in urls:
        print(f"Fetching: {url}")
        art = fetch_article(url)
        articles.append(art)
    if not articles:
        print("No articles fetched.")
        exit(1)

    # ==== 3. Choose Best ====
    chosen = select_best_article(articles)
    print(f"Selected for editorial: {chosen['title']} (date: {chosen['date']})")

    # ==== 4. Call OpenAI ====
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("No OPENAI_API_KEY in environment. Exiting.")
        exit(1)
    editorial = draft_editorial(chosen, api_key)
    if editorial.startswith("[ERROR"):
        print(editorial)
        exit(1)

    # ==== 5. Write Out (/out/editorial.txt) ====
    editorial_path = "/out/editorial.txt"
    try:
        with open(editorial_path, 'w', encoding='utf-8') as f:
            f.write(editorial)
        print(f"Editorial body saved to {editorial_path}")
    except Exception as e:
        print(f"Error writing to {editorial_path}: {e}")
        print("Listing /out directory for debug:")
        try:
            os.system("ls -la /out")
        except Exception as ls_e:
            print(f"Could not list /out: {ls_e}")
        exit(1)

    # Debug
    print("=== Directory listing for debugging (/out) ===")
    if os.path.exists("/out"):
        for entry in os.listdir("/out"):
            print(os.path.join("/out", entry))
    else:
        print("/out does not exist.")

if __name__ == '__main__':
    main()
