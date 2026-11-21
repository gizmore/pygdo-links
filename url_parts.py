"""Conservative URL extraction; this module never fetches a URL."""
import re
from urllib.parse import urlsplit

URL_RE = re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE)


def parse_url(url):
    if len(url) > 1024 or not url.isascii() or any(ord(c) < 33 for c in url):
        return None
    try:
        parts = urlsplit(url)
        host = parts.hostname
        if (parts.scheme.lower() not in ('http', 'https') or not host or
                parts.username is not None or parts.password is not None or
                len(host) > 96 or len(parts.path) > 1024 or len(parts.query) > 1024):
            return None
        parts.port  # Reject malformed ports.
    except ValueError:
        return None
    return {'url': url, 'host': host.lower(), 'path': parts.path or '/', 'query': parts.query}


def extract_urls(text):
    for match in URL_RE.finditer(text):
        url = match.group().rstrip('.,!?;:')
        parsed = parse_url(url)
        if parsed:
            yield parsed
