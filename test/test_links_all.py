import unittest
from unittest.mock import Mock, patch

from gdo.base.Application import Application
from gdo.base.Render import Mode
from gdo.links.method.links import links
from gdo.table.MethodQueryTable import MethodQueryTable


class LinksAllTest(unittest.TestCase):
    def setUp(self):
        Application.mode(Mode.render_txt)

    def test_unapproved_are_only_visible_to_staff_with_all(self):
        for requested, staff, filtered in ((False, False, True), (False, True, True),
                                           (True, False, True), (True, True, False)):
            with self.subTest(requested=requested, staff=staff):
                method = links()
                method._env_user = Mock()
                method._env_user.is_staff.return_value = staff
                query = Mock()
                with patch.object(MethodQueryTable, 'gdo_table_query', return_value=query), \
                     patch.object(method, 'param_value', return_value=requested):
                    self.assertIs(query, method.gdo_table_query())
                if filtered:
                    query.where.assert_called_once_with('link_approved=1')
                else:
                    query.where.assert_not_called()

    def test_option_is_non_positional_and_off_by_default(self):
        option = next(param for param in links().gdo_parameters() if param.get_name() == 'all')
        self.assertEqual('0', option._initial)
