import pandas as pd
from sqlalchemy import (and_, or_, case, func, literal)
from sqlalchemy.orm import aliased
from .nba_game_event_players import GameEventPlayer
from .nba_game_events import GameEvent
from .nba_game_shots import GameShot
from .nba_game_teams import GameTeam
from .nba_game_win_prob import GameWinProbEvent

def get_game_events(session, game_ids):
    game_events_query=set_game_events_query(session, game_ids)
    game_events=pd.read_sql_query(game_events_query.statement, session.bind)
    game_events=add_action_categories(game_events)
    game_events = game_events.sort_values(by=['game_id','model_event_num','sub_event_num'])
    game_events=fill_missing_sequence(game_events)
    game_events=add_stat_categories(game_events)
    return game_events

def set_game_events_query(session, game_ids):
    game_events=merge_events_and_event_players(session, game_ids).subquery()
    game_events=add_win_prob_data(session, game_events, game_ids).subquery()
    game_events=add_shot_chart_data(session, game_events, game_ids).subquery()
    game_events=add_poss_pts_data(session, game_events, game_ids)
    return game_events

def merge_events_and_event_players(session, game_ids):
    AwayTeam = session.query(GameTeam).filter(GameTeam.game_id.in_(game_ids)).filter(GameTeam.home_away==False).subquery()
    HomeTeam = session.query(GameTeam).filter(GameTeam.game_id.in_(game_ids)).filter(GameTeam.home_away==True).subquery()
    game_events = (session.query(GameEvent.event_id,
                                 GameEvent.sport,
                                 GameEvent.season,
                                 GameEvent.game_id,
                                 GameEvent.event_num,
                                 GameEvent.eventmsgtype,
                                 GameEventPlayer.player_num,
                                 GameEventPlayer.player_id,
                                 case([(is_player_team(AwayTeam), AwayTeam.c.team_nickname),
                                       (is_player_team(HomeTeam), HomeTeam.c.team_nickname)],
                                      else_ = GameEventPlayer.player_name).label('player_name'),
                                 case([(is_player_team(AwayTeam), AwayTeam.c.team_id),
                                       (is_player_team(HomeTeam), HomeTeam.c.team_id),
                                       (GameEventPlayer.team_id == None, 0)],
                                      else_ = GameEventPlayer.team_id).label('team_id'),
                                 case([(is_player_team(AwayTeam), AwayTeam.c.team_nickname),
                                       (is_player_team(HomeTeam), HomeTeam.c.team_nickname),
                                       (GameEventPlayer.team_id == None, 0)],
                                      else_ = GameEventPlayer.team_nickname).label('team_nickname'),
                                 HomeTeam.c.team_id.label('home_team_id'),
                                 AwayTeam.c.team_id.label('away_team_id'),
                                 GameEventPlayer.home_description,
                                 GameEventPlayer.away_description,
                                 GameEventPlayer.neutral_description.label('event_neutral_desc'))
                          .select_from(GameEvent)
                          .outerjoin(GameEventPlayer,
                                     and_(GameEvent.game_id==GameEventPlayer.game_id,
                                          GameEvent.event_num==GameEventPlayer.event_num))
                          .filter(GameEvent.event_id!=None)
                          .filter(is_instant_replay())
                          .filter(GameEvent.game_id==HomeTeam.c.game_id)
                          .filter(GameEvent.game_id==AwayTeam.c.game_id)
                          .filter(GameEvent.game_id.in_(game_ids))
                          .filter(~and_(GameEventPlayer.player_id==None,
                                        GameEvent.eventmsgtype==5)))
    return game_events

def is_player_team(Team):
    return GameEventPlayer.player_id == Team.c.team_id

def is_instant_replay():
    return GameEvent.eventmsgtype!=18

def add_win_prob_data(session, game_events, game_ids):
    game_events = (session.query(game_events,
                                 GameWinProbEvent.id.label('win_prob_event_id'),
                                 GameWinProbEvent.period,
                                 GameWinProbEvent.sec_remain,
                                 case([(and_(game_events.c.home_description == None,
                                             game_events.c.away_description == None,
                                             game_events.c.event_neutral_desc == None),
                                             GameWinProbEvent.description)],
                                      else_ = game_events.c.event_neutral_desc).label('neutral_description'))
                          .select_from(game_events)
                          .join(GameWinProbEvent,
                                and_(game_events.c.game_id==GameWinProbEvent.game_id,
                                     game_events.c.event_num==GameWinProbEvent.event_num))
                          .filter(GameWinProbEvent.game_id.in_(game_ids)))
    return game_events

def add_shot_chart_data(session, game_events, game_ids):
    FilteredGameShot = session.query(GameShot).filter(GameShot.game_id.in_(game_ids)).subquery()
    game_events = (session.query(game_events,
                                 FilteredGameShot.c.event_type.label('shot_event'),
                                 FilteredGameShot.c.shot_type,
                                 FilteredGameShot.c.shot_zone_basic,
                                 FilteredGameShot.c.shot_zone_area,
                                 FilteredGameShot.c.shot_zone_range)
                          .select_from(game_events)
                          .outerjoin(FilteredGameShot,
                                and_(game_events.c.game_id==FilteredGameShot.c.game_id,
                                     game_events.c.event_num==FilteredGameShot.c.event_num,
                                     game_events.c.player_id==FilteredGameShot.c.player_id)))
    return game_events

