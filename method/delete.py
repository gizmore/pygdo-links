from gdo.base.Method import Method
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Object import GDT_Object
from gdo.links.GDO_Link import GDO_Link


class delete(Method):
    @classmethod
    def gdo_trigger(cls):
        return 'links.delete'

    def gdo_user_permission(self):
        return GDO_Permission.ADMIN

    def gdo_transactional(self):
        return True

    def gdo_parameters(self):
        return [GDT_Object('id').table(GDO_Link.table()).not_null().positional(),
                GDT_Bool('confirm').not_null().initial('0')]

    def gdo_execute(self):
        if not self.param_value('confirm'):
            return self.err('err_link_delete_confirm')
        link = self.param_value('id')
        link_id = link.get_id()
        link.delete()
        return self.reply('msg_link_deleted', (link_id,))
