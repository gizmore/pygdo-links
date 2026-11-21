from gdo.base.Method import Method
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Object import GDT_Object
from gdo.links.GDO_Link import GDO_Link


class moderate(Method):
    @classmethod
    def gdo_trigger(cls):
        return 'links.moderate'

    def gdo_user_permission(self):
        return GDO_Permission.STAFF

    def gdo_transactional(self):
        return True

    def gdo_parameters(self):
        return [GDT_Object('id').table(GDO_Link.table()).not_null().positional(),
                GDT_Bool('approve').not_null().initial('0')]

    def gdo_execute(self):
        link = self.param_value('id')
        link = link.table().select().where(link.pk_where()).for_update().exec().fetch_object()
        if not link:
            return self.err('err_link_unavailable')
        link.save_val('link_approved', '1' if self.param_value('approve') else '0')
        return self.reply('msg_link_moderated', (link.get_id(),))