def add_poss_pts_data(session, game_events, game_ids):
    prior_events = prior_events_data(session, game_events, game_ids).subquery()
    game_events = (session.query(game_events.c.sport,
                                 game_events.c.season,
                                 game_events.c.game_id,
                                 game_events.c.period,
                                 game_events.c.event_id.label('model_event_num'),
                                 game_events.c.sec_remain,
                                 game_events.c.event_num,
                                 case([(game_events.c.player_num==None, 0)],
                                      else_=game_events.c.player_num).label('sub_event_num'),
                                 game_events.c.eventmsgtype,
                                 case([(game_events.c.home_description.contains('Offensive Foul Turnover'), 1),
                                       (game_events.c.home_description.contains('% Free Throw Technical %'), 1),
                                       (game_events.c.away_description.contains('Offensive Foul Turnover'), 0),
                                       (game_events.c.away_description.contains('% Free Throw Technical %'), 0),
                                       (game_events.c.eventmsgtype==10, 0),
                                       (prior_events.c.home_poss_ind == None, 0)],
                                      else_ = prior_events.c.home_poss_ind).label('home_poss'),
                                 case([(game_events.c.away_description.contains('Offensive Foul Turnover'), 1),
                                       (game_events.c.away_description.contains('% Free Throw Technical %'), 1),
                                       (game_events.c.home_description.contains('Offensive Foul Turnover'), 0),
                                       (game_events.c.home_description.contains('% Free Throw Technical %'), 0),
                                       (game_events.c.eventmsgtype==10, 0),
                                       (prior_events.c.home_poss_ind == 0, 1),
                                       (prior_events.c.home_poss_ind == 1, 0),
                                       (prior_events.c.home_poss_ind == None, 0)],
                                      else_ = None).label('away_poss'),
                                 game_events.c.neutral_description,
                                 game_events.c.home_description,
                                 game_events.c.away_description,
                                 game_events.c.shot_event,
                                 game_events.c.shot_type,
                                 game_events.c.shot_zone_basic,
                                 game_events.c.shot_zone_area,
                                 game_events.c.shot_zone_range,
                                 case([(is_opening_jump(game_events), 0)],
                                      else_=prior_events.c.home_pts).label('home_pts'),
                                 case([(is_opening_jump(game_events), 0)],
                                      else_=prior_events.c.away_pts).label('away_pts'),
                                 game_events.c.team_id,
                                 game_events.c.team_nickname,
                                 case([(is_home_player(game_events), game_events.c.away_team_id),
                                       (is_away_player(game_events), game_events.c.home_team_id)],
                                      else_=0).label('opp_team_id'),
                                 case([(is_blank_player_id(game_events), 0)],
                                      else_=game_events.c.player_id).label('person_id'),
                                 game_events.c.player_name.label('person_name'),
                                 game_events.c.home_team_id,
                                 game_events.c.away_team_id)
                              .select_from(game_events)
                              .outerjoin(prior_events,
                                         and_(game_events.c.win_prob_event_id==prior_events.c.id)))
    return game_events

def prior_events_data(session, game_events, game_ids):
    PriorWPEvent = aliased(GameWinProbEvent)
    prior_events = (session.query(GameWinProbEvent.id,
                                  GameWinProbEvent.game_id,
                                  GameWinProbEvent.event_num,
                                  func.max(PriorWPEvent.id).label('prior_win_prob_event_id'),
                                  PriorWPEvent.home_poss_ind,
                                  PriorWPEvent.home_pts,
                                  PriorWPEvent.away_pts)
                           .filter(PriorWPEvent.game_id==GameWinProbEvent.game_id)
                           .filter(PriorWPEvent.period==GameWinProbEvent.period)
                           .filter(GameWinProbEvent.id>PriorWPEvent.id)
                           .filter(PriorWPEvent!=None)
                           .filter(GameWinProbEvent.event_num!=None)
                           .filter(GameWinProbEvent.game_id.in_(game_ids))
                           .group_by(GameWinProbEvent.id))
    return prior_events

def is_jumpball(game_events):
    return game_events.c.eventmsgtype==10

def is_opening_jump(game_events):
    return and_(game_events.c.period==1,
                is_jumpball(game_events),
                game_events.c.event_num<=2)

def is_home_player(game_events):
    return game_events.c.team_id==game_events.c.home_team_id

def is_away_player(game_events):
    return game_events.c.team_id==game_events.c.away_team_id

def is_blank_player_id(game_events):
    return game_events.c.player_id==None

# Reinsert deleted detailed_stat_category and stat_category information here

def add_action_categories(game_events):
    game_events['action_category']=None
    game_events['action_sub_category']=None
    game_events = add_made_shot_actions(game_events)
    game_events = add_missed_shot_actions(game_events)
    game_events = add_free_throw_actions(game_events)
    game_events = add_rebound_actions(game_events)
    game_events = add_turnover_actions(game_events)
    game_events = add_foul_actions(game_events)
    game_events = add_violation_categories(game_events)
    game_events = add_sub_actions(game_events)
    game_events = add_timeout_actions(game_events)
    game_events = add_jumpball_actions(game_events)
    game_events = add_ejection_actions(game_events)
    game_events = add_period_start_actions(game_events)
    game_events = add_period_end_actions(game_events)
    return game_events

def add_missing_shot_types(game_events):
    for team in ['home','away']:
        desc_field = '{}_description'.format(team)
        for msg_type in [1,2]:
            missing_shot_type_query = ("eventmsgtype=={} and {}=={} and shot_type!=shot_type "\
                                       "and sub_event_num==1".format(str(msg_type),desc_field,desc_field))
            missing_shot_type = game_events.query(missing_shot_query)[desc_field]
            missing_3PT_shots = missing_shot_type[(missing_shot_type.str.contains('3PT') == True)].index
            game_events.loc[missing_3PT_shots,'shot_type'] = '3PT Field Goal'
            missing_2PT_shots = missing_shot_type[(missing_shot_type.str.contains('2PT') == True)].index
            game_events.loc[missing_2PT_shots,'shot_type'] = '2PT Field Goal'
    return game_events

def add_made_shot_actions(game_events):
    made_2PT_query = "eventmsgtype==1 and sub_event_num==1 and shot_type=='2PT Field Goal'"
    made_2PT_index = game_events.query(made_2PT_query).index
    game_events.loc[made_2PT_index,'action_sub_category'] = 'fg2m'
    game_events.loc[made_2PT_index,'action_category'] = 'fg2m'
    made_3PT_query = "eventmsgtype==1 and sub_event_num==1 and shot_type=='3PT Field Goal'"
    made_3PT_index = game_events.query(made_3PT_query).index
    game_events.loc[made_3PT_index,'action_sub_category'] = 'fg3m'
    game_events.loc[made_3PT_index,'action_category'] = 'fg3m'
    game_events = add_assisted_shot_actions(game_events)
    return game_events

