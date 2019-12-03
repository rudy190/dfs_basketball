import pandas as pd
from sqlalchemy import (and_, func, cast, literal)
from sqlalchemy.dialects.sqlite import INTEGER
from .nba_game_events import GameEvent
from .nba_game_starters import GameStarter
from .nba_game_teams import GameTeam
from .nba_game_win_prob import GameWinProbEvent

def get_sec_elapse_events(session, game_ids):
    sec_elapse_events_query=set_sec_elapse_events_query(session, game_ids)
    sec_elapse_events=pd.read_sql_query(sec_elapse_events_query.statement, session.bind)
    del sec_elapse_events['prior_id']
    sec_elapse_events = clip_sec_categories(sec_elapse_events)
    return sec_elapse_events

def set_sec_elapse_events_query(session, game_ids):
    wp_events = get_win_prob_events(session, game_ids).subquery()
    prior_wp_events = get_prior_win_prob_events(session, game_ids).subquery()
    sec_elapse_events_query = merge_win_prob_events(session, wp_events, prior_wp_events)
    return sec_elapse_events_query

def get_win_prob_events(session, game_ids):
    win_prob_events = (session.query(GameWinProbEvent,
                                     GameEvent.event_id.label('model_event_num'))
                              .filter(GameWinProbEvent.event_num!=None)
                              .filter(and_(GameWinProbEvent.game_id==GameEvent.game_id,
                                           GameWinProbEvent.event_num==GameEvent.event_num))
                              .filter(GameWinProbEvent.game_id.in_(game_ids)))
    return win_prob_events

def get_prior_win_prob_events(session, game_ids):
    prior_win_prob_events = (session.query(GameWinProbEvent)
                                    .filter(GameWinProbEvent.event_num!=None)
                                    .filter(and_(GameWinProbEvent.game_id==GameEvent.game_id,
                                                 GameWinProbEvent.event_num==GameEvent.event_num))
                                    .filter(GameWinProbEvent.game_id.in_(game_ids)))
    return prior_win_prob_events

def merge_win_prob_events(session, wp_events, prior_wp_events):
    sec_elapse_events = (session.query(wp_events.c.sport,
                                       wp_events.c.season,
                                       wp_events.c.game_id,
                                       wp_events.c.period,
                                       wp_events.c.model_event_num,
                                       func.max(prior_wp_events.c.id).label('prior_id'),
                                       (cast((prior_wp_events.c.sec_remain - wp_events.c.sec_remain),
                                             INTEGER)/100).label('sec_elapsed'))
                      .filter(prior_wp_events.c.game_id==wp_events.c.game_id)
                      .filter(prior_wp_events.c.period==wp_events.c.period)
                      .filter(wp_events.c.id>prior_wp_events.c.id)
                      .group_by(wp_events.c.id))
    return sec_elapse_events

def clip_sec_categories(sec_elapse_events):
    sec_elapse_events['clipped_sec_elapsed'] = sec_elapse_events['sec_elapsed']
    criteria = sec_elapse_events['sec_elapsed'] > 24
    sec_elapse_events.loc[criteria, 'clipped_sec_elapsed'] = 24
    return sec_elapse_events
