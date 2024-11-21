from urllib.parse import urlparse

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