def add_assisted_shot_actions(game_events):
    game_events = add_assist_actions(game_events)
    action_columns = ['game_id','model_event_num','action_sub_category']
    assist_query = "action_sub_category=='assist'"
    assisted_shots = game_events.query(assist_query)[action_columns]
    assisted_shots = pd.merge(left=game_events[action_columns[:2]].reset_index(),
                              right=assisted_shots,
                              on=action_columns[:2],
                              how='inner').set_index('index')['action_sub_category']
    shot_categories = ['fg3m','fg2m']
    shot_query = "action_sub_category in @shot_categories"
    shots = game_events.query(shot_query)[action_columns]
    shots = pd.merge(left=game_events[action_columns[:2]].reset_index(),
                     right=shots,
                     on=action_columns[:2],
                     how='inner').set_index('index')['action_sub_category']
    assist_intersect = shots.index.intersection(assisted_shots.index)
    shots.loc[assist_intersect] = 'assisted_' + shots.loc[assist_intersect]
    game_events.loc[shots.index, 'action_category'] = shots.loc[shots.index]
    return game_events

def add_assist_actions(game_events):
    assist_query = "eventmsgtype==1 and sub_event_num!=1"
    assists_index = game_events.query(assist_query).index
    game_events.loc[assists_index,'action_sub_category'] = 'assist'
    return game_events

def add_missed_shot_actions(game_events):
    missed_2PT_query = "eventmsgtype==2 and sub_event_num==1 and shot_type=='2PT Field Goal'"
    missed_2PT_index = game_events.query(missed_2PT_query).index
    game_events.loc[missed_2PT_index,'action_sub_category'] = 'fg2a'
    game_events.loc[missed_2PT_index,'action_category'] = 'fg2a'
    missed_3PT_query = "eventmsgtype==2 and sub_event_num==1 and shot_type=='3PT Field Goal'"
    missed_3PT_index = game_events.query(missed_3PT_query).index
    game_events.loc[missed_3PT_index,'action_sub_category'] = 'fg3a'
    game_events.loc[missed_3PT_index,'action_category'] = 'fg3a'
    game_events = add_blocked_shot_actions(game_events)
    return game_events

def add_blocked_shot_actions(game_events):
    game_events = add_block_actions(game_events)
    action_columns = ['game_id','model_event_num','action_sub_category']
    block_query = "action_sub_category=='block'"
    blocked_shots = game_events.query(block_query)[action_columns]
    blocked_shots = pd.merge(left=game_events[action_columns[:2]].reset_index(),
                             right=blocked_shots,
                             on=action_columns[:2],
                             how='inner').set_index('index')['action_sub_category']
    shot_categories = ['fg3a','fg2a']
    shot_query = "action_sub_category in @shot_categories"
    shots = game_events.query(shot_query)[action_columns]
    shots = pd.merge(left=game_events[action_columns[:2]].reset_index(),
                     right=shots,
                     on=action_columns[:2],
                     how='inner').set_index('index')['action_sub_category']
    block_intersect = shots.index.intersection(blocked_shots.index)
    shots.loc[block_intersect] = 'blocked_' + shots.loc[block_intersect]
    game_events.loc[shots.index, 'action_category'] = shots.loc[shots.index]
    return game_events

def add_block_actions(game_events):
    block_query = "eventmsgtype==2 and sub_event_num!=1"
    blocks_index = game_events.query(block_query).index
    game_events.loc[blocks_index,'action_sub_category'] = 'block'
    return game_events

def add_free_throw_actions(game_events):
    not_null_actions = 'action_category==action_category'
    null_actions = 'action_category!=action_category'
    for team in ['home','away']:
        desc_field = '{}_description'.format(team)
        if team != 'neutral':
            team_field = '{}_team_id'.format(team)
            criteria = "eventmsgtype==3 and {}=={} and team_id=={}".format(desc_field, desc_field, team_field)
        else:
            criteria = "eventmsgtype==3 and {}=={}".format(desc_field, desc_field)
        cols=['game_id','period','sec_remain','model_event_num','sub_event_num','person_id','team_id',desc_field]
        desc_df = game_events.query(criteria)[cols]
        desc_df['action_category'] = None
        desc_df['ft_num'] = None
        desc_df['ft_total'] = None
        desc_df['extra_info'] = None

        for pattern in ['(?P<miss_flag>MISS)\s(?P<player>.*)\s(?P<action_category>Free\sThrow\sTechnical).*',
                        '(?P<player>.*)\s(?P<action_category>Free\sThrow\sTechnical).*',
                        '(?P<miss_flag>MISS)\s(?P<player>.*)\s(?P<action_category>Free\sThrow\sFlagrant).*',
                        '(?P<player>.*)\s(?P<action_category>Free\sThrow\sFlagrant).*',
                        '(?P<miss_flag>MISS)\s(?P<player>.*)\s(?P<action_category>Free\sThrow\sClear\sPath)\s(?P<ft_num>\d+)\sof\s(?P<ft_total>\d+)',
                        '(?P<player>.*)\s(?P<action_category>Free\sThrow\sClear\sPath)\s(?P<ft_num>\d+)\sof\s(?P<ft_total>\d+)\s.*',
                        '(?P<player>.*)\s(?P<action_category>Free\sThrow\sClear\sPath)\s(?P<ft_num>\d+)\sof\s(?P<ft_total>\d+)',
                        '(?P<miss_flag>MISS)\s(?P<player>.*)\s(?P<action_category>Free\sThrow)\s(?P<ft_num>\d+)\sof\s(?P<ft_total>\d+)',
                        '(?P<player>.*)\s(?P<action_category>Free\sThrow)\s(?P<ft_num>\d+)\sof\s(?P<ft_total>\d+)\s.*',
                        '(?P<player>.*)\s(?P<action_category>Free\sThrow)\s(?P<ft_num>\d+)\sof\s(?P<ft_total>\d+)',
                        '(?P<action_category>Free\sThrow)\s(?P<ft_num>\d+)\sof\s(?P<ft_total>\d+)',
                        '(?P<action_category>Free\sThrow)\s(?P<ft_num>\d+)\sof\s(?P<ft_total>\d+)\s.*']:
            extract_df = desc_df[desc_field].fillna('').str.extract(pattern, expand=True)
            matched_indices = extract_df.query(not_null_actions).index.intersection(desc_df.query(null_actions).index)
            if len(matched_indices):
                if 'miss_flag' in extract_df.columns:
                    desc_df.loc[matched_indices, 'action_category'] = (
                         (extract_df.loc[matched_indices, 'action_category'].str.lower())
                          .str.cat(extract_df.loc[matched_indices, 'miss_flag'].str.lower(), sep=' '))
                else:
                    desc_df.loc[matched_indices, 'action_category'] = extract_df.loc[matched_indices, 'action_category'].str.lower()
                if 'ft_num' in extract_df.columns:
                    desc_df.loc[matched_indices, 'ft_num'] = extract_df.loc[matched_indices, 'ft_num']
                    desc_df.loc[matched_indices, 'ft_total'] = extract_df.loc[matched_indices, 'ft_total']
                else:
                    desc_df.loc[matched_indices, 'ft_num'] = '1'
                    desc_df.loc[matched_indices, 'ft_total'] = '1'

        free_throw_indices = desc_df.query(not_null_actions).index.intersection(game_events.query(null_actions).index)
        game_events.loc[free_throw_indices, 'action_category'] = desc_df.loc[free_throw_indices, 'action_category']
        game_events.loc[free_throw_indices, 'ft_num'] = desc_df.loc[free_throw_indices, 'ft_num']
        game_events.loc[free_throw_indices, 'ft_total'] = desc_df.loc[free_throw_indices, 'ft_total']
    return game_events

