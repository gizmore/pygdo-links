from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_String import GDT_String
from gdo.date.GDT_Created import GDT_Created
from gdo.net.GDT_Url import GDT_Url


class GDO_Link(GDO):

    def gdo_cached(self) -> bool:
        return False

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('link_id'),
            GDT_String('link_title').not_null(),
            GDT_String('link_description').maxlen(1024),
            GDT_Url('link_url').not_null(),
            GDT_Bool('link_approved').not_null().initial('1'),
            GDT_Created('link_created'),
            GDT_Creator('link_creator'),
        ]


