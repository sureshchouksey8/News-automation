FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps
RUN pip install lxml_html_clean

COPY . .
RUN chmod +x entrypoint.sh  
ENTRYPOINT ["bash","entrypoint.sh"]
