import pandas as pd
import numpy as np
from sqlalchemy import (and_, case, cast, func, literal, or_)
from sqlalchemy.dialects.sqlite import INTEGER
from nba_data.processing.db_config import Session
from nba_data.processing.nba_game_starters import GameStarter
from nba_data.processing.date_windows import DateWindow
from nba_data.processing.nba_game_events import GameEvent
from nba_data.processing.nba_game_players import GamePlayer
from nba_data.processing.nba_game_seq import GameSequence
from nba_data.processing.nba_game_seq_starts import GameSequenceStarters
from nba_data.processing.nba_game_seq_sec import GameSequenceSec
from nba_data.processing.nba_game_on_court import GameOnCourt
from nba_data.processing.nba_game_teams import GameTeam
from nba_data.processing.nba_games import Game
from nba_data.processing.nba_player_boxes import PlayerBoxScore
from nba_data.processing.nba_team_boxes import TeamBoxScore
from nba_data.processing.nba_rosters import TeamRoster
import random

class NBASequenceObs():
    def __init__(self):
        self.matrix_num_iter = 0
        self.in_game_ts_lag_count = 20
        self.daily_ts_lag_count = 14
        self.season_ts_lag_count = 3
        self.stat_rows = {'fg2a':0, 'fg2m':1, 'fg3a':2, 'fg3m':3, 'fta':4,
                          'ftm':5, 'ast':6, 'blk':7, 'oreb':8, 'dreb':9,
                          'tov':10, 'stl':11, 'pf_off':12, 'pf_def':13,
                          'pf_def_sf':14, 'tech':15, 'flag':16, 'df':17,
                          'df_sf':18, 'df_off':19, 'violation':20,
                          'sub_out':21, 'sub_in':22, 'jump_part':23,
                          'jump_poss':24, 'ejection':25, 'fta_tech':4,
                          'ftm_tech':5, 'timeout':0}
        self.action_events = {'fg2a':0, 'fg2m':1, 'fg3a':2, 'fg3m':3, 'fta':4,
                              'ftm':5, 'ast':6, 'blk':7, 'oreb':8, 'dreb':9,
                              'tov':10, 'stl':11, 'pf_off':12, 'pf_def':13,
                              'pf_def_sf':14, 'tech':15, 'flag':16, 'df':17,
                              'df_sf':18, 'df_off':19, 'violation':20,
                              'sub_in':21, 'sub_out':21, 'jump_part':22,
                              'jump_poss':22, 'ejection':23, 'fta_tech':24,
                              'ftm_tech':25, 'timeout':26, 'period_end': 27,
                              'period_start':28, 'unsportsmanlike_foul':29}
        self.player_stats = {'fg2a':0, 'fg2m':1, 'fg3a':2, 'fg3m':3, 'fta':4,
                              'ftm':5, 'ast':6, 'blk':7, 'oreb':8, 'dreb':9,
                              'tov':10, 'stl':11, 'pf_off':12, 'pf_def':13,
                              'pf_def_sf':14, 'tech':15, 'flag':16, 'df':17,
                              'df_sf':18, 'df_off':19, 'violation':20,
                              'sub_out':21, 'sub_in':22, 'jump_part':23,
                              'jump_poss':24, 'ejection':25, 'fta_tech':4,
                              'ftm_tech':5, 'timeout':26}
        self.team_fouls = ['pf_def','pf_def_sf']
        self.team_violations = ['violation']
        self.team_timeouts = ['timeout']
        self.static_game_columns = ['game_id','matrix_num','column_num','row_num',
                                    'value']
        self.in_game_columns = ['game_id','model_event_num','matrix_num','column_num',
                                'row_num','value']

    def get_obs(self, game_id):
        self.session = Session()
        self.game_id = game_id
        self.load_static_game_features()
        self.session.close()

    def set_obs(self, game_id):
        self.session = Session()
        self.game_id = game_id
        self.set_teams()
        self.set_game_date()
        self.set_season()
        self.set_ts_game_dates()
        self.set_game_ids()
        self.set_players()
        self.set_model_events()
        self.set_starter_alias()
        self.set_static_game_features()
        self.set_static_player_features()
        self.set_shifted_on_court_query()
        self.set_in_game_on_court_seq_query()
        self.set_lagged_prior_sec_query()
        self.set_lagged_prior_event_query()
        self.set_in_game_features()
        self.set_in_game_player_features()
        self.set_in_game_team_features()
        self.set_in_game_ts_features()
        self.set_daily_ts_features()
        self.set_daily_opp_ts_features()
        self.set_season_ts_features()
        self.set_season_opp_ts_features()
        self.set_labels()
        self.set_reward_baseline()
        self.session.close()

    # def set_input_data(self):
    #     input_arrays = {}
    #     for model_event in self.model_events:
    #         static_game_features
    #         input_arrays.update({model_event: })

    def create_input_arrays(self, df):
        columns = df2['column_num'].max() + 1
        rows = df2['row_num'].max() + 1
        depth = len(df2['matrix_num'].unique())

        input_array = np.zeros((columns, rows, depth), dtype=np.float32)

        for i, matrix in enumerate(df2['matrix_num'].unique()):
            input_array[:,:,i] = df2.loc[pd.IndexSlice[:, matrix], :].unstack().values

    def set_teams(self):
        session = self.session
        team_ids_query = (session.query(GameTeam.team_id)
                                 .filter(GameTeam.game_id==self.game_id))
        self.team_ids = set(team[0] for team in team_ids_query)
        self.home_team_id = (session.query(GameTeam.team_id)
                                    .filter(GameTeam.game_id==self.game_id)
                                    .filter(GameTeam.home_away==True)
                                    .scalar())
        self.away_team_id = (session.query(GameTeam.team_id)
                                    .filter(GameTeam.game_id==self.game_id)
                                    .filter(GameTeam.home_away==False)
                                    .scalar())

    def set_season(self):
        session = self.session
        self.season = session.query(Game.season).filter(Game.game_id==self.game_id).scalar()

    def set_game_date(self):
        session = self.session
        self.game_date = session.query(Game.game_date_est).filter(Game.game_id==self.game_id).scalar()

    def set_ts_game_dates(self):
        session = self.session
        self.ts_game_dates = set(session.query(DateWindow.window_date,
                                               DateWindow.days_lag)
                                        .filter(Game.game_date_est==DateWindow.game_date_est)
                                        .filter(Game.game_id==self.game_id)
                                        .filter(DateWindow.days_lag <= self.daily_ts_lag_count)
                                        .all())

    def set_game_ids(self):
        session = self.session
        game_date_vals = set(game[0] for game in self.ts_game_dates)
        game_ids_query = (session.query(GameTeam.game_id)
                                 .filter(GameTeam.team_id.in_(self.team_ids))
                                 .filter(GameTeam.game_id==Game.game_id)
                                 .filter(Game.game_date_est.in_(game_date_vals)))
        self.game_ids = set(game[0] for game in game_ids_query)

    def set_players(self):
        session = self.session
        self.set_game_starters()
        self.set_game_bench_players()
        self.players = self.starters | self.bench
        self.players = list(self.players)
        random.shuffle(self.players)
        self.players = dict((player_id, i) for i, player_id in enumerate(self.players))

    def set_game_starters(self):
        session = self.session
        starters_query = (session.query(GameStarter.player_id)
                                 .filter(and_(GameStarter.game_id==self.game_id,
                                              GameStarter.period==1)))
        self.starters = set(player[0] for player in starters_query)
        self.starters |= self.team_ids

    def set_game_bench_players(self):
        session = self.session
        game_players = (session.query(PlayerBoxScore.player_id)
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .subquery())
        bench_query = (session.query(PlayerBoxScore.team_id,
                                     PlayerBoxScore.player_id,
                                     func.sum(PlayerBoxScore.sec).label('total_sec'))
                              .filter(PlayerBoxScore.game_id.in_(self.game_ids))
                              .filter(PlayerBoxScore.team_id.in_(self.team_ids))
                              .filter(PlayerBoxScore.player_id==game_players.c.player_id)
                              .group_by(PlayerBoxScore.team_id,
                                        PlayerBoxScore.player_id))
        self.bench = set()
        for team_id, df in pd.read_sql(bench_query.statement, session.bind).groupby(['team_id']):
            criteria = df['player_id'].isin(self.starters)
            self.bench |= set(df.loc[~criteria,]
                                .sort_values(by=['total_sec'], ascending=False)
                                .head(7)['player_id'])

    def set_model_events(self):
        session=self.session
        model_events_query = (session.query(GameSequence.model_event_num)
                                     .filter(GameSequence.game_id==self.game_id)
                                     .group_by(GameSequence.model_event_num)
                                     .order_by(GameSequence.model_event_num))
        self.model_events = list(event[0] for event in model_events_query)

    def set_starter_alias(self):
        session = self.session
        self.starter_alias = (session.query(GameStarter)
                                     .filter(GameStarter.period==1)
                                     .filter(GameStarter.game_id==self.game_id)
                                     .subquery())

    def set_static_game_features(self):
        # static features take game_id for indexing
        self.static_game_features = []
        self.set_sport_ind_features()
        self.set_season_type_ind_features()
        self.static_game_features = pd.concat(self.static_game_features,
                                              axis=0,
                                              sort=False)

    def set_sport_ind_features(self):
        sport_ind = []
        for sport in ['nba','wnba','g_lg']:
            p_criteria=(PlayerBoxScore.sport==sport)
            t_criteria=(TeamBoxScore.sport==sport)
            sport_ind.append(self.set_static_ind_matrix(p_criteria, t_criteria))
        self.sport_ind_features = pd.concat(sport_ind, axis=0, sort=False)
        self.static_game_features.append(self.sport_ind_features)

    def set_season_type_ind_features(self):
        season_type_ind = []
        p_criteria=(PlayerBoxScore.game_id.like('%021%0%'))
        t_criteria=(TeamBoxScore.game_id.like('%021%0%'))
        season_type_ind.append(self.set_static_ind_matrix(p_criteria, t_criteria))
        p_criteria=(PlayerBoxScore.game_id.like('%041%0%'))
        t_criteria=(TeamBoxScore.game_id.like('%041%0%'))
        season_type_ind.append(self.set_static_ind_matrix(p_criteria, t_criteria))
        p_criteria=(PlayerBoxScore.game_id.like('%011%0%'))
        t_criteria=(TeamBoxScore.game_id.like('%011%0%'))
        season_type_ind.append(self.set_static_ind_matrix(p_criteria, t_criteria))
        self.season_type_ind_features = pd.concat(season_type_ind, axis=0, sort=False)
        self.static_game_features.append(self.season_type_ind_features)

    def set_static_player_features(self):
        # static features take game_id for indexing
        self.static_player_features = []
        self.set_team_ind_features()
        self.set_home_ind_features()
        # self.set_favorite_ind_features()
        self.set_start_ind_features()
        self.set_period_start_pct_features()
        self.set_avg_played_pct_features()
        self.set_pos_ind_features()
        self.set_active_ind_features()
        self.static_player_features = pd.concat(self.static_player_features,
                                                axis=0,
                                                sort=False)

    def set_team_ind_features(self):
        session = self.session
        starter_alias = self.starter_alias
        player_query = (session.query(PlayerBoxScore.game_id.label('game_id'),
                                      PlayerBoxScore.player_id.label('player_id'),
                                      (GameEvent.id - 1).label('row_num'),
                                      literal(0).label('value'))
                               .select_from(PlayerBoxScore)
                               .filter(GameEvent.id <= 26)
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .filter(PlayerBoxScore.player_id.in_(self.players.keys())))
        team_query = (session.query(TeamBoxScore.game_id.label('game_id'),
                                    TeamBoxScore.team_id.label('player_id'),
                                    (GameEvent.id - 1).label('row_num'),
                                    literal(1).label('value'))
                             .filter(GameEvent.id <= 26)
                             .filter(TeamBoxScore.game_id==self.game_id)
                             .filter(TeamBoxScore.team_id.in_(self.players.keys())))
        team_ind_query=player_query.union(team_query)
        team_ind = pd.read_sql_query(team_ind_query.statement, session.bind)
        team_ind['column_num'] = team_ind['player_id'].replace(self.players)
        team_ind['matrix_num'] = self.matrix_num_iter
        self.team_ind_features=team_ind[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.static_player_features.append(self.team_ind_features)
        self.matrix_num_iter += 1

    def set_home_ind_features(self):
        p_criteria=(PlayerBoxScore.team_id==GameTeam.team_id)
        t_criteria=(TeamBoxScore.team_id==GameTeam.team_id)
        self.home_ind_features=self.set_static_ind_matrix(p_criteria, t_criteria)
        self.static_player_features.append(self.home_ind_features)

    def set_start_ind_features(self):
        starter_alias = self.starter_alias
        p_criteria = (starter_alias.c.player_id!=None)
        t_criteria = TeamBoxScore.game_id==TeamBoxScore.game_id
        self.start_ind_features=self.set_static_ind_matrix(p_criteria, t_criteria)
        self.static_player_features.append(self.start_ind_features)

    def set_period_start_pct_features(self):
        session = self.session
        min_max_period=self.get_min_max_periods().subquery()
        player_starter=self.get_player_period_starters(min_max_period)
        team_starter=self.get_team_period_starters( min_max_period)
        total_team_games=team_starter.subquery()
        starter_query=player_starter.union(team_starter).subquery()
        starter_query = (session.query(starter_query.c.player_id.label('player_id'),
                                       (GameEvent.id - 1).label('row_num'),
                                       starter_query.c.period.label('period'),
                                       starter_query.c.start_ind.label('player_starts'),
                                       total_team_games.c.start_ind.label('all_starts'),
                                       ((starter_query.c.start_ind * 1.0) /
                                         total_team_games.c.start_ind).label('value'))
                                .select_from(starter_query)
                                .outerjoin(total_team_games,
                                           and_(starter_query.c.team_id==total_team_games.c.team_id,
                                                starter_query.c.period==total_team_games.c.period))
                                .filter(GameEvent.id <= 26)
                                .filter(starter_query.c.player_id!=None))
        self.period_start_pct_features = pd.read_sql_query(starter_query.statement, session.bind)
        self.period_start_pct_features['game_id'] = self.game_id
        self.period_start_pct_features['column_num'] = (self.period_start_pct_features['player_id']
                                                            .replace(self.players))
        self.period_start_pct_features['matrix_num'] = ((self.period_start_pct_features['period'] - 1)
                                                        + self.matrix_num_iter)
        self.period_start_pct_features = self.period_start_pct_features.drop(['period','player_starts','all_starts'], axis=1)
        self.period_start_pct_features=self.period_start_pct_features[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.static_player_features.append(self.period_start_pct_features)
        self.matrix_num_iter += 5

    def set_avg_played_pct_features(self):
        session = self.session
        player_sec_played_query = (session.query(PlayerBoxScore.game_id.label('game_id'),
                                               PlayerBoxScore.team_id.label('team_id'),
                                               PlayerBoxScore.player_id.label('player_id'),
                                               (PlayerBoxScore.sec * 1.0).label('total_sec'))
                                        .filter(and_(PlayerBoxScore.game_id.in_(self.game_ids),
                                                     PlayerBoxScore.player_id.in_(self.players.keys()))))
        team_sec_played_query = (session.query(TeamBoxScore.game_id.label('game_id'),
                                               TeamBoxScore.team_id.label('team_id'),
                                               TeamBoxScore.team_id.label('player_id'),
                                               (TeamBoxScore.sec * 1.0 / 5).label('total_sec'))
                                        .filter(and_(TeamBoxScore.game_id.in_(self.game_ids),
                                                     TeamBoxScore.team_id.in_(self.players.keys()))))
        sec_played_query = player_sec_played_query.union(team_sec_played_query).subquery()
        total_team_sec_played = team_sec_played_query.subquery()
        sec_played_query = (session.query(sec_played_query.c.game_id,
                                          sec_played_query.c.player_id.label('player_id'),
                                          (sec_played_query.c.total_sec /
                                           total_team_sec_played.c.total_sec).label('played_pct'))
                                   .select_from(sec_played_query)
                                   .join(total_team_sec_played,
                                         and_(sec_played_query.c.game_id==total_team_sec_played.c.game_id,
                                              sec_played_query.c.team_id==total_team_sec_played.c.team_id))
                                   .subquery())
        player_avg_played_pct = (session.query(sec_played_query.c.player_id.label('player_id'),
                                               func.avg(sec_played_query.c.played_pct).label('value'))
                                        .group_by(sec_played_query.c.player_id)
                                        .subquery())
        player_avg_played_pct = (session.query(player_avg_played_pct.c.player_id,
                                               player_avg_played_pct.c.value,
                                               (GameEvent.id - 1).label('row_num'))
                                        .filter(GameEvent.id <= 26))
        self.avg_played_pct_features = pd.read_sql_query(player_avg_played_pct.statement,
                                                         session.bind)
        self.avg_played_pct_features['game_id'] = self.game_id
        self.avg_played_pct_features['column_num'] = (self.avg_played_pct_features['player_id']
                                                          .replace(self.players))
        self.avg_played_pct_features['matrix_num'] = self.matrix_num_iter
        self.avg_played_pct_features=self.avg_played_pct_features[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.static_player_features.append(self.avg_played_pct_features)
        self.matrix_num_iter += 1

    def set_pos_ind_features(self):
        pos_ind = []
        for position in ['G','F','C']:
            p_criteria=(TeamRoster.position.contains(position))
            t_criteria=(TeamBoxScore.game_id!=TeamBoxScore.game_id)
            pos_ind.append(self.set_static_ind_matrix(p_criteria, t_criteria))
        self.pos_ind_features = pd.concat(pos_ind, axis=0, sort=False)
        self.static_player_features.append(self.pos_ind_features)

    def set_active_ind_features(self):
        session = self.session
        player_criteria = (GamePlayer.inactive==False)
        player_query = (session.query(PlayerBoxScore.game_id.label('game_id'),
                                      PlayerBoxScore.player_id.label('player_id'),
                                      (GameEvent.id - 1).label('row_num'),
                                      case([(player_criteria, 1)],
                                           else_=0).label('value'))
                               .select_from(PlayerBoxScore)
                               .outerjoin(GamePlayer,
                                          and_(PlayerBoxScore.game_id==GamePlayer.game_id,
                                               PlayerBoxScore.team_id==GamePlayer.team_id,
                                               PlayerBoxScore.player_id==GamePlayer.player_id))
                               .filter(GameEvent.id <= 26)
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .filter(PlayerBoxScore.player_id.in_(self.players.keys()))
                               .filter(GamePlayer.game_id==self.game_id)
                               .filter(GamePlayer.player_id.in_(self.players.keys())))
        team_query = (session.query(TeamBoxScore.game_id.label('game_id'),
                                    TeamBoxScore.team_id.label('player_id'),
                                    (GameEvent.id - 1).label('row_num'),
                                    literal(1).label('value'))
                             .filter(GameEvent.id <= 26)
                             .filter(TeamBoxScore.game_id==self.game_id)
                             .filter(TeamBoxScore.team_id.in_(self.players.keys())))
        active_ind_query=player_query.union(team_query)
        active_ind = pd.read_sql_query(active_ind_query.statement,
                                            session.bind)
        active_ind['column_num'] = active_ind['player_id'].replace(self.players)
        active_ind['matrix_num'] = self.matrix_num_iter
        self.active_ind_features=active_ind[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.static_player_features.append(self.active_ind_features)
        self.matrix_num_iter += 1

    def set_static_ind_matrix(self, player_criteria, team_criteria):
        session = self.session
        starter_alias = self.starter_alias
        player_query = (session.query(PlayerBoxScore.game_id.label('game_id'),
                                      PlayerBoxScore.player_id.label('player_id'),
                                      (GameEvent.id - 1).label('row_num'),
                                      case([(player_criteria, 1)],
                                           else_=0).label('value'))
                               .select_from(PlayerBoxScore)
                               .outerjoin(starter_alias,
                                          and_(PlayerBoxScore.game_id==starter_alias.c.game_id,
                                               PlayerBoxScore.player_id==starter_alias.c.player_id))
                               .outerjoin(TeamRoster,
                                          and_(PlayerBoxScore.team_id==TeamRoster.team_id,
                                               PlayerBoxScore.player_id==TeamRoster.player_id))
                               .filter(GameEvent.id <= 26)
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .filter(PlayerBoxScore.player_id.in_(self.players.keys()))
                               .filter(GameTeam.game_id==self.game_id)
                               .filter(GameTeam.home_away==True))
        team_query = (session.query(TeamBoxScore.game_id.label('game_id'),
                                    TeamBoxScore.team_id.label('player_id'),
                                    (GameEvent.id - 1).label('row_num'),
                                    case([(team_criteria, 1)],
                                         else_=0).label('value'))
                             .filter(GameEvent.id <= 26)
                             .filter(TeamBoxScore.game_id==self.game_id)
                             .filter(TeamBoxScore.team_id.in_(self.players.keys()))
                             .filter(GameTeam.game_id==self.game_id)
                             .filter(GameTeam.home_away==True))
        static_game_ind_query=player_query.union(team_query)
        static_game_ind = pd.read_sql_query(static_game_ind_query.statement,
                                            session.bind)
        static_game_ind['column_num'] = static_game_ind['player_id'].replace(self.players)
        static_game_ind['matrix_num'] = self.matrix_num_iter
        static_game_ind = static_game_ind[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.matrix_num_iter += 1
        return static_game_ind

    def get_min_max_periods(self):
        session = self.session
        min_max_period=(session.query(GameStarter.game_id,
                                      func.max(GameStarter.period).label('max_period'))
                               .filter(GameStarter.game_id.in_(self.game_ids))
                               .group_by(GameStarter.game_id))
        return min_max_period

    def get_player_period_starters(self, min_max_period):
        session = self.session
        player_starter=(session.query(min_max_period.c.game_id.label('game_id'),
                                      PlayerBoxScore.player_id.label('player_id'),
                                      PlayerBoxScore.team_id.label('team_id'),
                                      GameEvent.id.label('period'))
                               .filter(GameEvent.id>=1)
                               .filter(GameEvent.id<=min_max_period.c.max_period)
                               .filter(PlayerBoxScore.player_id.in_(self.players.keys()))
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .subquery())
        player_starter=(session.query(case([(player_starter.c.period < 5, player_starter.c.period)],
                                           else_=5).label('period'),
                                      player_starter.c.player_id.label('player_id'),
                                      player_starter.c.team_id.label('team_id'),
                                      case([(GameStarter.period!=None, 1)],
                                           else_=0).label('start_ind'))
                               .select_from(player_starter)
                               .outerjoin(GameStarter,
                                          and_(player_starter.c.game_id==GameStarter.game_id,
                                               player_starter.c.period==GameStarter.period,
                                               player_starter.c.team_id==GameStarter.team_id,
                                               player_starter.c.player_id==GameStarter.player_id))
                               .filter(player_starter.c.player_id!=None)
                               .subquery())
        player_starter=(session.query(player_starter.c.player_id.label('player_id'),
                                      player_starter.c.team_id.label('team_id'),
                                      player_starter.c.period.label('period'),
                                      func.sum(player_starter.c.start_ind).label('start_ind'))
                               .group_by(player_starter.c.player_id,
                                         player_starter.c.team_id,
                                         player_starter.c.period))
        return player_starter

    def get_team_period_starters(self, min_max_period):
        session = self.session
        team_starter=(session.query(min_max_period.c.game_id,
                                    TeamBoxScore.team_id.label('player_id'),
                                    TeamBoxScore.team_id.label('team_id'),
                                    case([(GameEvent.id < 5, GameEvent.id)],
                                         else_=5).label('period'),
                                    literal(1).label('start_ind'))
                               .filter(TeamBoxScore.game_id==self.game_id)
                               .filter(GameEvent.id>=1)
                               .filter(GameEvent.id<=min_max_period.c.max_period)
                               .filter(TeamBoxScore.team_id.in_(self.players.keys()))
                               .subquery())
        team_starter=(session.query(team_starter.c.player_id.label('player_id'),
                                    team_starter.c.team_id.label('team_id'),
                                    team_starter.c.period.label('period'),
                                    func.sum(team_starter.c.start_ind).label('start_ind'))
                             .group_by(team_starter.c.player_id,
                                       team_starter.c.team_id,
                                       team_starter.c.period))
        return team_starter

    def set_in_game_features(self):
        # in game features take both game_id and model_event_num for indexing
        self.in_game_features = []
        self.set_period_ind_features()
        self.set_period_pct_remain_feature()
        self.set_game_score_margin_feature()
        self.set_offensive_ind_feature()
        self.set_on_court_ind_feature()
        # self.set_event_sec_elapsed_feature()
        self.set_prior_event_period_start_ind_feature()
        self.set_prior_event_timeout_ind_feature()
        self.in_game_features = pd.concat(self.in_game_features,
                                          axis=0,
                                          sort=False)

    def set_period_ind_features(self):
        period_ind = []
        for period in range(1, 6):
            if period < 5:
                p_criteria=(GameSequence.period==period)
                t_criteria=(GameSequence.period==period)
            elif period == 5:
                p_criteria=(GameSequence.period>=period)
                t_criteria=(GameSequence.period>=period)
            period_ind.append(self.set_in_game_ind_matrix(p_criteria, t_criteria))
        self.period_ind_features = pd.concat(period_ind, axis=0, sort=False)
        self.in_game_features.append(self.period_ind_features)

    def set_period_pct_remain_feature(self):
        session = self.session
        total_per_sec = (session.query(GameSequence.game_id.label('game_id'),
                                       GameSequence.period.label('period'),
                                       func.max(GameSequence.sec_remain).label('total_sec'))
                                .filter(GameSequence.game_id==self.game_id)
                                .group_by(GameSequence.game_id,
                                          GameSequence.period)
                                .subquery())
        player_query = (session.query(GameSequence.game_id.label('game_id'),
                                      GameSequence.model_event_num.label('model_event_num'),
                                      PlayerBoxScore.player_id.label('player_id'),
                                      (GameEvent.id - 1).label('row_num'),
                                      (GameSequence.sec_remain / total_per_sec.c.total_sec).label('value'))
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .filter(GameSequence.game_id==self.game_id)
                               .filter(and_(GameSequence.game_id==total_per_sec.c.game_id,
                                            GameSequence.period==total_per_sec.c.period))
                               .filter(GameEvent.id <= 26)
                               .filter(PlayerBoxScore.player_id.in_(self.players.keys()))
                               .group_by(GameSequence.game_id,
                                         GameSequence.model_event_num,
                                         PlayerBoxScore.player_id,
                                         GameEvent.id))
        team_query = (session.query(GameSequence.game_id.label('game_id'),
                                    GameSequence.model_event_num.label('model_event_num'),
                                    TeamBoxScore.team_id.label('player_id'),
                                    (GameEvent.id - 1).label('row_num'),
                                    (GameSequence.sec_remain / total_per_sec.c.total_sec).label('value'))
                             .filter(TeamBoxScore.game_id==self.game_id)
                             .filter(GameSequence.game_id==self.game_id)
                             .filter(and_(GameSequence.game_id==total_per_sec.c.game_id,
                                          GameSequence.period==total_per_sec.c.period))
                             .filter(GameEvent.id <= 26)
                             .filter(TeamBoxScore.team_id.in_(self.players.keys()))
                             .group_by(GameSequence.game_id,
                                       GameSequence.model_event_num,
                                       TeamBoxScore.team_id,
                                       GameEvent.id))
        period_pct_remain_feature=player_query.union(team_query)
        period_pct_remain_feature = pd.read_sql_query(period_pct_remain_feature.statement,
                                                      session.bind)
        period_pct_remain_feature['column_num'] = period_pct_remain_feature['player_id'].replace(self.players)
        period_pct_remain_feature['matrix_num'] = self.matrix_num_iter
        self.period_pct_remain_feature=period_pct_remain_feature[self.in_game_columns].set_index(self.in_game_columns[:5])
        self.in_game_features.append(self.period_pct_remain_feature)
        self.matrix_num_iter += 1

    def set_game_score_margin_feature(self):
        session = self.session
        player_query = (session.query(GameSequence.game_id.label('game_id'),
                                      GameSequence.model_event_num.label('model_event_num'),
                                      PlayerBoxScore.player_id.label('player_id'),
                                      (GameEvent.id - 1).label('row_num'),
                                      case([(PlayerBoxScore.team_id==GameSequence.home_team_id,
                                             GameSequence.home_pts - GameSequence.away_pts),
                                            (PlayerBoxScore.team_id==GameSequence.away_team_id,
                                             GameSequence.away_pts - GameSequence.home_pts)],
                                           else_=0).label('value'))
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .filter(GameSequence.game_id==self.game_id)
                               .filter(GameEvent.id <= 26)
                               .filter(PlayerBoxScore.player_id.in_(self.players.keys()))
                               .group_by(GameSequence.game_id,
                                         GameSequence.model_event_num,
                                         PlayerBoxScore.player_id,
                                         GameEvent.id))
        team_query = (session.query(GameSequence.game_id.label('game_id'),
                                    GameSequence.model_event_num.label('model_event_num'),
                                    TeamBoxScore.team_id.label('player_id'),
                                    (GameEvent.id - 1).label('row_num'),
                                    case([(TeamBoxScore.team_id==GameSequence.home_team_id,
                                           GameSequence.home_pts - GameSequence.away_pts),
                                          (TeamBoxScore.team_id==GameSequence.away_team_id,
                                           GameSequence.away_pts - GameSequence.home_pts)],
                                         else_=0).label('value'))
                               .filter(TeamBoxScore.game_id==self.game_id)
                               .filter(GameSequence.game_id==self.game_id)
                               .filter(GameEvent.id <= 26)
                               .filter(TeamBoxScore.team_id.in_(self.players.keys()))
                               .group_by(GameSequence.game_id,
                                         GameSequence.model_event_num,
                                         TeamBoxScore.team_id,
                                         GameEvent.id))
        game_score_margin_query=player_query.union(team_query)
        game_score_margin_feature = pd.read_sql_query(game_score_margin_query.statement,
                                                      session.bind)
        game_score_margin_feature['column_num'] = game_score_margin_feature['player_id'].replace(self.players)
        game_score_margin_feature['matrix_num'] = self.matrix_num_iter
        self.game_score_margin_feature=game_score_margin_feature[self.in_game_columns].set_index(self.in_game_columns[:5])
        self.in_game_features.append(self.game_score_margin_feature)
        self.matrix_num_iter += 1

    def set_offensive_ind_feature(self):
        p_criteria=(or_(and_(GameSequence.home_poss==1,
                             PlayerBoxScore.team_id==GameSequence.home_team_id),
                        and_(GameSequence.away_poss==1,
                             PlayerBoxScore.team_id==GameSequence.away_team_id)))
        t_criteria=(or_(and_(GameSequence.home_poss==1,
                             TeamBoxScore.team_id==GameSequence.home_team_id),
                        and_(GameSequence.away_poss==1,
                             TeamBoxScore.team_id==GameSequence.away_team_id)))
        self.offensive_ind_feature=self.set_in_game_ind_matrix(p_criteria, t_criteria)
        self.in_game_features.append(self.offensive_ind_feature)

    def set_lagged_prior_sec_query(self):
        session = self.session
        AliasGameSequenceSec = (session.query(GameSequenceSec.game_id.label('game_id'),
                                              GameSequenceSec.model_event_num.label('model_event_num'),
                                              GameSequenceSec.clipped_sec_elapsed.label('sec_elapsed'))
                                       .filter(GameSequenceSec.game_id==self.game_id)
                                       .group_by(GameSequenceSec.game_id,
                                                 GameSequenceSec.model_event_num)
                                       .subquery())
        self.lagged_prior_sec_query = (session.query(GameSequence.game_id.label('game_id'),
                                                     GameSequence.model_event_num.label('model_event_num'),
                                                     func.max(AliasGameSequenceSec.c.model_event_num).label('lag_event_num'),
                                                     AliasGameSequenceSec.c.sec_elapsed.label('sec_elapsed'))
                                              .filter(GameSequence.game_id==self.game_id)
                                              .filter(GameSequence.game_id==AliasGameSequenceSec.c.game_id)
                                              .filter(GameSequence.model_event_num>AliasGameSequenceSec.c.model_event_num)
                                              .group_by(GameSequence.game_id,
                                                        GameSequence.model_event_num))

    def set_event_sec_elapsed_feature(self):
        session = self.session
        self.event_sec_elapsed_feature = []
        lagged_events = self.lagged_prior_sec_query.subquery()
        sec_elapsed_query = (session.query(GameSequence.game_id.label('game_id'),
                                           GameSequence.model_event_num.label('model_event_num'),
                                           case([(lagged_events.c.sec_elapsed==None, 0)],
                                                else_=lagged_events.c.sec_elapsed).label('column_num'),
                                           (GameEvent.id - 1).label('row_num'),
                                           case([(lagged_events.c.sec_elapsed==None, 0)],
                                                else_=1).label('value'))
                               .select_from(GameSequence)
                               .outerjoin(lagged_events,
                                          and_(GameSequence.game_id==lagged_events.c.game_id,
                                               GameSequence.model_event_num==lagged_events.c.model_event_num))
                               .filter(GameSequence.game_id==self.game_id)
                               .filter(GameEvent.id <= 26)
                               .group_by(GameSequence.game_id,
                                         GameSequence.model_event_num,
                                         GameEvent.id))
        event_sec_elapsed_feature = pd.read_sql_query(sec_elapsed_query.statement, session.bind)
        event_sec_elapsed_feature['matrix_num'] = self.matrix_num_iter
        self.event_sec_elapsed_feature = event_sec_elapsed_feature[self.in_game_columns].set_index(self.in_game_columns[:5])
        self.in_game_features.append(self.event_sec_elapsed_feature)
        self.matrix_num_iter += 1

    def set_prior_event_period_start_ind_feature(self):
        lagged_events = self.lagged_prior_event_query
        p_criteria=(lagged_events.c.action_category=='period_start')
        t_criteria=(lagged_events.c.action_category=='period_start')
        self.prior_event_period_start_ind_feature=self.set_prior_event_ind_feature(p_criteria, t_criteria)
        self.in_game_features.append(self.prior_event_period_start_ind_feature)

    def set_prior_event_timeout_ind_feature(self):
        lagged_events = self.lagged_prior_event_query
        p_criteria=(lagged_events.c.action_category=='timeout')
        t_criteria=(lagged_events.c.action_category=='timeout')
        self.prior_event_timeout_ind_feature=self.set_prior_event_ind_feature(p_criteria, t_criteria)
        self.in_game_features.append(self.prior_event_timeout_ind_feature)

    def set_shifted_on_court_query(self):
        session = self.session
        max_model_event = (session.query(func.max(GameOnCourt.model_event_num))
                                  .filter(GameOnCourt.game_id==self.game_id)
                                  .scalar())
        first_event_on_court_query = (session.query(GameOnCourt.game_id.label('game_id'),
                                                    GameOnCourt.model_event_num.label('model_event_num'),
                                                    GameOnCourt.player_id.label('player_id'),
                                                    GameOnCourt.on_court_ind.label('on_court_ind'))
                                             .filter(GameOnCourt.game_id==self.game_id)
                                             .filter(GameOnCourt.model_event_num==1))
        shifted_on_court_query = (session.query(GameOnCourt.game_id.label('game_id'),
                                                (GameOnCourt.model_event_num + 1).label('model_event_num'),
                                                GameOnCourt.player_id.label('player_id'),
                                                GameOnCourt.on_court_ind.label('on_court_ind'))
                                         .filter(GameOnCourt.game_id==self.game_id)
                                         .filter(GameOnCourt.model_event_num<max_model_event))
        self.shifted_on_court_query = first_event_on_court_query.union(shifted_on_court_query).subquery()

    def set_in_game_on_court_seq_query(self):
        session = self.session
        shifted_on_court = self.shifted_on_court_query
        seq_players_query = (session.query(GameSequence.game_id.label('game_id'),
                                           GameSequence.model_event_num.label('model_event_num'),
                                           PlayerBoxScore.player_id.label('player_id'))
                                    .filter(GameSequence.game_id==self.game_id)
                                    .filter(PlayerBoxScore.game_id==self.game_id)
                                    .filter(PlayerBoxScore.game_id==GameSequence.game_id)
                                    .filter(PlayerBoxScore.player_id.in_(self.players.keys()))
                                    .group_by(GameSequence.game_id,
                                              GameSequence.model_event_num,
                                              PlayerBoxScore.player_id)
                                    .subquery())
        self.in_game_on_court_seq_query = (session.query(seq_players_query.c.game_id.label('game_id'),
                                                         seq_players_query.c.model_event_num.label('model_event_num'),
                                                         seq_players_query.c.player_id.label('player_id'),
                                                         shifted_on_court.c.on_court_ind.label('on_court_ind'))
                                                  .select_from(seq_players_query)
                                                  .outerjoin(shifted_on_court,
                                                             and_(seq_players_query.c.game_id==shifted_on_court.c.game_id,
                                                                  seq_players_query.c.model_event_num==shifted_on_court.c.model_event_num,
                                                                  seq_players_query.c.player_id==shifted_on_court.c.player_id))
                                                  .filter(seq_players_query.c.game_id!=None)
                                                  .subquery())

    def set_on_court_ind_feature(self):
        session = self.session
        game_seq_query = self.in_game_on_court_seq_query
        player_query = (session.query(game_seq_query.c.game_id.label('game_id'),
                                      game_seq_query.c.model_event_num.label('model_event_num'),
                                      game_seq_query.c.player_id.label('player_id'),
                                      (GameEvent.id - 1).label('row_num'),
                                      case([(game_seq_query.c.on_court_ind==None, 0)],
                                           else_=1).label('value'))
                               .filter(GameEvent.id <= 26))
        team_query = (session.query(GameSequence.game_id.label('game_id'),
                                    GameSequence.model_event_num.label('model_event_num'),
                                    TeamBoxScore.team_id.label('player_id'),
                                    (GameEvent.id - 1).label('row_num'),
                                    literal(1).label('value'))
                             .filter(GameSequence.game_id==TeamBoxScore.game_id)
                             .filter(GameEvent.id <= 26)
                             .filter(GameSequence.game_id==self.game_id)
                             .filter(TeamBoxScore.team_id.in_(self.players.keys()))
                             .group_by(GameSequence.game_id,
                                       GameSequence.model_event_num,
                                       TeamBoxScore.team_id,
                                       GameEvent.id))
        in_game_ind_query=player_query.union(team_query)
        in_game_ind = pd.read_sql_query(in_game_ind_query.statement,
                                        session.bind)
        in_game_ind['column_num'] = in_game_ind['player_id'].replace(self.players)
        in_game_ind['matrix_num'] = self.matrix_num_iter
        self.on_court_ind_feature=in_game_ind[self.in_game_columns].set_index(self.in_game_columns[:5])
        self.in_game_features.append(self.on_court_ind_feature)
        self.matrix_num_iter += 1
        return in_game_ind

    def set_in_game_ind_matrix(self, player_criteria, team_criteria):
        session = self.session
        player_query = (session.query(GameSequence.game_id.label('game_id'),
                                      GameSequence.model_event_num.label('model_event_num'),
                                      PlayerBoxScore.player_id.label('player_id'),
                                      (GameEvent.id - 1).label('row_num'),
                                      case([(player_criteria, 1)],
                                           else_=0).label('value'))
                               .filter(GameEvent.id <= 26)
                               .filter(GameSequence.game_id==self.game_id)
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .filter(PlayerBoxScore.player_id.in_(self.players.keys()))
                               .filter(PlayerBoxScore.game_id==GameSequence.game_id)
                               .group_by(GameSequence.game_id,
                                         GameSequence.model_event_num,
                                         GameEvent.id,
                                         PlayerBoxScore.player_id))
        team_query = (session.query(GameSequence.game_id.label('game_id'),
                                    GameSequence.model_event_num.label('model_event_num'),
                                    TeamBoxScore.team_id.label('player_id'),
                                    (GameEvent.id - 1).label('row_num'),
                                    case([(team_criteria, 1)],
                                         else_=0).label('value'))
                             .filter(GameEvent.id <= 26)
                             .filter(GameSequence.game_id==self.game_id)
                             .filter(TeamBoxScore.game_id==self.game_id)
                             .filter(TeamBoxScore.team_id.in_(self.players.keys()))
                             .filter(TeamBoxScore.game_id==GameSequence.game_id)
                             .group_by(GameSequence.game_id,
                                       GameSequence.model_event_num,
                                       GameEvent.id,
                                       TeamBoxScore.team_id))
        in_game_ind_query=player_query.union(team_query)
        in_game_ind = pd.read_sql_query(in_game_ind_query.statement,
                                        session.bind)
        in_game_ind['column_num'] = in_game_ind['player_id'].replace(self.players)
        in_game_ind['matrix_num'] = self.matrix_num_iter
        index_columns = ['game_id','matrix_num','row_num','column_num']
        in_game_ind=in_game_ind[self.in_game_columns].set_index(self.in_game_columns[:5])
        self.matrix_num_iter += 1
        return in_game_ind

    def set_lagged_prior_event_query(self):
        session = self.session
        AliasGameSequence = (session.query(GameSequence.game_id.label('game_id'),
                                           GameSequence.model_event_num.label('model_event_num'),
                                           GameSequence.action_category.label('action_category'))
                                    .filter(GameSequence.game_id==self.game_id)
                                    .subquery())
        self.lagged_prior_event_query = (session.query(GameSequence.game_id.label('game_id'),
                                                       GameSequence.model_event_num.label('model_event_num'),
                                                       func.max(AliasGameSequence.c.model_event_num).label('lag_event_num'),
                                                       AliasGameSequence.c.action_category.label('action_category'))
                                                .filter(GameSequence.game_id==AliasGameSequence.c.game_id)
                                                .filter(GameSequence.model_event_num>AliasGameSequence.c.model_event_num)
                                                .group_by(GameSequence.game_id,
                                                          GameSequence.model_event_num)
                                                .subquery())

    def set_prior_event_ind_feature(self, player_criteria, team_criteria):
        session = self.session
        lagged_events = self.lagged_prior_event_query
        player_query = (session.query(GameSequence.game_id.label('game_id'),
                                      GameSequence.model_event_num.label('model_event_num'),
                                      PlayerBoxScore.player_id.label('player_id'),
                                      (GameEvent.id - 1).label('row_num'),
                                      case([(player_criteria, 1)],
                                           else_=0).label('value'))
                               .select_from(GameSequence)
                               .outerjoin(lagged_events,
                                          and_(GameSequence.game_id==lagged_events.c.game_id,
                                               GameSequence.model_event_num==lagged_events.c.model_event_num))
                               .filter(GameEvent.id <= 26)
                               .filter(GameSequence.game_id==self.game_id)
                               .filter(PlayerBoxScore.game_id==self.game_id)
                               .filter(PlayerBoxScore.player_id.in_(self.players.keys()))
                               .group_by(GameSequence.game_id,
                                         GameSequence.model_event_num,
                                         PlayerBoxScore.player_id,
                                         GameEvent.id))
        team_query = (session.query(GameSequence.game_id.label('game_id'),
                                    GameSequence.model_event_num.label('model_event_num'),
                                    TeamBoxScore.team_id.label('player_id'),
                                    (GameEvent.id - 1).label('row_num'),
                                    case([(team_criteria, 1)],
                                         else_=0).label('value'))
                             .select_from(GameSequence)
                             .outerjoin(lagged_events,
                                        and_(GameSequence.game_id==lagged_events.c.game_id,
                                             GameSequence.model_event_num==lagged_events.c.model_event_num))
                             .filter(GameEvent.id <= 26)
                             .filter(GameSequence.game_id==self.game_id)
                             .filter(TeamBoxScore.game_id==self.game_id)
                             .filter(TeamBoxScore.team_id.in_(self.players.keys()))
                             .group_by(GameSequence.game_id,
                                       GameSequence.model_event_num,
                                       TeamBoxScore.team_id,
                                       GameEvent.id))
        prior_event_ind_query=player_query.union(team_query)
        prior_event_ind = pd.read_sql_query(prior_event_ind_query.statement,
                                            session.bind)
        prior_event_ind['column_num'] = prior_event_ind['player_id'].replace(self.players)
        prior_event_ind['matrix_num'] = self.matrix_num_iter
        prior_event_ind=prior_event_ind[self.in_game_columns].set_index(self.in_game_columns[:5])
        self.matrix_num_iter += 1
        return prior_event_ind

    def set_in_game_player_features(self):
        session = self.session
        in_game_features_query = (session.query(GameSequence.game_id.label('game_id'),
                                                (GameSequence.model_event_num + 1).label('model_event_num'),
                                                GameSequence.player_id.label('player_id'),
                                                GameSequence.action_category.label('action'),
                                                literal(1).label('value'))
                                         .filter(GameSequence.game_id==self.game_id)
                                         .filter(GameSequence.player_id.in_(self.players.keys()))
                                         .filter(GameSequence.model_event_num<=max(self.model_events))
                                         .filter(GameSequence.action_category.in_(self.stat_rows.keys())))
        in_game_player_features = pd.read_sql_query(in_game_features_query.statement,
                                                    session.bind)
        in_game_player_features['row_num'] = (
                        in_game_player_features['action'].replace(self.stat_rows))
        in_game_player_features = in_game_player_features.drop(['action'], axis=1)
        index_columns=['game_id','model_event_num','player_id','row_num']
        in_game_player_features = in_game_player_features.set_index(index_columns)
        in_game_player_features = (in_game_player_features.unstack(-2).unstack()
                                                          .fillna(0).astype('int')
                                                          .cumsum()
                                                          .stack(-2).stack()
                                                          .reset_index())
        in_game_player_features['matrix_num'] = self.matrix_num_iter
        in_game_player_features['column_num'] = (
          in_game_player_features['player_id'].replace(self.players))
        index_columns=['game_id','model_event_num','matrix_num','column_num','row_num']
        in_game_player_features = in_game_player_features.set_index(index_columns)
        new_index = pd.MultiIndex.from_product([in_game_player_features.index.levels[0],
                                                pd.Index(self.model_events),
                                                in_game_player_features.index.levels[2],
                                                pd.Index(range(0,26)),
                                                pd.Index(range(0,26))],
                                               names=index_columns)
        in_game_player_features = (in_game_player_features.reindex(new_index, fill_value=0)
                                                          .reset_index())
        self.in_game_player_features = in_game_player_features[self.in_game_columns].set_index(self.in_game_columns[:5])
        self.matrix_num_iter += 1

    def set_in_game_team_features(self):
        self.in_game_team_features = []
        self.in_game_team_foul_features = self.set_in_game_team_matrix(self.team_fouls)
        self.in_game_team_viol_features = self.set_in_game_team_matrix(self.team_violations)
        self.in_game_team_to_features = self.set_in_game_team_matrix(self.team_timeouts)
        self.in_game_team_features = pd.concat(self.in_game_team_features,
                                               axis=0,
                                               sort=False)

    def set_in_game_team_matrix(self, action_categories):
        session = self.session
        team_features_in_game = []
        for team_id in [self.home_team_id, self.away_team_id]:
            in_game_features_query = (session.query(GameSequence.game_id.label('game_id'),
                                                    (GameSequence.model_event_num + 1).label('model_event_num'),
                                                    literal(self.matrix_num_iter).label('matrix_num'),
                                                    func.count(GameSequence.action_category).label('value'))
                                             .filter(GameSequence.game_id==self.game_id)
                                             .filter(GameSequence.team_id==team_id)
                                             .filter(GameSequence.model_event_num<=max(self.model_events))
                                             .filter(GameSequence.action_category.in_(action_categories))
                                             .group_by(GameSequence.game_id,
                                                       GameSequence.model_event_num)
                                             .order_by(GameSequence.game_id,
                                                       GameSequence.model_event_num))
            in_game_team_features = pd.read_sql_query(in_game_features_query.statement,
                                                      session.bind)
            index_columns=['game_id','model_event_num','matrix_num']
            in_game_team_features = in_game_team_features.set_index(index_columns)
            in_game_team_features['value'] = in_game_team_features['value'].cumsum()
            index_columns=['game_id','model_event_num','matrix_num','column_num','row_num']
            new_index = pd.MultiIndex.from_product([in_game_team_features.index.levels[0],
                                                    pd.Index(self.model_events),
                                                    in_game_team_features.index.levels[2],
                                                    pd.Index(range(0,26)),
                                                    pd.Index(range(0,26))],
                                                   names=index_columns)
            in_game_team_features = (in_game_team_features.reindex(new_index, fill_value=None)
                                                          .reset_index())
            in_game_team_features['value'] = (in_game_team_features['value'].fillna(method='ffill')
                                                                            .fillna(0))
            team_features_in_game.append(in_game_team_features[self.in_game_columns].set_index(self.in_game_columns[:5]))
            self.matrix_num_iter += 1
        team_features_in_game = pd.concat(team_features_in_game, axis=0)
        self.in_game_team_features.append(team_features_in_game)
        return team_features_in_game

    def set_in_game_ts_features(self):
        session = self.session
        lag_event_lb = GameSequence.model_event_num - (self.in_game_ts_lag_count * 2)
        in_game_ts_features = []
        lagged_events = (session.query(GameSequence.game_id.label('game_id'),
                                       GameSequence.model_event_num.label('model_event_num'),
                                       GameSequence.player_id.label('player_id'),
                                       GameSequence.action_category.label('action'))
                                .filter(GameSequence.game_id==self.game_id)
                                .filter(self.box_stat_categories())
                                .subquery())
        lagged_events = (session.query(GameSequence.game_id.label('game_id'),
                                       GameSequence.model_event_num.label('model_event_num'),
                                       lagged_events.c.model_event_num.label('lagged_num'),
                                       literal(1).label('matrix_num'),
                                       lagged_events.c.player_id.label('player_id'),
                                       lagged_events.c.stat.label('action'),
                                       literal(1).label('value'))
                                .filter(GameSequence.game_id==self.game_id)
                                .filter(GameSequence.game_id==lagged_events.c.game_id)
                                .filter(lagged_events.c.model_event_num<GameSequence.model_event_num)
                                .filter(lagged_events.c.model_event_num>=lag_event_lb))
        lagged_groups = (pd.read_sql_query(lagged_events.statement,
                                           session.bind)
                           .groupby(['game_id','model_event_num']))
        for group, df in lagged_groups:
            df = df.sort_values(by=['lagged_num'], ascending=False)[:self.in_game_ts_lag_count]
            df['matrix_num'] = df['matrix_num'].cumsum()
            df['matrix_num'] = df['matrix_num'] - 1
            in_game_ts_features.append(df)
        in_game_ts_features = pd.concat(in_game_ts_features, axis=0, sort=False)
        in_game_ts_features['matrix_num'] = in_game_ts_features['matrix_num'] + self.matrix_num_iter
        in_game_ts_features['column_num'] = in_game_ts_features['player_id'].replace(self.players)
        in_game_ts_features['row_num'] = in_game_ts_features['action'].replace(self.stat_rows)
        index_columns=['game_id','model_event_num','matrix_num','column_num','row_num']
        in_game_ts_features = in_game_ts_features.set_index(index_columns)
        new_index = pd.MultiIndex.from_product([in_game_ts_features.index.levels[0],
                                                pd.Index(self.model_events),
                                                in_game_ts_features.index.levels[2],
                                                pd.Index(range(0,26)),
                                                pd.Index(range(0,26))],
                                               names=index_columns)
        in_game_ts_features = (in_game_ts_features.reindex(new_index, fill_value=0)
                                                  .reset_index())
        self.in_game_ts_features = in_game_ts_features[self.in_game_columns].set_index(self.in_game_columns[:5])
        self.matrix_num_iter += self.in_game_ts_lag_count

    def set_daily_ts_features(self):
        session = self.session
        daily_ts_query = (session.query(GameSequence.game_id.label('game_id'),
                                        Game.game_date_est.label('game_date_est'),
                                        GameSequence.player_id.label('player_id'),
                                        GameSequence.action_category.label('action'),
                                        func.count(GameSequence.action_category).label('value'))
                                 .filter(GameSequence.game_id.in_(self.game_ids))
                                 .filter(GameSequence.player_id.in_(self.players.keys()))
                                 .filter(Game.game_id.in_(self.game_ids))
                                 .filter(GameSequence.game_id==Game.game_id)
                                 .filter(GameSequence.action_category.in_(self.player_stats.keys()))
                                 .group_by(GameSequence.game_id,
                                           Game.game_date_est,
                                           GameSequence.player_id,
                                           GameSequence.action_category))
        daily_ts_features = pd.read_sql_query(daily_ts_query.statement,
                                              session.bind)
        daily_ts_features['matrix_num'] = (
          (self.game_date - daily_ts_features['game_date_est']).dt.days
           + self.matrix_num_iter - 1)
        daily_ts_features['column_num'] = daily_ts_features['player_id'].replace(self.players)
        daily_ts_features['row_num'] = daily_ts_features['action'].replace(self.stat_rows)
        daily_ts_features['game_id'] = self.game_id
        index_columns=['game_id','matrix_num','column_num','row_num']
        cols = index_columns + ['value']
        daily_ts_features = daily_ts_features[cols].groupby(index_columns).sum()
        matrix_num_range = range(self.matrix_num_iter, self.matrix_num_iter+ self.daily_ts_lag_count)
        new_index = pd.MultiIndex.from_product([daily_ts_features.index.levels[0],
                                                pd.Index(matrix_num_range),
                                                pd.Index(range(0,26)),
                                                pd.Index(range(0,26))],
                                               names=index_columns)
        daily_ts_features = (daily_ts_features.reindex(new_index, fill_value=0)
                                              .reset_index())
        self.daily_ts_features = daily_ts_features[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.matrix_num_iter += self.daily_ts_lag_count

    def set_daily_opp_ts_features(self):
        session = self.session
        players_query = self.player_opp_query().subquery()
        daily_opp_ts_query = (session.query(GameSequence.game_id.label('game_id'),
                                            Game.game_date_est.label('game_date_est'),
                                            GameSequence.opp_team_id.label('opp_team_id'),
                                            GameSequence.action_category.label('action'),
                                            func.count(GameSequence.action_category).label('value'))
                                     .filter(GameSequence.game_id.in_(self.game_ids))
                                     .filter(GameSequence.game_id==Game.game_id)
                                     .filter(GameSequence.opp_team_id.in_(self.team_ids))
                                     .filter(GameSequence.action_category.in_(self.player_stats.keys()))
                                     .group_by(GameSequence.game_id,
                                               Game.game_date_est,
                                               GameSequence.opp_team_id,
                                               GameSequence.action_category)
                                     .subquery())
        daily_opp_ts_query = (session.query(daily_opp_ts_query.c.game_id,
                                             daily_opp_ts_query.c.game_date_est,
                                             players_query.c.player_id,
                                             daily_opp_ts_query.c.stat,
                                             daily_opp_ts_query.c.value)
                                      .filter(daily_opp_ts_query.c.opp_team_id==players_query.c.opp_team_id))
        daily_opp_ts_features = pd.read_sql_query(daily_opp_ts_query.statement,
                                                  session.bind)
        daily_opp_ts_features['matrix_num'] = (
          (self.game_date - daily_opp_ts_features['game_date_est']).dt.days
           + self.matrix_num_iter - 1)
        daily_opp_ts_features['game_id'] = self.game_id
        daily_opp_ts_features['column_num'] = daily_opp_ts_features['player_id'].replace(self.players)
        daily_opp_ts_features['row_num'] = daily_opp_ts_features['action'].replace(self.stat_rows)
        daily_opp_ts_features['game_id'] = self.game_id
        index_columns=['game_id','matrix_num','column_num','row_num']
        cols = index_columns + ['value']
        daily_opp_ts_features = daily_opp_ts_features[cols].groupby(index_columns).sum()
        matrix_num_range = range(self.matrix_num_iter, self.matrix_num_iter + self.daily_ts_lag_count)
        new_index = pd.MultiIndex.from_product([daily_opp_ts_features.index.levels[0],
                                                pd.Index(matrix_num_range),
                                                pd.Index(range(0,26)),
                                                pd.Index(range(0,26))],
                                               names=index_columns)
        daily_opp_ts_features = (daily_opp_ts_features.reindex(new_index, fill_value=0)
                                                      .reset_index())
        self.daily_opp_ts_features = daily_opp_ts_features[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.matrix_num_iter += self.daily_ts_lag_count

    def set_season_ts_features(self):
        session = self.session
        season_lb = self.season - (self.season_ts_lag_count - 1)
        season_ts_query = (session.query(GameSequence.season.label('season'),
                                        GameSequence.game_id.label('game_id'),
                                        GameSequence.player_id.label('player_id'),
                                        GameSequence.action_category.label('action'),
                                        func.count(GameSequence.action_category).label('value'))
                                 .filter(GameSequence.season>=season_lb)
                                 .filter(GameSequence.season<=self.season)
                                 .filter(GameSequence.game_id==Game.game_id)
                                 .filter(Game.game_date_est<self.game_date)
                                 .filter(GameSequence.player_id.in_(self.players.keys()))
                                 .filter(GameSequence.action_category.in_(self.player_stats.keys()))
                                 .group_by(GameSequence.season,
                                           GameSequence.game_id,
                                           GameSequence.player_id,
                                           GameSequence.action_category))
        season_ts_features = pd.read_sql_query(season_ts_query.statement,
                                               session.bind)
        season_ts_features['column_num'] = season_ts_features['player_id'].replace(self.players)
        season_ts_features['row_num'] = season_ts_features['action'].replace(self.stat_rows)
        index_columns=['season','game_id','column_num','row_num']
        cols = index_columns + ['value']
        season_ts_features = season_ts_features[cols].groupby(index_columns).sum()
        season_ts_features = (season_ts_features.unstack(-2).unstack()
                                                .fillna(0).astype('int')
                                                .groupby(['season']).mean()
                                                .stack(-2).stack()
                                                .reset_index())
        season_ts_features['matrix_num'] = ((self.season
                                             - season_ts_features['season'])
                                             + self.matrix_num_iter)
        season_ts_features['game_id'] = self.game_id
        index_columns=['game_id','matrix_num','column_num','row_num']
        season_ts_features = season_ts_features.set_index(index_columns)
        new_index = pd.MultiIndex.from_product([season_ts_features.index.levels[0],
                                                season_ts_features.index.levels[1],
                                                pd.Index(range(0,26)),
                                                pd.Index(range(0,26))],
                                               names=index_columns)
        season_ts_features = (season_ts_features.reindex(new_index, fill_value=0)
                                                .reset_index())
        self.season_ts_features = season_ts_features[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.matrix_num_iter += self.season_ts_lag_count

    def set_season_opp_ts_features(self):
        session = self.session
        season_lb = self.season - (self.season_ts_lag_count - 1)
        index_columns=['season','game_id','player_id','action']
        players_query = self.player_opp_query().subquery()
        season_opp_ts_query = (session.query(GameSequence.season.label('season'),
                                             GameSequence.game_id.label('game_id'),
                                             GameSequence.opp_team_id.label('opp_team_id'),
                                             GameSequence.action_category.label('action'),
                                             func.count(GameSequence.action_category).label('value'))
                                      .filter(GameSequence.season>=season_lb)
                                      .filter(GameSequence.season<=self.season)
                                      .filter(GameSequence.game_id==Game.game_id)
                                      .filter(Game.game_date_est<self.game_date)
                                      .filter(GameSequence.opp_team_id.in_(self.team_ids))
                                      .filter(GameSequence.action_category.in_(self.player_stats.keys()))
                                      .group_by(GameSequence.season,
                                                GameSequence.game_id,
                                                GameSequence.opp_team_id,
                                                GameSequence.action_category)
                                      .subquery())
        season_opp_ts_query = (session.query(season_opp_ts_query.c.season,
                                             season_opp_ts_query.c.game_id,
                                             players_query.c.player_id,
                                             season_opp_ts_query.c.stat,
                                             season_opp_ts_query.c.value)
                                      .filter(season_opp_ts_query.c.opp_team_id==players_query.c.opp_team_id))
        season_opp_ts_features = pd.read_sql_query(season_opp_ts_query.statement,
                                               session.bind)
        season_opp_ts_features['column_num'] = season_opp_ts_features['player_id'].replace(self.players)
        season_opp_ts_features['row_num'] = season_opp_ts_features['action'].replace(self.stat_rows)
        index_columns=['season','game_id','column_num','row_num']
        cols = index_columns + ['value']
        season_opp_ts_features = season_opp_ts_features[cols].groupby(index_columns).sum()
        season_opp_ts_features = (season_opp_ts_features.unstack(-2).unstack()
                                                        .fillna(0).astype('int')
                                                        .groupby(['season']).mean()
                                                        .stack(-2).stack()
                                                        .reset_index())
        season_opp_ts_features['matrix_num'] = ((self.season
                                                 - season_opp_ts_features['season'])
                                                + self.matrix_num_iter)
        season_opp_ts_features['game_id'] = self.game_id
        index_columns=['game_id','matrix_num','column_num','row_num']
        season_opp_ts_features = season_opp_ts_features.set_index(index_columns)
        new_index = pd.MultiIndex.from_product([season_opp_ts_features.index.levels[0],
                                                season_opp_ts_features.index.levels[1],
                                                pd.Index(range(0,26)),
                                                pd.Index(range(0,26))],
                                               names=index_columns)
        season_opp_ts_features = (season_opp_ts_features.reindex(new_index, fill_value=0)
                                                        .reset_index())
        self.season_opp_ts_features = season_opp_ts_features[self.static_game_columns].set_index(self.static_game_columns[:4])
        self.matrix_num_iter += self.season_ts_lag_count

    def player_opp_query(self):
        session = self.session
        AwayTeam = (session.query(GameTeam)
                           .filter(GameTeam.game_id==self.game_id)
                           .filter(GameTeam.home_away==False)
                           .subquery())
        away_player=PlayerBoxScore.team_id==AwayTeam.c.team_id
        HomeTeam = (session.query(GameTeam)
                           .filter(GameTeam.game_id==self.game_id)
                           .filter(GameTeam.home_away==True)
                           .subquery())
        home_player=PlayerBoxScore.team_id==HomeTeam.c.team_id
        players_query = (session.query(case([(home_player, AwayTeam.c.team_id),
                                             (away_player, HomeTeam.c.team_id)],
                                            else_=None).label('opp_team_id'),
                                       PlayerBoxScore.player_id.label('player_id'))
                                .filter(PlayerBoxScore.game_id==self.game_id)
                                .filter(PlayerBoxScore.game_id==AwayTeam.c.game_id)
                                .filter(PlayerBoxScore.game_id==HomeTeam.c.game_id)
                                .filter(PlayerBoxScore.player_id.in_(self.players.keys())))
        away_team=TeamBoxScore.team_id==AwayTeam.c.team_id
        home_team=TeamBoxScore.team_id==HomeTeam.c.team_id
        teams_query = (session.query(case([(home_team, AwayTeam.c.team_id),
                                           (away_team, HomeTeam.c.team_id)],
                                            else_=None).label('opp_team_id'),
                                     TeamBoxScore.team_id.label('player_id'))
                                .filter(TeamBoxScore.game_id==self.game_id)
                                .filter(TeamBoxScore.game_id==AwayTeam.c.game_id)
                                .filter(TeamBoxScore.game_id==HomeTeam.c.game_id)
                                .filter(TeamBoxScore.team_id.in_(self.players.keys())))
        player_opp = players_query.union(teams_query)
        return player_opp

    def box_stat_categories(self):
        return and_(~GameSequence.action_category.like('%_sec'),
                    GameSequence.action_category!='period_start',
                    GameSequence.action_category!='period_end',
                    GameSequence.action_category!='timeout')

    def set_labels(self):
        self.set_game_event_labels()
        self.set_player_event_labels()
        self.set_second_event_labels()
        self.labels = pd.concat([self.game_event_labels,
                                 self.player_event_labels,
                                 self.second_event_labels],
                                axis=1)

    def set_game_event_labels(self):
        session = self.session
        event_stats = set(self.action_events.keys())
        event_label_query = (session.query(GameSequence.game_id.label('game_id'),
                                           GameSequence.model_event_num.label('model_event_num'),
                                           case([(GameSequence.action_category.in_(event_stats), GameSequence.action_category)],
                                                else_='').label('label_0'))
                                    .filter(GameSequence.game_id==self.game_id)
                                    .group_by(GameSequence.game_id,
                                              GameSequence.model_event_num,
                                              GameSequence.action_category))
        game_event_labels = pd.read_sql_query(event_label_query.statement,
                                              session.bind,
                                              index_col=['game_id','model_event_num'])
        game_event_labels['label_0'] = game_event_labels['label_0'].replace(self.action_events)
        self.game_event_labels = game_event_labels

    def set_player_event_labels(self):
        session = self.session
        player_event_labels = (session.query(GameSequence.game_id.label('game_id'),
                                             GameSequence.player_id.label('player_id'),
                                             GameSequence.model_event_num.label('model_event_num'),
                                             GameSequence.sub_event_num.label('sub_event_num'))
                                      .filter(GameSequence.game_id==self.game_id)
                                      .filter(GameSequence.player_id.in_(self.players.keys()))
                                      .filter(GameSequence.sub_event_num!=0)
                                      .group_by(GameSequence.game_id,
                                                GameSequence.model_event_num,
                                                GameSequence.sub_event_num))
        player_event_labels = pd.read_sql_query(player_event_labels.statement,
                                                session.bind)
        index_columns = ['game_id','model_event_num','sub_event_num']
        player_event_labels = (player_event_labels.set_index(index_columns)
                                                  .unstack()
                                                  .replace(self.players))
        col_names = []
        for col in player_event_labels.columns:
            col_names.append('label_{}'.format(col[1]))
        player_event_labels.columns = col_names
        new_index = pd.MultiIndex.from_product([player_event_labels.index.levels[0],
                                                pd.Index(self.model_events)],
                                               names=['game_id','model_event_num'])
        self.player_event_labels = (player_event_labels.reindex(new_index)
                                                       .fillna(27).astype('int')
                                                       .sort_index())

    def set_second_event_labels(self):
        session = self.session
        event_label_query = (session.query(GameSequence.game_id.label('game_id'),
                                           GameSequence.model_event_num.label('model_event_num'),
                                           case([(GameSequenceSec.clipped_sec_elapsed==None, 0)],
                                                else_=GameSequenceSec.clipped_sec_elapsed).label('label_4'))
                                    .select_from(GameSequence)
                                    .outerjoin(GameSequenceSec,
                                               and_(GameSequence.game_id == GameSequenceSec.game_id,
                                                    GameSequence.model_event_num == GameSequenceSec.model_event_num))
                                    .filter(GameSequence.game_id==self.game_id)
                                    .group_by(GameSequence.game_id,
                                              GameSequence.model_event_num))
        self.second_event_labels = pd.read_sql_query(event_label_query.statement,
                                                     session.bind,
                                                     index_col=['game_id','model_event_num'])

    def set_reward_baseline(self):
        session = self.session
        event_stats = set(self.player_stats.keys())
        reward_baseline = (session.query(GameSequence.game_id.label('game_id'),
                                         GameSequence.player_id.label('player_id'),
                                         GameSequence.action_category.label('action'),
                                         func.count(GameSequence.action_category).label('value'))
                                  .filter(GameSequence.game_id==game_id)
                                  .filter(GameSequence.action_category.in_(event_stats))
                                  .filter(GameSequence.player_id.in_(self.players.keys()))
                                  .group_by(GameSequence.game_id,
                                            GameSequence.player_id,
                                            GameSequence.action_category))
        reward_baseline = pd.read_sql_query(reward_baseline.statement,
                                            session.bind)
        reward_baseline['row_num'] = reward_baseline['action'].replace(self.player_stats)
        reward_baseline['column_num'] = reward_baseline['player_id'].replace(self.players)
        reward_baseline = reward_baseline.drop(['player_id', 'action'], axis=1)
        index_columns = ['game_id','column_num','row_num']
        reward_baseline = reward_baseline.set_index(index_columns)
        new_index = pd.MultiIndex.from_product([reward_baseline.index.levels[0],
                                                pd.Index(range(0,26)),
                                                pd.Index(range(0,26))],
                                               names=index_columns)
        self.reward_baseline = (reward_baseline.reindex(new_index, fill_value=0)
                                               .reset_index())
