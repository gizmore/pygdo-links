from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Bool import GDT_Bool


class settings(Method):
    """Independent opt-ins, managed with the normal channel settings command."""

    @classmethod
    def gdo_trigger(cls):
        return 'links.settings'

    @classmethod
    def gdo_method_config_channel(cls) -> list[GDT]:
        return [GDT_Bool('links_collect').not_null().initial('0'),
                GDT_Bool('links_abbo').not_null().initial('0')]

    def gdo_execute(self):
        return self.empty()

    @classmethod
    def collection_enabled(cls, channel):
        if channel is None:
            return False
        return bool(cls().env_channel(channel).get_config_channel_value('links_collect'))
