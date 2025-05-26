import requests
from bs4 import BeautifulSoup

def fetch_article(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
        # Extract the title
        title = soup.title.string.strip() if soup.title else 'No Title'
        # Extract the main content; tweak this selector for your target sites!
        main_content = ""
        # Try a few common selectors
        for selector in [
            'article',                           # Most modern sites
            'div[itemprop="articleBody"]',       # Many news sites
            'div[class*="content"]',
            'div[class*="story"]',
            'section[class*="article"]',
            'div#content',
        ]:
            el = soup.select_one(selector)
            if el and el.text.strip():
                main_content = el.get_text(separator="\n", strip=True)
                break
        # Fallback to all <p> tags if nothing else
        if not main_content:
            main_content = "\n".join([p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)])
        return {
            'title': title,
            'content': main_content or "[No main content found]"
        }
    except Exception as e:
        return {
            'title': url,
            'content': f"[ERROR fetching: {e}]"
        }

def main():
    # Read URLs from today_links.txt
    with open('today_links.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    if len(urls) < 1:
        print("No links found in today_links.txt")
        exit(1)

    articles = []
    for url in urls:
        print(f"Fetching: {url}")
        article = fetch_article(url)
        articles.append(article)

    # Build the message body
    body_lines = []
    for i, art in enumerate(articles, 1):
        body_lines.append(f"### {i}. {art['title']}\n\n{art['content']}\n")

    body = "\n\n---\n\n".join(body_lines)

    # Save to file for email body (since dawidd6/action-send-mail@v3 can use body_file)
    with open('editorial.txt', 'w', encoding='utf-8') as f:
        f.write(body)

    print("Editorial body saved to editorial.txt")

if __name__ == '__main__':
    main()
