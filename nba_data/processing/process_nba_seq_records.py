import pandas as pd
from .db_config import (Session, Engine)
from .nba_game_seq import GameSequence
from .nba_game_seq_sec import GameSequenceSec
from .nba_game_on_court import GameOnCourt
from .nba_game_sequence_events import get_game_events
from .nba_starter_events import get_period_start_sub_actions
from .nba_on_court_records import get_on_court_events

def process_game_sequences(game_ids):
    session=Session()

    game_events = get_game_events(session, game_ids)
    period_start_subs=get_period_start_sub_actions(session, game_events)
    starter_errors = get_games_with_starter_errors(game_events, period_start_subs)
    game_events = remove_games_with_starter_errors(game_events, starter_errors)
    period_start_subs = remove_games_with_starter_errors(period_start_subs, starter_errors)
    game_events=merge_game_events_and_sub_actions(game_events, period_start_subs)
    insert_sequence_event_records(session, GameSequence, game_events)

    sec_elapse_events = get_sec_elapse_events(game_events)
    insert_sequence_event_records(session, GameSequenceSec, sec_elapse_events)

    on_court_events = get_on_court_events(session, game_events)
    insert_sequence_event_records(session, GameOnCourt, on_court_events)

    session.close()
    return True

def remove_games_with_starter_errors(events_df, starter_errors):
    return events_df.query("game_id not in @starter_errors")

def get_game_periods(game_events):
    group_cols=['game_id','period','model_event_num']
    game_periods=(game_events.reset_index()[group_cols]
                             .groupby(group_cols[:-1])
                             .count())
    return game_periods

def get_games_with_starter_errors(game_events, period_start_subs):
    game_periods = get_game_periods(game_events)
    group_cols=['game_id','period','action_category']
    period_starter_count=(period_start_subs.reset_index()[group_cols]
                                           .groupby(group_cols[:-1])
                                           .count())
    criteria = period_starter_count['action_category']!=10
    period_starter_count = (period_starter_count.reindex(game_periods.index)
                                                .reset_index())
    criteria = "action_category!=10 or action_category!=action_category"
    starter_error_games=list(period_starter_count.query(criteria)[group_cols[0]].unique())
    if starter_error_games:
        print('Excluded: {} games'.format(len(starter_error_games)))
        print(starter_error_games)
    return starter_error_games

def insert_sequence_event_records(session, tableClass, events_df):
    columns=[col.name for col in tableClass.__table__.c if not col.primary_key]
    events_df[columns].to_sql(tableClass.__table__.name,
                              session.bind,
                              if_exists='append',
                              index=False,
                              chunksize=500000)
    session.commit()
    return True

def merge_game_events_and_sub_actions(game_events, period_start_sub_actions):
    game_events = pd.concat([game_events, period_start_sub_actions], axis=0, sort=False)
    game_events['model_event_num'] = game_events.groupby(['game_id','model_event_num','eventmsgtype']).ngroup() + 1
    game_events = game_events.sort_values(by=['game_id','model_event_num','sub_event_num'])
    return game_events

def get_sec_elapse_events(game_events):
    group_cols = ['sport','season','game_id','period','model_event_num']
    sec_elapse_events = pd.concat([game_events.groupby(group_cols)['sec_remain'].min(),
                                   game_events.groupby(group_cols)['sec_remain'].min().shift(1).rename('shifted_sec')],
                                  axis=1,
                                  sort=False).reset_index()
    criteria = (sec_elapse_events['period'] != sec_elapse_events['period'].shift(1))
    sec_elapse_events.loc[criteria, 'shifted_sec'] = sec_elapse_events.loc[criteria, 'sec_remain']
    sec_elapse_events['sec_elapsed'] = sec_elapse_events['shifted_sec'] - sec_elapse_events['sec_remain']
    sec_elapse_events['clipped_sec_elapsed'] = sec_elapse_events['sec_elapsed']
    criteria = sec_elapse_events['sec_elapsed'] > 24
    sec_elapse_events.loc[criteria, 'clipped_sec_elapsed'] = 24
    sec_elapse_events = sec_elapse_events.drop(['sec_remain','shifted_sec'], axis=1)
    return sec_elapse_events
