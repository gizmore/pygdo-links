import unittest
from unittest.mock import AsyncMock, Mock, patch

from gdo.base.Application import Application
from gdo.base.Render import Mode
from gdo.core.GDO_Permission import GDO_Permission
from gdo.links.method.delete import delete
from gdo.links.method.moderate import moderate
from gdo.links.method.up import up
from gdo.vote.MethodVote import MethodVote


class LinksActionsTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Application.mode(Mode.render_txt)

    async def test_unapproved_link_cannot_be_upvoted(self):
        method = up()
        obj = Mock()
        current = obj.table.return_value.select.return_value.where.return_value.for_update.return_value.exec.return_value.fetch_object.return_value
        current.gdo_value.return_value = False
        method.get_vote_object = Mock(return_value=obj)
        method.err = Mock(return_value='unavailable')
        with patch.object(MethodVote, 'gdo_execute', new_callable=AsyncMock) as vote:
            self.assertEqual('unavailable', await method.gdo_execute())
        vote.assert_not_awaited()

    async def test_approved_link_uses_vote_module(self):
        method = up()
        obj = Mock()
        obj.table.return_value.select.return_value.where.return_value.for_update.return_value.exec.return_value.fetch_object.return_value.gdo_value.return_value = True
        method.get_vote_object = Mock(return_value=obj)
        with patch.object(MethodVote, 'gdo_execute', new_callable=AsyncMock, return_value='voted') as vote:
            self.assertEqual('voted', await method.gdo_execute())
        vote.assert_awaited_once()
        self.assertEqual('1', method.param_val('score'))

    def test_moderation_roles_and_hard_delete_confirmation(self):
        self.assertEqual(GDO_Permission.STAFF, moderate().gdo_user_permission())
        method = delete()
        self.assertEqual(GDO_Permission.ADMIN, method.gdo_user_permission())
        method.param_value = Mock(return_value=False)
        method.err = Mock(return_value='confirm')
        self.assertEqual('confirm', method.gdo_execute())
        method.param_value.assert_called_once_with('confirm')