def add_rebound_actions(game_events):
    not_null_actions = 'action_category==action_category'
    null_actions = 'action_category!=action_category'
    for team in ['home','away','neutral']:
        desc_field = '{}_description'.format(team)
        if team != 'neutral':
            team_field = '{}_team_id'.format(team)
            criteria = "eventmsgtype==4 and {}=={} and team_id=={}".format(desc_field, desc_field, team_field)
        else:
            criteria = "eventmsgtype==4 and {}=={}".format(desc_field, desc_field)
        cols=['game_id','period','sec_remain','model_event_num','sub_event_num','person_id','team_id','home_poss','away_poss','home_team_id', desc_field]
        desc_df = game_events.query(criteria)[cols]
        desc_df['action_category'] = None
        desc_df['action_sub_category'] = None
        desc_df['extra_info'] = None
        desc_df['player'] = None
        desc_df['extra_info'] = None

        uncommon_rebounds = ['Normal Rebound','Unknown']
        uncommon_rebound_indices = desc_df.query("{} in @uncommon_rebounds".format(desc_field)).index
        desc_df.loc[criteria, 'action_category'] = 'rebound'

        for pattern in ['(?P<player>.*)\s(?P<action_category>REBOUND)\s\((?P<extra_info>.*)\)',
                        '(?P<player>.*)\s(?P<action_category>Rebound)']:
            extract_df = desc_df[desc_field].fillna('').str.extract(pattern, expand=True)
            matched_indices = extract_df.query(not_null_actions).index.intersection(desc_df.query(null_actions).index)
            desc_df.loc[matched_indices, 'action_category'] = extract_df.loc[matched_indices, 'action_category'].str.lower()
            desc_df.loc[matched_indices, 'player'] = extract_df.loc[matched_indices, 'player']
            if 'extra_info' in extract_df.columns:
                desc_df.loc[matched_indices, 'extra_info'] = extract_df.loc[matched_indices, 'extra_info']

        desc_df['reb_type'] = None

        rebound_type_query = 'Off:(?P<off_reb>\d+)\sDef:(?P<def_reb>\d+)'
        rebound_types = desc_df['extra_info'].fillna('').str.extract(rebound_type_query, expand=True)

        for reb_type in ['off','def']:
            reb_type_string = "{}_reb".format(reb_type)
            desc_df[reb_type_string] = None
            not_null_off_reb_query = "{}=={}".format(reb_type_string, reb_type_string)
            reb_type_indices = rebound_types.query(not_null_off_reb_query).index
            desc_df.loc[reb_type_indices, reb_type_string] = rebound_types.loc[reb_type_indices, reb_type_string]
            desc_df[reb_type_string] = desc_df[reb_type_string].fillna(0).astype('int')


        desc_df = desc_df.sort_values(by=['game_id','person_id','model_event_num'])
        desc_df['game_id_shifted'] = desc_df['game_id'].shift(1).fillna(0)
        desc_df['person_id_shifted'] = desc_df['person_id'].shift(1).fillna(0)
        desc_df['off_reb_shifted'] = desc_df['off_reb'].shift(1).fillna(0)
        desc_df['def_reb_shifted'] = desc_df['def_reb'].shift(1).fillna(0)

        non_match_query = "game_id!=game_id_shifted or person_id!=person_id_shifted"
        non_match_indices = desc_df.query(non_match_query).index
        desc_df.loc[non_match_indices,'off_reb_shifted'] = 0
        desc_df.loc[non_match_indices,'def_reb_shifted'] = 0

        desc_df['off_reb_change'] = desc_df['off_reb'] - desc_df['off_reb_shifted']
        desc_df['def_reb_change'] = desc_df['def_reb'] - desc_df['def_reb_shifted']

        for reb_type in ['off','def']:
            reb_change_query = "{}_reb_change == 1".format(reb_type)
            rebound_indices = desc_df.query(reb_change_query).index
            desc_df.loc[rebound_indices, 'action_category'] = "{}_reb".format(reb_type)

        off_reb_query = "action_sub_category!=action_sub_category and home_team_id==team_id and home_poss==1"
        off_reb_indices = desc_df.query(off_reb_query).index
        desc_df.loc[off_reb_indices, 'action_sub_category'] = 'off_reb'

        off_reb_query = "action_sub_category!=action_sub_category and home_team_id!=team_id and away_poss==1"
        off_reb_indices = desc_df.query(off_reb_query).index
        desc_df.loc[off_reb_indices, 'action_sub_category'] = 'off_reb'

        def_reb_query = "action_sub_category!=action_sub_category and home_team_id==team_id and home_poss==0"
        def_reb_indices = desc_df.query(def_reb_query).index
        desc_df.loc[def_reb_indices, 'action_sub_category'] = 'def_reb'

        def_reb_query = "action_sub_category!=action_sub_category and home_team_id!=team_id and away_poss==0"
        def_reb_indices = desc_df.query(def_reb_query).index
        desc_df.loc[def_reb_indices, 'action_sub_category'] = 'def_reb'

        desc_df['action_category'] = desc_df['action_sub_category']

        rebound_indices = desc_df.query(not_null_actions).index.intersection(game_events.query(null_actions).index)
        game_events.loc[rebound_indices, 'action_sub_category'] = desc_df.loc[rebound_indices, 'action_sub_category']
        game_events.loc[rebound_indices, 'action_category'] = desc_df.loc[rebound_indices, 'action_category']
    return game_events

