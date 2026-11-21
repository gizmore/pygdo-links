from gdo.vote.GDO_VoteTable import GDO_VoteTable


class GDO_LinkVote(GDO_VoteTable):
    def gdo_min_vote_score(self):
        return 1

    def gdo_max_vote_score(self):
        return 1

    def gdo_votes_table(self):
        return self.table()

    def gdo_vote_object_table(self):
        from gdo.links.GDO_Link import GDO_Link
        return GDO_Link.table()
