import pandas as pd
from sqlalchemy import (and_, case, func, literal)
from nba_data.processing.nba_player_boxes import PlayerBoxScore

def get_on_court_events(session, game_events):
    cols = ['sport','season','game_id','period','model_event_num',
            'event_num','team_id','person_id','action_sub_category']
    substitution_categories = ['sub_in','sub_out']
    criteria = "action_sub_category in @substitution_categories"
    sub_events = game_events.query(criteria)[cols]
    sub_events = add_sub_count(sub_events)
    sub_events = sub_events.set_index(cols[:-1])
    game_players_index = get_game_players_index(session, game_events)
    on_court_events = sub_events.reindex(game_players_index)
    on_court_events['sub_count'] = on_court_events['sub_count'].fillna(0)
    on_court_events = add_on_court_ind(on_court_events)
    on_court_events = remove_off_court_records(on_court_events)
    on_court_events = on_court_events['on_court_ind'].reset_index()
    return on_court_events

def add_sub_count(sub_events):
    indices = sub_events.query("action_sub_category=='sub_in'").index
    sub_events.loc[indices, 'sub_count'] = 1
    indices = sub_events.query("action_sub_category=='sub_out'").index
    sub_events.loc[indices, 'sub_count'] = -1
    return sub_events

def get_game_players_index(session, game_events):
    game_ids = list(game_events['game_id'].unique())
    game_players = (session.query(PlayerBoxScore.game_id,
                                  PlayerBoxScore.team_id,
                                  PlayerBoxScore.player_id.label('person_id'))
                           .filter(PlayerBoxScore.game_id.in_(game_ids)))
    game_players = pd.read_sql_query(game_players.statement, session.bind)
    index_cols = ['sport','season','game_id','period','model_event_num',
                  'event_num','team_id','person_id']
    game_players = pd.merge(left=game_events[index_cols[:-2]].drop_duplicates(keep='first'),
                            right=game_players,
                            on=['game_id'],
                            how='inner').set_index(index_cols)
    return game_players.index

def add_on_court_ind(on_court_events):
    group_cols=['game_id','period','person_id']
    on_court_events['on_court_ind']=on_court_events.groupby(group_cols)['sub_count'].cumsum()
    on_court_events['on_court_ind'] = on_court_events['on_court_ind'].fillna(0).astype('int')
    return on_court_events

def remove_off_court_records(on_court_events):
    indices = on_court_events.query("on_court_ind!=0").index
    on_court_events = on_court_events.loc[indices, :]
    return on_court_events