def add_turnover_actions(game_events):
    not_null_actions = 'action_category==action_category'
    not_null_action_subs = 'action_sub_category==action_sub_category'
    null_actions = 'action_category!=action_category'
    for team in ['home','away','neutral']:
        desc_field = '{}_description'.format(team)
        if team != 'neutral':
            team_field = '{}_team_id'.format(team)
            criteria = "eventmsgtype==5 and {}=={} and team_id=={}".format(desc_field, desc_field, team_field)
        else:
            criteria = "eventmsgtype==5 and {}=={}".format(desc_field, desc_field)
        cols=['game_id','period','sec_remain','model_event_num','sub_event_num','person_id','team_id',desc_field]
        desc_df = game_events.query(criteria)[cols]
        desc_df['action_category'] = None
        desc_df['action_sub_category'] = None
        desc_df['extra_info'] = None

        steal_patterns = ['(?P<player>.*)\s(?P<action_category>STEAL)\s\((?P<extra_info>.*)\)',
                             '(?P<action_category>STEAL)\s\((?P<extra_info>.*)\)']
        for pattern in steal_patterns:
            extract_df = desc_df[desc_field].fillna('').str.extract(pattern, expand=True)
            matched_indices = extract_df.query(not_null_actions).index.intersection(desc_df.query(null_actions).index)
            desc_df.loc[matched_indices, 'action_category'] = extract_df.loc[matched_indices, 'action_category'].str.lower()
            desc_df.loc[matched_indices, 'action_sub_category'] = extract_df.loc[matched_indices, 'action_category'].str.lower()
            desc_df.loc[matched_indices, 'extra_info'] = extract_df.loc[matched_indices, 'extra_info']

        violation_tovs=('Traveling|Offensive Goaltending|3 Second Violation|'\
                        'Discontinue Dribble|Double Dribble|Backcourt|Palming|'\
                        'Kicked Ball Violation|Inbound|No|Lane Violation|'\
                        'Illegal Assist|Illegal Screen|5 Second Violation|'\
                        'Punched Ball|Basket from Below|'\
                        'Swinging Elbows|Opposite Basket|Player Out of Bounds Violation|'\
                        'Shot Clock|8 Second Violation|5 Second Inbound|Too Many Players')

        jumpball_viols=('Jump Ball Violation')

        foul_tovs=('Offensive Foul|Foul|Double Personal')

        tovs=('Out of Bounds Lost Ball|Bad Pass|Out of Bounds - Bad Pass Turnover|'\
              'Lost Ball|Step Out of Bounds|Out Of Bounds')

        for sub_types, action_category in [(foul_tovs, 'off_foul_tov'),
                                           (violation_tovs, 'off_violation'),
                                           (jumpball_viols, 'jump_violation'),
                                           (tovs, 'tov')]:
            patterns = []
            patterns.append('(?P<player>.*)\s(?P<action_sub_category>{})\sTurnover\s\((?P<extra_info>.*)\)'.format(sub_types))
            patterns.append('(?P<player>.*)\sTurnover:\s(?P<action_sub_category>{})\s\((?P<extra_info>.*)\)'.format(sub_types))
            patterns.append('\sTurnover:\s(?P<action_sub_category>{})\s\((?P<extra_info>.*)\)'.format(sub_types))
            patterns.append('(?P<action_sub_category>{})\sTurnover\s\((?P<extra_info>.*)\)'.format(sub_types))

            for pattern in patterns:
                extract_df = desc_df[desc_field].fillna('').str.extract(pattern, expand=True)
                matched_indices = extract_df.query(not_null_action_subs).index.intersection(desc_df.query(null_actions).index)
                desc_df.loc[matched_indices, 'action_category'] = action_category
                desc_df.loc[matched_indices, 'action_sub_category'] = extract_df.loc[matched_indices, 'action_sub_category'].str.lower()

        team_indices = desc_df.query('team_id==person_id').index
        desc_df.loc[team_indices, 'action_sub_category'] = 'unknown'
        desc_df.loc[team_indices, 'action_category'] = 'off_violation'

        turnover_indices = desc_df.query(not_null_actions).index.intersection(game_events.query(null_actions).index)
        game_events.loc[turnover_indices, 'action_sub_category'] = desc_df.loc[turnover_indices, 'action_sub_category']
        game_events.loc[turnover_indices, 'action_category'] = desc_df.loc[turnover_indices, 'action_category']

    steal_action = get_steal_action_categories(game_events)
    steal_indices = steal_action.index
    game_events.loc[steal_indices, 'action_category'] = steal_action.loc[steal_indices]

    return game_events

def get_steal_action_categories(game_events):
    action_columns = ['game_id','model_event_num','action_category']

    steal_query = "action_category=='steal'"
    steals = game_events.query(steal_query)[action_columns]
    steals = pd.merge(left=game_events[action_columns[:2]].reset_index(),
                      right=steals,
                      on=action_columns[:2],
                      how='inner').set_index('index')['action_category']
    return steals

