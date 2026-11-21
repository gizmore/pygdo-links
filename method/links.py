from gdo.links.GDO_Link import GDO_Link
from gdo.core.GDT_Bool import GDT_Bool
from gdo.table.MethodQueryTable import MethodQueryTable


class links(MethodQueryTable):
    @classmethod
    def gdo_trigger(cls):
        return 'links'

    def gdo_table(self):
        return GDO_Link.table()

    def gdo_parameters(self):
        return super().gdo_parameters() + [GDT_Bool('all').not_null().initial('0')]

    def gdo_table_query(self):
        query = super().gdo_table_query()
        # Unapproved includes soft-deleted records, so only moderators can see them.
        if not (self.param_value('all') and self._env_user and self._env_user.is_staff()):
            query.where('link_approved=1')
        return query

    def gdo_table_headers(self):
        table = self.gdo_table()
        return [table.column(name) for name in ('link_id', 'link_title', 'link_url',
                'link_host', 'link_description', 'link_sightings', 'link_vote_count')]
