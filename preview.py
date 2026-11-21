"""Bounded previews, with DNS checked and pinned separately at each redirect."""
import http.client
import ipaddress
import socket
from threading import BoundedSemaphore
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from gdo.links.url_parts import parse_url

MAX_BYTES = 65536
_FETCH_SLOTS = BoundedSemaphore(4)


class _Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title = ''
        self.description = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == 'title':
            self.in_title = True
        elif tag.lower() == 'meta' and (attrs.get('name') or '').lower() == 'description':
            self.description = attrs.get('content') or ''

    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def _public_addresses(host, port):
    addresses = {item[4][0] for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError('host resolves to a non-public address')
    return sorted(addresses)


def _open_pinned(parts):
    port = parts.port or (443 if parts.scheme == 'https' else 80)
    addresses = _public_addresses(parts.hostname, port)
    connection_cls = http.client.HTTPSConnection if parts.scheme == 'https' else http.client.HTTPConnection
    connection = connection_cls(parts.hostname, port, timeout=5)
    # HTTPSConnection still verifies the certificate against the original hostname.
    connection._create_connection = lambda address, timeout, source_address=None: socket.create_connection(
        (addresses[0], port), timeout, source_address)
    return connection


def fetch_preview(url):
    if not _FETCH_SLOTS.acquire(blocking=False):
        return None
    try:
        return _fetch_preview(url)
    finally:
        _FETCH_SLOTS.release()


def _fetch_preview(url):
    for _ in range(4):
        if not parse_url(url):
            raise ValueError('invalid URL')
        parts = urlsplit(url)
        connection = _open_pinned(parts)
        try:
            path = parts.path or '/'
            if parts.query:
                path += '?' + parts.query
            connection.request('GET', path, headers={'Accept': 'text/plain, text/html',
                                                     'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader('Location')
                if not location:
                    raise ValueError('redirect has no location')
                url = urljoin(url, location)
                continue
            if response.status != 200 or response.getheader('Content-Encoding', 'identity').lower() != 'identity':
                return None
            content_type = response.getheader('Content-Type', '').split(';', 1)[0].strip().lower()
            if content_type not in ('text/plain', 'text/html'):
                return None
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                body = body[:MAX_BYTES]
            text = body.decode('utf-8', errors='replace')
            if content_type == 'text/plain':
                return {'title': '', 'description': ' '.join(text.splitlines()[:3])[:1024]}
            parser = _Metadata()
            parser.feed(text)
            return {'title': ' '.join(parser.title.split())[:255],
                    'description': ' '.join(parser.description.split())[:1024]}
        finally:
            connection.close()
    raise ValueError('too many redirects')