def add_foul_actions(game_events):
    not_null_actions = 'action_sub_category==action_sub_category'
    null_actions = 'action_sub_category!=action_sub_category'

    for team in ['home','away','neutral']:
        desc_field = '{}_description'.format(team)
        criteria = "eventmsgtype==6 and {}=={}".format(desc_field, desc_field)
        cols=['game_id','period','sec_remain','model_event_num','sub_event_num','person_id','team_id',desc_field]
        desc_df = game_events.query(criteria)[cols]
        desc_df['action_category'] = None
        desc_df['action_sub_category'] = None
        desc_df['team'] = None
        desc_df['pers_foul'] = 0
        desc_df['team_foul'] = 0

        player_name_regex = ('\w+\sa\s\w+|\w+\-\w+\sJr.|\w+\-\w+\sJr|\w+\-\w+|'\
                             '\w+\sII|\w+\sIII|\w+\sIV|\w+\sV|\w+\sJr\.|\w+\,\sJr\.|'\
                             '\w+\sJr|\w+\,\sJr|\w+\sSr\.|\w+\,\sSr\.|\w+\sSr|'\
                             '\w+\,\sSr|\w+\s\w+|\w+')

        action_sub_cat_regex = ('\w+\.\w+|\w+\.\w+\.\w+|\w+\.\w+\.\w+\.\w+|\w+\s\w+\s\w+|'\
                                'Non-Unsportsmanlike|Taunting|Indirect Technical')

        neutral_fouls_regex = ('Foul:T.FOUL|Double Technical|Foul : Double Personal|Delay Technical|'\
                               'Foul:DOUBLE.TECHNICAL.FOUL|Excess Timeout Technical|'\
                               'Too Many Players Technical|Foul:Non-Unsportsmanlike|Defense 3 Second')

        for pattern in ['(?P<player>\.*)\s(?P<action_sub_category>T.FOUL|T.Foul)\s(?P<extra_info>.*\s\d\sSec\s.*)',
                        '(?P<player>\w+)\s(?P<action_sub_category>Delay|T.FOUL|T.Foul|Excess Timeout Technical)\s(?P<extra_info>.*)',
                        '(?P<player>\w+)\s(?P<action_sub_category>Delay|T.FOUL|T.Foul|Excess Timeout Technical)',
                        '(?P<action_sub_category>P\.FOUL|S\.FOUL|L\.B\.FOUL|OFF\.FOUL|OFF\.Foul|Personal Take Foul)\s(?P<extra_info>.*)',
                        '(?P<player>{})\s(?P<action_sub_category>{})\s(?P<extra_info>.*)'.format(player_name_regex, action_sub_cat_regex),
                        '(?P<action_sub_category>{})\s.*'.format(neutral_fouls_regex),
                        '.*(?P<action_sub_category>{})\s.*'.format(neutral_fouls_regex),
                        '.*(?P<action_sub_category>{})'.format(neutral_fouls_regex)]:
            extract_df = desc_df[desc_field].fillna('').str.extract(pattern, expand=True)
            extract_df['pers_foul'] = None
            extract_df['team_foul'] = None
            extract_df['team'] = None
            extract_df['official'] = None
            if 'extra_info' in extract_df.columns:
                pattern = '(?P<foul_details>.*)\) \((?P<official>.*)'
                extra_info = extract_df['extra_info'].fillna('').str.extract(pattern, expand=True)

                extra_info['foul_details'] = extra_info['foul_details'].fillna('').str.replace('\(','')
                extra_info['foul_details'] = extra_info['foul_details'].fillna('').str.replace('\)','')
                def_3_sec_indices = extra_info.query("foul_details.str.contains('Def. 3 Sec')").index
                if len(def_3_sec_indices):
                    extract_df.loc[def_3_sec_indices, 'action_sub_category'] = 'Defense 3 Second'
                    extract_df.loc[def_3_sec_indices, 'team'] = extract_df.loc[def_3_sec_indices, 'player'].str.title()

                for pattern in ['P(?P<pers_foul>\d+)\.T(?P<team_foul>\d+)',
                                'P(?P<pers_foul>\d+)$',
                                'P(?P<pers_foul>\d+)\.(?P<team_foul>PN)']:
                    foul_cnt = extra_info['foul_details'].fillna('').str.extract(pattern, expand=True)
                    not_null_fouls = 'pers_foul == pers_foul'
                    null_fouls = 'pers_foul != pers_foul'
                    matched_indices = foul_cnt.query(not_null_fouls).index.intersection(extract_df.query(null_fouls).index)
                    extract_df.loc[matched_indices, 'pers_foul'] = 1
                    if 'team_foul' in foul_cnt.columns:
                        not_null_fouls = 'team_foul==team_foul'
                        null_fouls = 'team_foul != team_foul'
                        matched_indices = foul_cnt.query(not_null_fouls).index.intersection(extract_df.query(null_fouls).index)
                        extract_df.loc[matched_indices, 'team_foul'] = 1

                extra_info['official'] = extra_info['official'].str.replace('\)','')
                extra_info['official'] = extra_info['official'].str.replace('\(','')
                not_null_official_query = 'official==official'
                official_indices = extra_info.query(not_null_official_query).index
                extract_df.loc[official_indices, 'official'] = extra_info.loc[official_indices, 'official']

            matched_indices = extract_df.query(not_null_actions).index.intersection(desc_df.query(null_actions).index)
            desc_df.loc[matched_indices, 'action_sub_category'] = extract_df.loc[matched_indices, 'action_sub_category']
            desc_df.loc[matched_indices, 'pers_foul'] = extract_df.loc[matched_indices, 'pers_foul']
            desc_df.loc[matched_indices, 'team_foul'] = extract_df.loc[matched_indices, 'team_foul']
            desc_df.loc[matched_indices, 'official'] = extract_df.loc[matched_indices, 'official']

            # correct team technicals assigned to players
            not_null_team_query = 'team==team'
            team_technical = extract_df.query(not_null_team_query).index
            game_events.loc[team_technical, 'person_name'] = extract_df.loc[team_technical, 'team']
            game_events.loc[team_technical, 'person_id'] = game_events.loc[team_technical, 'team_id']

        neutral_foul_types = ['Technical', 'Shooting', 'Inbound', 'Offensive', 'No Foul','Loose Ball']
        neutral_foul_query = "{}.isin(@neutral_foul_types) and action_sub_category!=action_sub_category".format(desc_field)
        neutral_foul_indices = desc_df.query(neutral_foul_query).index
        desc_df.loc[neutral_foul_indices, 'action_sub_category'] = desc_df.loc[neutral_foul_indices, desc_field]

        action_category_map = {'L.B.FOUL':'pf_loose', 'Loose Ball':'pf_loose',
                               'AWAY.FROM.PLAY.FOUL':'pf_away_play', 'PUNCH.FOUL':'pf_punch',
                               'P.FOUL':'pf_def', 'C.P.FOUL':'pf_def',
                               'Personal Block Foul':'pf_def','IN.FOUL':'pf_def','Inbound':'pf_def',
                               'Personal Take Foul':'pf_def',
                               'S.FOUL':'pf_def_sf', 'Shooting Block Foul':'pf_def_sf', 'Shooting':'pf_def_sf',
                               'OFF.Foul':'pf_off', 'Offensive':'pf_off', 'Offensive Charge Foul':'pf_off_charge',
                               'T.Foul':'tech', 'T.FOUL':'tech', 'Foul:T.FOUL':'tech', 'Technical':'tech',
                               'Double Technical':'tech_dbl', 'Foul:DOUBLE.TECHNICAL.FOUL':'tech_dbl',
                               'Delay':'delay_tech', 'Delay Technical':'delay_tech',
                               'Indirect Technical':'violation_tech', 'HANGING.TECH.FOUL':'violation_tech',
                               'Many Players Tech':'violation_tech', 'Non-Unsportsmanlike':'violation_tech',
                               'Excess Timeout Technical':'violation_tech', 'Too Many Players Technical':'violation_tech',
                               'Defense 3 Second':'violation_tech', 'Foul:Non-Unsportsmanlike':'violation_tech',
                               'Foul : Double Personal':'pf_dbl',
                               'FLAGRANT.FOUL.TYPE1':'flag_1',
                               'FLAGRANT.FOUL.TYPE2':'flag_2',
                               'Taunting':'pf_taunt',
                               'NO.FOUL':'pf_def', 'No Foul':'pf_def'}

        desc_df['action_category'] = desc_df['action_sub_category'].replace(action_category_map)

        foul_indices = desc_df.query(not_null_actions).index.intersection(game_events.query(null_actions).index)
        game_events.loc[foul_indices, 'action_category'] = desc_df.loc[foul_indices, 'action_category']
        game_events.loc[foul_indices, 'action_sub_category'] = desc_df.loc[foul_indices, 'action_sub_category'].str.lower()
        game_events.loc[foul_indices, 'official'] = desc_df.loc[foul_indices, 'official']

        if team != 'neutral':
            team_field = '{}_team_id'.format(team)
            excluded_fouls = 'tech','tech_dbl','delay_tech','violation_tech','flag_1','flag_2'
            criteria = "team_id=={} and action_category not in @excluded_fouls".format(team_field)
            team_id_indices = foul_indices.intersection(game_events.query(criteria).index)
            game_events.loc[team_id_indices, 'pers_foul'] = desc_df.loc[team_id_indices, 'pers_foul'].fillna(0)
            game_events.loc[team_id_indices, 'team_foul'] = desc_df.loc[team_id_indices, 'team_foul'].fillna(0)
            criteria = "team_id=={} and action_category in @excluded_fouls".format(team_field)
            team_id_indices = foul_indices.intersection(game_events.query(criteria).index)
            game_events.loc[team_id_indices, 'pers_foul'] = 0
            game_events.loc[team_id_indices, 'team_foul'] = 0
        else:
            game_events.loc[foul_indices, 'pers_foul'] = 0
            game_events.loc[foul_indices, 'team_foul'] = 0

    shooting_foul_action = get_shooting_foul_action_categories(game_events)
    shooting_foul_indices = shooting_foul_action.index
    game_events.loc[shooting_foul_indices, 'action_category'] = shooting_foul_action.loc[shooting_foul_indices]

    return game_events

