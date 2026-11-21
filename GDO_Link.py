from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_String import GDT_String
from gdo.date.GDT_Created import GDT_Created
from gdo.net.GDT_Url import GDT_Url
from gdo.net.GDT_Host import GDT_Host
from gdo.core.GDT_UInt import GDT_UInt
from gdo.vote.WithVotes import WithVotes
from gdo.vote.GDT_VoteCount import GDT_VoteCount
from gdo.vote.GDT_VoteOutcome import GDT_VoteOutcome


class GDO_Link(WithVotes, GDO):

    def gdo_votes_table(self):
        from gdo.links.GDO_LinkVote import GDO_LinkVote
        return GDO_LinkVote.table()

    def gdo_vote_object_table(self):
        return GDO_Link.table()

    def gdo_cached(self) -> bool:
        return False

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('link_id'),
            GDT_String('link_title').not_null(),
            GDT_String('link_description').maxlen(1024),
            GDT_Url('link_url').not_null(),
            GDT_Host('link_host'),
            GDT_String('link_path').maxlen(1024),
            GDT_String('link_query').maxlen(1024),
            GDT_UInt('link_sightings').not_null().initial('1'),
            GDT_Bool('link_spreaded').not_null().initial('0'),
            GDT_Bool('link_approved').not_null().initial('1'),
            GDT_VoteCount('link_vote_count'),
            GDT_VoteOutcome('link_vote_score'),
            GDT_Created('link_created'),
            GDT_Creator('link_creator'),
        ]


