import asyncio
import http.client

from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.Message import Message
from gdo.links.GDO_Link import GDO_Link
from gdo.base.GDO import GDO
from gdo.base.Logger import Logger
from gdo.core.GDO_Channel import GDO_Channel
from gdo.links.GDO_LinkVote import GDO_LinkVote
from gdo.links.method.settings import settings
from gdo.links.url_parts import extract_urls
from gdo.links.preview import fetch_preview


class module_links(GDO_Module):

    def gdo_dependencies(self) -> list:
        return ['vote']

    def gdo_classes(self) -> list[type[GDO]]:
        return [
            GDO_Link,
            GDO_LinkVote,
        ]

    def gdo_subscribe_events(self):
        Application.EVENTS.subscribe('new_message', self.on_new_message)
        Application.EVENTS.add_timer_async(10, self.spread_pending, Application.EVENTS.FOREVER)

    def claim_pending(self):
        """Claim before sending: a best-effort attempt is made at most once."""
        db = Application.db()
        db.begin()
        try:
            link = (GDO_Link.table().select()
                    .where('link_approved=1 AND link_spreaded=0 AND link_vote_count>0')
                    .order('link_id ASC').first().for_update().exec().fetch_object())
            if link:
                link.save_val('link_spreaded', '1')
            db.commit()
            return link
        except Exception:
            db.rollback()
            raise

    async def spread_pending(self):
        if not Application.IS_DOG:
            return
        # Bound each timer pass so other Dog events keep making progress.
        for _ in range(20):
            link = self.claim_pending()
            if not link:
                break
            for channel in GDO_Channel.with_setting(settings(), 'links_abbo', '1', '0'):
                try:
                    await channel.send_text('msg_link_spread', (
                        self.notice_text(link.gdo_val('link_url'), 1024),
                        self.notice_text(link.gdo_val('link_title')),
                        self.notice_text(link.gdo_val('link_description')) or 'no description',
                        link.get_votes_total(), channel.get_trigger(), link.get_id()))
                except Exception:
                    # No retry: the spread flag records the attempt, not delivery.
                    Logger.warning('Links: one channel announcement failed')

    async def on_new_message(self, message: Message):
        # Private messages and channels without explicit consent are never collected.
        if not settings.collection_enabled(message._env_channel):
            return
        for parts in extract_urls(message._message):
            link = self.record_sighting(parts)
            if link:
                if await self.populate_preview(link, parts['url']) is False:
                    continue
                channel = message._env_channel
                # Keep untrusted metadata on one line in chat and avoid control codes.
                title = self.notice_text(link.gdo_val('link_title')) or parts['host']
                description = self.notice_text(link.gdo_val('link_description')) or 'no description'
                await channel.send_text('msg_link_detected',
                                        (title, description, channel.get_trigger(), link.get_id()))

    async def populate_preview(self, link, url):
        try:
            preview = await asyncio.wait_for(asyncio.to_thread(fetch_preview, url), timeout=8)
        except (OSError, ValueError, TimeoutError, http.client.HTTPException, UnicodeError):
            return
        if not preview:
            return
        # The fetch runs without a database transaction; re-check deletion before saving.
        current = GDO_Link.table().get_by_id(link.get_id())
        if not current or not current.gdo_value('link_approved'):
            return False
        values = {}
        if title := self.notice_text(preview.get('title'))[:192]:
            values['link_title'] = title
        if description := self.notice_text(preview.get('description'), 1024):
            values['link_description'] = description
        if values:
            current.save_vals(values)
            link.set_vals(values)

    @staticmethod
    def notice_text(value, limit=255):
        return ' '.join(''.join(c if c.isprintable() else ' ' for c in (value or '')).split())[:limit]

    def record_sighting(self, parts):
        """Serialize exact-URL deduplication, including the first insertion."""
        db = Application.db()
        table = GDO_Link.table()
        db.begin()
        try:
            db.select("SELECT module_id FROM gdo_module WHERE module_name = 'links' FOR UPDATE").fetch_row()
            existing = table.select().where(f"BINARY link_url=BINARY {table.quote(parts['url'])}").first().for_update().exec().fetch_object()
            created = None
            if existing:
                # A deleted link must stay deleted and must not accrue sightings.
                if existing.gdo_value('link_approved'):
                    existing.save_val('link_sightings', str((existing.gdo_value('link_sightings') or 0) + 1))
            else:
                created = GDO_Link.blank({'link_url': parts['url'], 'link_host': parts['host'],
                                          'link_path': parts['path'], 'link_query': parts['query'],
                                          'link_title': parts['host']}).insert()
            db.commit()
            return created
        except Exception:
            db.rollback()
            raise