def get_shooting_foul_actions(game_events):
    cols = ['game_id','period','sec_remain','person_id','model_event_num']
    shooting_fouls = "'s.foul','shooting block foul','shooting'"
    foul_action_query = "eventmsgtype==6 and action_sub_category.isin([{}])".format(shooting_fouls)
    return game_events.query(foul_action_query)[cols]

def get_free_throw_actions(game_events):
    excl_free_throws = ['free throw technical','free throw technical miss',
                        'free throw flagrant','free throw flagrant miss']
    foul_action_query = "eventmsgtype==3 and action_sub_category not in @excl_free_throws"
    group_cols = ['game_id','period','sec_remain','person_id']
    return game_events.query("eventmsgtype==3").groupby(group_cols)['ft_total'].min().reset_index()

def get_shooting_foul_action_categories(game_events):
    merge_cols = ['game_id','period','sec_remain','person_id']
    free_throw_actions = get_free_throw_actions(game_events)
    foul_actions = get_shooting_foul_actions(game_events)
    shooting_foul_ft_total = (foul_actions.reset_index()
                                          .merge(free_throw_actions, on=merge_cols, how='inner')
                                          .set_index('index'))
    fgm_query = ("ft_total=='1'")
    fgm_indices = shooting_foul_ft_total.query(fgm_query).index
    shooting_foul_ft_total.loc[fgm_indices,'action_category'] = 'pf_def_sf_fgm'
    fgm_query = ("ft_total=='2'")
    fgm_indices = shooting_foul_ft_total.query(fgm_query).index
    shooting_foul_ft_total.loc[fgm_indices,'action_category'] = 'pf_def_sf_fg2a'
    fgm_query = ("ft_total=='3'")
    fgm_indices = shooting_foul_ft_total.query(fgm_query).index
    shooting_foul_ft_total.loc[fgm_indices,'action_category'] = 'pf_def_sf_fg3a'
    shooting_foul_action = pd.merge(left=game_events[['game_id','model_event_num']].reset_index(),
                                    right=shooting_foul_ft_total,
                                    on=['game_id','model_event_num'],
                                    how='inner').set_index('index')['action_category']
    new_index = (shooting_foul_action.index.duplicated(keep='first') == False)
    shooting_foul_action = shooting_foul_action[new_index]
    return shooting_foul_action

