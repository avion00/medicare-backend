import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from db import get_db_connection


IGNORE_EXTENSIONS = (
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg',
    '.ico', '.mp4', '.mp3', '.wav', '.avi', '.mov', '.pdf',
    '.zip', '.rar', '.tar', '.gz'
)

def is_valid_url(url, base_domain):
    parsed_url = urlparse(url)
    if parsed_url.netloc != base_domain:
        return False
    if any(url.lower().endswith(ext) for ext in IGNORE_EXTENSIONS):
        return False
    return True

def clean_text(soup):
    for script_or_style in soup(['script', 'style', 'meta', 'link']):
        script_or_style.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return ' '.join(text.split())

def summarize_text(text, max_tokens=100):
    # Summarization logic (e.g., using OpenAI API) or simple fallback
    return text[:max_tokens]

def crawl_major_pages(base_url, max_pages=5):
    visited = set()
    to_visit = [base_url]
    base_domain = urlparse(base_url).netloc
    all_summaries = []

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            response = requests.get(current_url, timeout=10)
            if 'text/html' in response.headers.get('Content-Type', ''):
                soup = BeautifulSoup(response.text, 'html.parser')
                content = clean_text(soup)
                if content:
                    summary = summarize_text(content, max_tokens=100)
                    all_summaries.append(summary)

                for link in soup.find_all('a', href=True):
                    href = link['href']
                    next_url = urljoin(base_url, href)
                    if is_valid_url(next_url, base_domain):
                        next_url = next_url.split('#')[0]
                        if next_url not in visited:
                            to_visit.append(next_url)
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")

    return ' '.join(all_summaries)



# Save summaries to the database
def save_summary_to_db(base_url, summaries):
    conn = get_db_connection()
    cursor = conn.cursor()

    for summary in summaries:
        cursor.execute('''
            INSERT INTO knowledge_base (website_url, summary)
            VALUES (%s, %s)
        ''', (summary['url'], summary['summary']))

    conn.commit()
    conn.close()

def fetch_knowledge_base():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query to fetch data from knowledge_base
        cursor.execute("SELECT * FROM knowledge_base;")
        rows = cursor.fetchall()

        for row in rows:
            print(row)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
