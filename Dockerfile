FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only if you use playwright or lxml_html_clean (if not, you can comment them out)
RUN pip install lxml_html_clean || true
RUN pip install playwright || true
RUN playwright install chromium --with-deps || true

COPY . .

RUN chmod +x entrypoint.sh  
ENTRYPOINT ["bash","entrypoint.sh"]
