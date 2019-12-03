import pandas as pd
from sqlalchemy import (and_, case, func, literal)
from sqlalchemy.orm import aliased
from .nba_game_events import GameEvent
from .nba_game_players import GamePlayer
from .nba_game_starters import GameStarter
from .nba_game_teams import GameTeam

def get_period_start_sub_actions(session, game_events):
    period_start_subs=set_period_start_subs(session, game_events)
    period_start_subs=add_sub_event_num(period_start_subs)
    return period_start_subs

def set_period_start_subs(session, game_events):
    period_min_events = get_period_min_events(game_events)
    period_start_subs_query = get_period_start_subs_query(session, game_events)
    period_start_subs = pd.read_sql_query(period_start_subs_query.statement, session.bind)
    period_start_subs = pd.merge(left=period_start_subs,
                                 right=period_min_events,
                                 on=['game_id','period'],
                                 how='inner')
    return period_start_subs

def get_period_min_events(game_events):
    merge_cols = ['game_id','period','model_event_num']
    period_min_events = game_events.groupby(merge_cols[:2])[merge_cols[-1:]].min().reset_index()
    min_events_index = pd.merge(left=game_events[merge_cols].reset_index(),
                                right=period_min_events,
                                on=merge_cols,
                                how='inner').set_index('index').index
    cols = merge_cols + ['sec_remain','home_poss','away_poss','home_pts','away_pts']
    period_min_events = game_events.loc[min_events_index, cols]
    return period_min_events

def get_period_start_subs_query(session, game_events):
    game_ids = list(game_events['game_id'].unique())
    AwayTeam = session.query(GameTeam).filter(GameTeam.game_id.in_(game_ids)).filter(GameTeam.home_away==False).subquery()
    HomeTeam = session.query(GameTeam).filter(GameTeam.game_id.in_(game_ids)).filter(GameTeam.home_away==True).subquery()
    period_start_subs = (session.query(GameStarter.sport,
                                       GameStarter.season,
                                       GameStarter.game_id,
                                       GameStarter.period,
                                       GameStarter.team_id,
                                       GameStarter.player_id.label('person_id'),
                                       GamePlayer.player_name.label('person_name'),
                                       GameTeam.team_nickname.label('team_nickname'),
                                       HomeTeam.c.team_id.label('home_team_id'),
                                       AwayTeam.c.team_id.label('away_team_id'),
                                       (case([(GameStarter.team_id==AwayTeam.c.team_id, None),
                                              (GameStarter.team_id==HomeTeam.c.team_id, 'home_period_starters')])
                                             .label('home_description')),
                                       (case([(GameStarter.team_id==AwayTeam.c.team_id, 'away_period_starters'),
                                              (GameStarter.team_id==HomeTeam.c.team_id, None)])
                                             .label('away_description')),
                                       literal(None).label('neutral_description'),
                                       (case([(GameStarter.team_id==AwayTeam.c.team_id, 'away_period_starters'),
                                              (GameStarter.team_id==HomeTeam.c.team_id, 'home_period_starters')])
                                             .label('action_category')),
                                       literal('sub_in').label('action_sub_category'),
                                       literal('shift').label('stat_category'),
                                       (case([(GameStarter.team_id==AwayTeam.c.team_id, HomeTeam.c.team_id),
                                              (GameStarter.team_id==HomeTeam.c.team_id, AwayTeam.c.team_id)],
                                              else_=0).label('opp_team_id')),
                                       literal(None).label('pers_foul'),
                                       literal(None).label('team_foul'),
                                       literal(None).label('official'),
                                       literal(None).label('shot_event'),
                                       literal(None).label('shot_type'),
                                       literal(None).label('shot_zone_basic'),
                                       literal(None).label('shot_zone_area'),
                                       literal(None).label('shot_zone_range'),
                                       (case([(GameStarter.team_id==AwayTeam.c.team_id, -2),
                                              (GameStarter.team_id==HomeTeam.c.team_id, -1)])
                                              .label('eventmsgtype')),
                                       literal(None).label('event_num'),
                                       literal(None).label('ft_num'),
                                       literal(None).label('ft_total'))
                                .filter(GameStarter.game_id.in_(game_ids))
                                .filter(GameStarter.game_id==HomeTeam.c.game_id)
                                .filter(GameStarter.game_id==AwayTeam.c.game_id)
                                .filter(GamePlayer.game_id.in_(game_ids))
                                .filter(GameStarter.game_id==GamePlayer.game_id)
                                .filter(GameStarter.player_id==GamePlayer.player_id)
                                .filter(GameTeam.game_id.in_(game_ids))
                                .filter(GameStarter.game_id==GameTeam.game_id)
                                .filter(GameStarter.team_id==GameTeam.team_id))
    return period_start_subs

def add_sub_event_num(period_start_subs):
    group_cols = ['game_id','period','team_id']
    period_start_subs['sub_event_num'] = period_start_subs.groupby(group_cols).cumcount()
    return period_start_subs