def add_violation_categories(game_events):
    not_null_actions = 'action_sub_category==action_sub_category'
    null_actions = 'action_category!=action_category'
    for team in ['home','away','neutral']:
        desc_field = '{}_description'.format(team)
        if team != 'neutral':
            team_field = '{}_team_id'.format(team)
            criteria = "eventmsgtype==7 and {}=={} and team_id=={}".format(desc_field, desc_field, team_field)
        else:
            criteria = "eventmsgtype==7 and {}=={}".format(desc_field, desc_field)
        cols=['game_id','period','sec_remain','model_event_num','sub_event_num','person_id','team_id',desc_field]
        desc_df = game_events.query(criteria)[cols]
        desc_df['action_category'] = None
        desc_df['action_sub_category'] = None
        desc_df['extra_info'] = None

        action_category_map = {'defensive goaltending':'def_violation',
                               'kicked ball':'def_violation',
                               'jump ball':'def_jump_violation',
                               'lane':'def_free_throw_violation',
                               'double lane':'def_free_throw_violation',
                               'delay of game violation':'delay_violation',
                               'delay of game':'delay_violation',
                               'no violation':'def_violation'}

        for pattern in ['(?P<player>.*)\sViolation:(?P<action_sub_category>.*)\s\((?P<extra_info>.*)\)',
                        '(?P<player>.*)\sViolation:(?P<action_sub_category>.*)']:
            extract_df = desc_df[desc_field].fillna('').str.extract(pattern, expand=True)
            matched_indices = extract_df.query(not_null_actions).index.intersection(desc_df.query(null_actions).index)
            desc_df.loc[matched_indices, 'action_sub_category'] = extract_df.loc[matched_indices, 'action_sub_category'].str.lower().str.strip()
            desc_df.loc[matched_indices, 'action_category'] = desc_df.loc[matched_indices, 'action_sub_category'].replace(action_category_map)

        criteria = "{}.isin(['Delay Of Game', 'Kicked Ball', 'No Violation']) and action_category!=action_category".format(desc_field)
        remaining_indices = desc_df.query(criteria).index
        desc_df.loc[remaining_indices, 'action_sub_category'] = desc_df.loc[remaining_indices, desc_field]
        desc_df.loc[remaining_indices, 'action_category'] = desc_df.loc[remaining_indices, 'action_sub_category'].replace(action_category_map)

        violation_indices = desc_df.query(not_null_actions).index.intersection(game_events.query(null_actions).index)
        game_events.loc[violation_indices, 'action_sub_category'] = desc_df.loc[violation_indices, 'action_sub_category']
        game_events.loc[violation_indices, 'action_category'] = desc_df.loc[violation_indices, 'action_category']
    return game_events

def add_sub_actions(game_events):
    criteria = "game_events[((game_events['eventmsgtype']==8) & (game_events['sub_event_num']==1))].index"
    game_events.loc[pd.eval(criteria), 'action_category'] = 'substitution'
    game_events.loc[pd.eval(criteria), 'action_sub_category'] = 'sub_out'
    criteria = "game_events[((game_events['eventmsgtype']==8) & (game_events['sub_event_num']!=1))].index"
    game_events.loc[pd.eval(criteria), 'action_category'] = 'substitution'
    game_events.loc[pd.eval(criteria), 'action_sub_category'] = 'sub_in'
    return game_events

def add_timeout_actions(game_events):
    criteria = "game_events[game_events['eventmsgtype']==9].index"
    game_events.loc[pd.eval(criteria), 'action_category'] = 'timeout'
    game_events.loc[pd.eval(criteria), 'action_sub_category'] = 'timeout'
    return game_events

def add_jumpball_actions(game_events):
    criteria = "game_events[((game_events['eventmsgtype']==10) & (game_events['sub_event_num']!=3))].index"
    game_events.loc[pd.eval(criteria), 'action_category'] = 'jumpball'
    game_events.loc[pd.eval(criteria), 'action_sub_category'] = 'jump_part'
    criteria = "game_events[((game_events['eventmsgtype']==10) & (game_events['sub_event_num']==3))].index"
    game_events.loc[pd.eval(criteria), 'action_category'] = 'jumpball'
    game_events.loc[pd.eval(criteria), 'action_sub_category'] = 'jump_poss'
    return game_events

def add_ejection_actions(game_events):
    criteria = "game_events[game_events['eventmsgtype']==11].index"
    game_events.loc[pd.eval(criteria), 'action_category'] = 'ejection'
    game_events.loc[pd.eval(criteria), 'action_sub_category'] = 'ejection'
    return game_events

def add_period_start_actions(game_events):
    criteria = "game_events[game_events['eventmsgtype']==12].index"
    game_events.loc[pd.eval(criteria), 'action_category'] = 'period_start'
    return game_events

def add_period_end_actions(game_events):
    criteria = "game_events[game_events['eventmsgtype']==13].index"
    game_events.loc[pd.eval(criteria), 'action_category'] = 'period_end'
    return game_events

def fill_missing_sequence(game_events):
    fill_cols = ['home_pts','away_pts','home_poss','away_poss','sec_remain']
    game_events.loc[:,fill_cols] = (game_events.groupby(['game_id'])[fill_cols]
                                               .bfill()
                                               .ffill()
                                               .astype('int'))
    return game_events

def add_stat_categories(game_events):
    action_category_stat_msgs = [3,5,6,7]
    indices = game_events.query("eventmsgtype in @action_category_stat_msgs").index
    game_events.loc[indices, 'stat_category'] = game_events.loc[indices, 'action_category']

    action_sub_category_stat_msgs = [1,2,4,8,9,10,11]
    indices = game_events.query("eventmsgtype in @action_sub_category_stat_msgs").index
    game_events.loc[indices, 'stat_category'] = game_events.loc[indices, 'action_sub_category']

    excluded_action_sub_categories = ['sub_out','period_start','period_end']
    indices = game_events.query("action_sub_category in @excluded_action_sub_categories").index
    game_events.loc[indices, 'stat_category'] = None

    stat_category_map = {'assist':'ast',
                         'block':'blk',
                         'steal':'stl',
                         'free throw technical':'ftm_tech',
                         'free throw technical miss':'fta_tech',
                         'free throw flagrant':'ftm',
                         'free throw flagrant miss':'fta',
                         'free throw clear path':'ftm',
                         'free throw clear path miss':'fta',
                         'free throw':'ftm',
                         'free throw miss':'fta',
                         'pf_def_sf_fg2a':'pf_def_sf',
                         'pf_def_sf_fg3a':'pf_def_sf',
                         'pf_def_sf_fgm':'pf_def_sf',
                         'pf_loose':'pf',
                         'pf_away_play':'pf',
                         'pf_punch':'pf',
                         'sub_in':'shift',
                         'pf_off_charge':'pf',
                         'off_foul_tov':'tov',
                         'jump_violation':'tov',
                         'tech_dbl':'tech',
                         'delay_tech':'violation_tech',
                         'pf_dbl':'pf',
                         'pf_taunt':'pf',
                         'def_jump_violation':'def_violation',
                         'def_free_throw_violation':'def_violation',
                         'def_free_throw_violation':'def_violation'}


    game_events['stat_category'] = game_events['stat_category'].replace(stat_category_map)
    return game_events
