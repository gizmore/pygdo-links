from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.Message import Message
from gdo.links.GDO_Link import GDO_Link


class module_links(GDO_Module):

    def gdo_classes(self):
        return [
            GDO_Link,
        ]

    def gdo_subscribe_events(self):
        Application.EVENTS.subscribe('new_message', self.on_new_message)

    async def on_new_message(self, message: Message):
        pass
        # message._message
