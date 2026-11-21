from gdo.core.GDT_Object import GDT_Object
from gdo.links.GDO_Link import GDO_Link
from gdo.links.GDO_LinkVote import GDO_LinkVote
from gdo.vote.MethodVote import MethodVote


class up(MethodVote):
    @classmethod
    def gdo_trigger(cls):
        return 'links.up'

    def gdo_votes_table(self):
        return GDO_LinkVote.table()

    def gdo_vote_object_table(self):
        return GDO_Link.table()

    def gdo_parameters(self):
        return [GDT_Object('id').not_null().table(GDO_Link.table()).positional()]

    def param_val(self, name):
        if name == 'score':
            return '1'
        if name == 'reason':
            return None
        return super().param_val(name)

    async def gdo_execute(self):
        obj = self.get_vote_object()
        current = obj.table().select().where(obj.pk_where()).for_update().exec().fetch_object()
        if not current or not current.gdo_value('link_approved'):
            return self.err('err_link_unavailable')
        return await super().gdo_execute()
