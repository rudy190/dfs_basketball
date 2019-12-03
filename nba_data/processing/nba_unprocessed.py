from datetime import datetime
from ..staging.db_config import Session
from ..staging.period_starters import StagePeriodStarters
from ..staging.game_summary import StageGameSummary
from ..staging.box_scores import StageBoxScore
from ..staging.play_by_play import StagePlayByPlay
from ..staging.schedule import StageSchedule
from ..staging.season import StageSeason
from ..staging.win_prob import StageWinProb
from ..staging.shot_chart import StageShotChart
from ..staging.roster import StageRoster
from ..staging.player import StagePlayer

class UnprocessedData():
    def __init__(self, sport, season):
        self.session=Session()
        self.sport=sport
        self.season=season
        self.game_ids=set()
        self.set_unprocessed_date_count()

    def commit(self):
        self.session.commit()
        self.session.close()
        return True

    def set_unprocessed_date_count(self):
        self.unprocessed_date_count=(self.session.query(StageSchedule)
                                         .filter(StageSchedule.processed == False)
                                         .filter(StageSchedule.sport == self.sport)
                                         .filter(StageSchedule.season == self.season)
                                         .filter(StageSchedule.status_code == 200)
                                         .count())

    @property
    def dates(self):
        dates=(self.session.query(StageSchedule)
                           .filter(StageSchedule.processed == False)
                           .filter(StageSchedule.sport == self.sport)
                           .filter(StageSchedule.season == self.season)
                           .filter(StageSchedule.status_code == 200))
        for unprocessed_date in dates:
            game_ids=self.get_game_ids(unprocessed_date)
            self.update_processed_fields(unprocessed_date)
            yield unprocessed_date

    @property
    def shot_charts(self):
        shot_charts=(self.session.query(StageShotChart)
                                 .filter(StageShotChart.processed == False)
                                 .filter(StageShotChart.sport == self.sport)
                                 .filter(StageShotChart.season == self.season)
                                 .filter(StageShotChart.status_code == 200))
        for unprocessed_shot_chart in shot_charts:
            self.update_processed_fields(unprocessed_shot_chart)
            yield unprocessed_shot_chart

    @property
    def team_rosters(self):
        team_rosters=(self.session.query(StageRoster)
                                  .filter(StageRoster.processed == False)
                                  .filter(StageRoster.sport == self.sport)
                                  .filter(StageShotChart.season == self.season)
                                  .filter(StageRoster.status_code == 200))
        for unprocessed_roster in team_rosters:
            self.update_processed_fields(unprocessed_roster)
            yield unprocessed_roster

    @property
    def players(self):
        players=(self.session.query(StagePlayer)
                             .filter(StagePlayer.processed == False)
                             .filter(StagePlayer.status_code == 200))
        for unprocessed_player in players:
            self.update_processed_fields(unprocessed_player)
            yield unprocessed_player

    @property
    def game_players(self):
        players=(self.session.query(StageBoxScore,
                                    StageGameSummary)
                             .filter(StageGameSummary.game_id==StageBoxScore.game_id)
                             .filter(StageGameSummary.status_code == 200)
                             .filter(StageGameSummary.game_id.in_(self.game_ids)))
        for unprocessed_game_player in players:
            yield unprocessed_game_player

    @property
    def game_summaries(self):
        summaries=(self.session.query(StageGameSummary)
                               .filter(StageGameSummary.processed == False)
                               .filter(StageGameSummary.status_code == 200)
                               .filter(StageGameSummary.game_id.in_(self.game_ids)))
        for unprocessed_game_summary in summaries:
            self.update_processed_fields(unprocessed_game_summary)
            yield unprocessed_game_summary

    @property
    def box_scores(self):
        box_scores=(self.session.query(StageBoxScore)
                                .filter(StageBoxScore.processed == False)
                                .filter(StageBoxScore.status_code == 200)
                                .filter(StageBoxScore.game_id.in_(self.game_ids)))
        for unprocessed_box_score in box_scores:
            self.update_processed_fields(unprocessed_box_score)
            yield unprocessed_box_score

    @property
    def starters(self):
        starters=(self.session.query(StagePeriodStarters)
                              .filter(StagePeriodStarters.processed == False)
                              .filter(StagePeriodStarters.status_code == 200)
                              .filter(StagePeriodStarters.game_id.in_(self.game_ids)))
        for unprocessed_starter in starters:
            self.update_processed_fields(unprocessed_starter)
            yield unprocessed_starter

    @property
    def events(self):
        events=(self.session.query(StagePlayByPlay)
                            .filter(StagePlayByPlay.processed == False)
                            .filter(StagePlayByPlay.status_code == 200)
                            .filter(StagePlayByPlay.game_id.in_(self.game_ids)))
        for unprocessed_event in events:
            self.update_processed_fields(unprocessed_event)
            yield unprocessed_event

    @property
    def win_prob_events(self):
        win_probs=(self.session.query(StageWinProb)
                               .filter(StageWinProb.processed == False)
                               .filter(StageWinProb.status_code == 200)
                               .filter(StageWinProb.game_id.in_(self.game_ids)))
        for unprocessed_win_prob_event in win_probs:
            self.update_processed_fields(unprocessed_win_prob_event)
            yield unprocessed_win_prob_event

    def get_game_ids(self, unprocessed_date):
        game_ids = [g[2] for g in unprocessed_date.json['resultSets'][0]['rowSet']]
        if game_ids:
            self.update_game_ids(game_ids)
        return game_ids

    def update_processed_fields(self, sql_object):
        sql_object.processed = True
        sql_object.processed_date = datetime.now()
        return True

    def update_game_ids(self, game_ids):
        self.game_ids |= set(game_ids)
