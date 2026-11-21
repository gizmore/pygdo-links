import unittest
from unittest.mock import AsyncMock, Mock, patch

from gdo.links.url_parts import extract_urls, parse_url
from gdo.links.method.settings import settings
from gdo.links.module_links import module_links
from gdo.links.preview import _Metadata, _public_addresses


class LinkParsingTest(unittest.TestCase):
    def test_parts_preserve_url_and_normalize_host(self):
        self.assertEqual({'url': 'https://EXAMPLE.org/a?q=1', 'host': 'example.org',
                          'path': '/a', 'query': 'q=1'},
                         parse_url('https://EXAMPLE.org/a?q=1'))

    def test_unsafe_or_unrepresentable_inputs_are_not_collected(self):
        for url in ('https://user:secret@example.org/', 'https://x:99999/',
                    'https://é.example/', 'https://' + 'x' * 97 + '/'):
            self.assertIsNone(parse_url(url))

    def test_extract_and_private_default(self):
        self.assertEqual(['https://example.org/a'],
                         [p['url'] for p in extract_urls('See https://example.org/a!')])
        self.assertFalse(settings.collection_enabled(None))

    def test_collection_requires_opt_in_and_uses_only_channel_messages(self):
        import asyncio
        module = module_links()
        module.record_sighting = Mock(return_value=None)
        message = Mock(_env_channel=None, _message='https://example.org/')
        asyncio.run(module.on_new_message(message))
        module.record_sighting.assert_not_called()
        message._env_channel = object()
        with patch.object(settings, 'collection_enabled', return_value=True):
            asyncio.run(module.on_new_message(message))
        module.record_sighting.assert_called_once()

    def test_new_link_notice_only_in_originating_channel(self):
        import asyncio
        module = module_links()
        link = Mock()
        link.gdo_val.side_effect = lambda name: {'link_title': 'Title\nhello',
                                                 'link_description': 'Description'}[name]
        link.get_id.return_value = '7'
        module.record_sighting = Mock(return_value=link)
        module.populate_preview = AsyncMock()
        channel = Mock()
        channel.get_trigger.return_value = '!'
        channel.send_text = AsyncMock()
        message = Mock(_env_channel=channel, _message='https://example.org/')
        with patch.object(settings, 'collection_enabled', return_value=True):
            asyncio.run(module.on_new_message(message))
        channel.send_text.assert_awaited_once_with('msg_link_detected',
                                                   ('Title hello', 'Description', '!', '7'))

    def test_duplicate_does_not_announce(self):
        import asyncio
        module = module_links()
        module.record_sighting = Mock(return_value=None)
        channel = Mock()
        channel.send_text = AsyncMock()
        with patch.object(settings, 'collection_enabled', return_value=True):
            asyncio.run(module.on_new_message(Mock(_env_channel=channel, _message='https://example.org/')))
        channel.send_text.assert_not_awaited()

    def test_preview_rejects_mixed_public_and_private_dns(self):
        with patch('gdo.links.preview.socket.getaddrinfo', return_value=[
            (2, 1, 6, '', ('8.8.8.8', 443)), (2, 1, 6, '', ('127.0.0.1', 443))]):
            with self.assertRaises(ValueError):
                _public_addresses('example.org', 443)

    def test_html_metadata_is_plain_text(self):
        parser = _Metadata()
        parser.feed('<title>Hi &amp; bye</title><meta name="description" content="nice &amp; easy">')
        self.assertEqual('Hi & bye', parser.title)
        self.assertEqual('nice & easy', parser.description)
