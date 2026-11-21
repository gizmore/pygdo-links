import unittest
from unittest.mock import AsyncMock, Mock, patch

from gdo.base.Application import Application
from gdo.base.Render import Mode
from gdo.links.module_links import module_links


class LinksDeliveryTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Application.mode(Mode.render_txt)

    async def test_spread_is_dog_only_and_to_subscribers(self):
        module = module_links()
        link = Mock()
        values = {'link_url': 'https://example.org/a', 'link_title': 'Title',
                  'link_description': 'Description'}
        link.gdo_val.side_effect = values.get
        link.get_votes_total.return_value = 1
        link.get_id.return_value = '42'
        module.claim_pending = Mock(side_effect=[link, None])
        channel = Mock()
        channel.get_trigger.return_value = '!'
        channel.send_text = AsyncMock()
        with patch.object(Application, 'IS_DOG', True), \
             patch('gdo.links.module_links.GDO_Channel.with_setting', return_value=[channel]) as subscribers:
            await module.spread_pending()
        subscribers.assert_called_once()
        self.assertEqual(('links_abbo', '1', '0'), subscribers.call_args.args[1:])
        channel.send_text.assert_awaited_once_with('msg_link_spread', (
            'https://example.org/a', 'Title', 'Description', 1, '!', '42'))

    async def test_non_dog_does_not_claim(self):
        module = module_links()
        module.claim_pending = Mock()
        with patch.object(Application, 'IS_DOG', False):
            await module.spread_pending()
        module.claim_pending.assert_not_called()

    async def test_failure_of_one_destination_does_not_prevent_next(self):
        module = module_links()
        link = Mock()
        link.gdo_val.return_value = 'value'
        link.get_votes_total.return_value = 1
        module.claim_pending = Mock(side_effect=[link, None])
        bad, good = Mock(), Mock()
        bad.send_text = AsyncMock(side_effect=OSError('offline'))
        good.send_text = AsyncMock()
        with patch.object(Application, 'IS_DOG', True), \
             patch('gdo.links.module_links.GDO_Channel.with_setting', return_value=[bad, good]), \
             patch('gdo.links.module_links.Logger.warning'):
            await module.spread_pending()
        good.send_text.assert_awaited_once()

    async def test_preview_rejects_deleted_link(self):
        module = module_links()
        link = Mock()
        deleted = Mock()
        deleted.gdo_value.return_value = False
        table = Mock()
        table.get_by_id.return_value = deleted
        with patch('gdo.links.module_links.fetch_preview', return_value={'title': 'x'}), \
             patch('gdo.links.module_links.GDO_Link.table', return_value=table):
            self.assertFalse(await module.populate_preview(link, 'https://example.org/'))
        deleted.save_vals.assert_not_called()
