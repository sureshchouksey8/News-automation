import os
import sys
import requests
from bs4 import BeautifulSoup

def fetch_article(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No Title'
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
    import os

    # Prefer URLs from command-line
    urls = sys.argv[1:]
    if not urls:
        # Fallback to file only if no CLI args
        if os.path.exists('/out/today_links.txt'):
            with open('/out/today_links.txt', 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        elif os.path.exists('today_links.txt'):
            with open('today_links.txt', 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        else:
            print("No links provided and today_links.txt does not exist.")
            exit(1)

    if len(urls) < 1:
        print("No links found.")
        exit(1)

    articles = []
    for url in urls:
        print(f"Fetching: {url}")
        article = fetch_article(url)
        articles.append(article)

    body_lines = []
    for i, art in enumerate(articles, 1):
        body_lines.append(f"### {i}. {art['title']}\n\n{art['content']}\n")
    body = "\n\n---\n\n".join(body_lines)

    # >>>> HERE IS THE IMPORTANT PART <<<<
    # Always write output to /out/editorial.txt (host-mapped directory)
    output_path = "/out/editorial.txt" if os.path.exists("/out") else "editorial.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(body)

    print(f"Editorial body saved to {output_path}")

if __name__ == '__main__':
    main()
