from datetime import datetime
from ..utilities.collection_functions import (request_data, set_status_values)
from nba_data.utilities.collection_config import (nba_league_id_dict,
                                                  nba_headers,
                                                  basketball_stats_urls,
                                                  period_min,
                                                  ot_min)

def create_nba_staging_instances(instance_template,
                                 rename_dict,
                                 **kwargs):
    # 1. StageBoxScore (season, sport, endpoint, game_id)
    # 2. StageGameSummary (season, sport, endpoint, game_id)
    # 3. StagePeriodStarters (season, sport, endpoint, game_id, range_type, period, start_range, end_range)
    # 4. StagePlayByPlay (season, sport, endpoint, game_id)
    # 5. StageSchedule (season, sport, endpoint, date)
    # 6. StageSeason (season, sport, endpoint, season_type, participant)
    # 7. StageShotChart (season, sport, endpoint, season_type, start_date, end_date, context, player_id, team_id)
    # 8. StageWinProb (season, sport, endpoint, game_id)
    instance = init_instance(instance_template)
    req_response = request_nba_endpoint(**kwargs)
    instance = fill_staging_json(instance, req_response)
    instance = fill_league_id(instance, kwargs.get('sport'))
    instance = fill_url(instance, req_response)
    instance = fill_status_fields(instance, req_response)
    instance = fill_load_date(instance)
    for key, value in kwargs.items():
        if key in instance:
            instance.update({key: value})
    instance = rename_instance_fields(rename_dict, instance)
    return instance

def init_instance(instance_template):
    instance = dict([(key, value) for key, value in instance_template.items()])
    return instance

def request_nba_endpoint(**kwargs):
    endpoint = kwargs.get('endpoint')
    base_url = set_base_url(endpoint, kwargs.get('sport'))
    league_id = nba_league_id_dict[kwargs.get('sport')]
    if endpoint == 'box_score':
        params = set_basketball_params(GameID=kwargs.get('game_id'),
                                       RangeType=0,
                                       StartPeriod=1,
                                       EndPeriod=14,
                                       StartRange=0,
                                       EndRange=0)
    elif endpoint == 'game_summary':
        params = set_basketball_params(GameID=kwargs.get('game_id'))
    elif endpoint == 'player':
        params = set_basketball_params(PlayerID=kwargs.get('player_id'),
                                       LeagueID='')
    elif endpoint == 'win_prob':
        params = set_basketball_params(GameID=kwargs.get('game_id'),
                                       RunType='each second')
    elif endpoint == 'period_starters':
        params = set_basketball_params(GameID=kwargs.get('game_id'),
                                       RangeType=kwargs.get('range_type'),
                                       StartPeriod=kwargs.get('period'),
                                       EndPeriod=kwargs.get('period'),
                                       StartRange=kwargs.get('start_range'),
                                       EndRange=kwargs.get('end_range'))
    elif endpoint == 'pbp':
        params = set_basketball_params(GameID=kwargs.get('game_id'),
                                       StartPeriod=1,
                                       EndPeriod=14)
    elif endpoint == 'schedule':
        game_date = kwargs.get('date').strftime('%Y-%m-%d')
        params = set_basketball_params(DayOffset='0',
                                       LeagueID=league_id,
                                       GameDate=game_date)
    elif endpoint == 'roster':
        season = kwargs.get('season')
        team_id = kwargs.get('team_id')
        season_string='{}-{}'.format(season, int(season) + 1 - 2000)
        params = set_basketball_params(LeagueID=None,
                                       Season=season_string,
                                       TeamID=team_id)
    elif endpoint == 'season':
        season = kwargs.get('season')
        date_to = kwargs.get('date_to').strftime('%Y-%m-%d')
        try:
            date_from = kwargs.get('date_from').strftime('%Y-%m-%d')
        except AttributeError:
            date_from = None
        season_string = '{}-{}'.format(str(season), str(season + 1 - 2000))
        params = set_basketball_params(Counter=0,
                                       Direction='ASC',
                                       LeagueID=league_id,
                                       DateTo=date_to,
                                       DateFrom=date_from,
                                       PlayerOrTeam=kwargs.get('participant'),
                                       Season=season_string,
                                       SeasonType=kwargs.get('season_type'),
                                       Sorter='DATE')
    elif endpoint == 'shot_chart':
        date_from = kwargs.get('start_date').strftime('%Y-%m-%d')
        date_to = kwargs.get('end_date').strftime('%Y-%m-%d')
        params = set_basketball_params(AheadBehind='',
                                       ClutchTime='',
                                       ContextFilter='',
                                       ContextMeasure=kwargs.get('context'),
                                       DateFrom=date_from,
                                       DateTo=date_to,
                                       EndPeriod='',
                                       EndRange='',
                                       GameID='',
                                       GameSegment='',
                                       LastNGames='0',
                                       LeagueID=league_id,
                                       Location='',
                                       Month='0',
                                       OpponentTeamID='0',
                                       Outcome='',
                                       Period='0',
                                       PlayerID=kwargs.get('player_id'),
                                       PlayerPosition='',
                                       PointDiff='',
                                       Position='',
                                       RangeType='',
                                       RookieYear='',
                                       Season='',
                                       SeasonSegment='',
                                       SeasonType=kwargs.get('season_type'),
                                       StartPeriod='',
                                       StartRange='',
                                       TeamID=kwargs.get('team_id'),
                                       VsConference='',
                                       VsDivision='')
    Proxies = kwargs.get('proxies')
    req_response = request_data(base_url,
                                params,
                                nba_headers,
                                Proxies)
    return req_response

def set_base_url(endpoint, sport):
    return basketball_stats_urls[endpoint][sport]

def set_basketball_params(**kwargs):
    params = dict([(key, value) for key, value in kwargs.items()])
    return params

def fill_staging_json(instance, req_response):
    if req_response.ok:
        try:
            instance['json'] = req_response.json()
        except ValueError:
            instance['json'] = None
            instance['status_reason'] = 'Invalid JSON'
    else:
        instance['json'] = None
    return instance

def fill_league_id(instance, sport):
    if 'league_id' in instance:
        instance['league_id'] = nba_league_id_dict[sport]
    return instance

def fill_url(instance, req_response):
    if 'url' in instance:
        instance['url'] = req_response.url
    return instance

def fill_status_fields(instance, req_response):
    status_code, status_reason = set_status_values(req_response)
    if 'status_code' in instance:
        instance['status_code'] = status_code
    if 'status_reason' in instance:
        instance['status_reason'] = status_reason
    return instance

def fill_load_date(instance):
    if 'load_date' in instance:
        instance['load_date'] = datetime.now()
    return instance

def rename_instance_fields(rename_dict, instance):
    for old_key, new_key in rename_dict.items():
        if old_key in instance:
            instance.update({new_key:instance.pop(old_key)})
    return instance

def get_starter_params(instance):
    starter_params = []
    period_set = set()
    minutes_in_period = period_min[instance['sport']]
    minutes_in_ot = ot_min[instance['sport']]
    if instance['json'] is not None:
        dict_col_names = instance['json']['resultSets'][0]['headers']
        for game in instance['json']['resultSets'][0]['rowSet']:
            play_details = dict(zip(dict_col_names, game))
            if play_details['EVENTMSGTYPE'] not in [10, 12, 13]:
                period = play_details['PERIOD']
                game_id = play_details['GAME_ID']
                range_type = 2
                if period not in period_set:
                    period_set |= {period}
                    time_remain = play_details['PCTIMESTRING'].split(':')
                    sec_remaining = (int(time_remain[0]) * 60 + int(time_remain[1]))
                    if period < 5:
                        game_sec_elapsed = ((period - 1) * minutes_in_period * 60) * 10
                        first_event = (game_sec_elapsed
                                       + (minutes_in_period * 60 - sec_remaining) * 10)
                    else:
                        game_sec_elapsed = (4 * minutes_in_period * 60
                                              + (period - 4) * minutes_in_ot * 60) * 10
                        first_event = (game_sec_elapsed
                                       + (minutes_in_ot * 60 - sec_remaining) * 10)
                    lookup_tuple = (game_id,
                                    range_type,
                                    period,
                                    game_sec_elapsed,
                                    first_event)
                    starter_params.append(lookup_tuple)
    return starter_params

def get_game_dates(season_instance):
    game_dates = set()
    if season_instance['json'] is not None:
        if 'resultSets' in season_instance['json']:
            for result in season_instance['json']['resultSets']:
                if 'name' in result:
                    if result['name'] == 'LeagueGameLog':
                        if 'rowSet' in result:
                            fields = [f.lower() for f in result['headers']]
                            for player_game in result['rowSet']:
                                player_record = dict(zip(fields, player_game))
                                game_date = datetime.strptime(player_record['game_date'],
                                                              '%Y-%m-%d')
                                game_dates |= {game_date}
    return game_dates


def get_games_played(season_instance):
    games_played = set()
    if season_instance['json'] is not None:
        if 'resultSets' in season_instance['json']:
            for result in season_instance['json']['resultSets']:
                if 'name' in result:
                    if result['name'] == 'LeagueGameLog':
                        if 'rowSet' in result:
                            fields = [f.lower() for f in result['headers']]
                            for player_game in result['rowSet']:
                                player_record = dict(zip(fields, player_game))
                                games_played |= {(player_record['game_id'], )}
    return games_played

def get_teams(season_instance):
    sport_lookup = dict((value, key) for key, value in nba_league_id_dict.items())
    teams = set()
    if season_instance['json'] is not None:
        if 'resultSets' in season_instance['json']:
            for result in season_instance['json']['resultSets']:
                if 'name' in result:
                    if result['name'] == 'LeagueGameLog':
                        if 'rowSet' in result:
                            fields = [f.lower() for f in result['headers']]
                            for player_game in result['rowSet']:
                                player_record = dict(zip(fields, player_game))
                                sport = sport_lookup[player_record['game_id'][:2]]
                                season = int(player_record['season_id'][-4:])
                                team_id = player_record['team_id']
                                teams |= {(sport, season, team_id)}
    return teams

def get_players(season_instance):
    players = set()
    if season_instance['json'] is not None:
        if 'resultSets' in season_instance['json']:
            for result in season_instance['json']['resultSets']:
                if 'name' in result:
                    if result['name'] == 'LeagueGameLog':
                        if 'rowSet' in result:
                            fields = [f.lower() for f in result['headers']]
                            for player_game in result['rowSet']:
                                player_record = dict(zip(fields, player_game))
                                players |= {(player_record['player_id'], )}
    return players

def get_shot_chart_players(season_instance, date_list):
    dates = set(dt.strftime('%Y-%m-%d') for dt in date_list)
    shot_chart_players = set()
    if season_instance['json'] is not None:
        if 'resultSets' in season_instance['json']:
            for result in season_instance['json']['resultSets']:
                if 'name' in result:
                    if result['name'] == 'LeagueGameLog':
                        if 'rowSet' in result:
                            fields = [f.lower() for f in result['headers']]
                            for player_game in result['rowSet']:
                                player_record = dict(zip(fields, player_game))
                                if 'game_date' in player_record:
                                    if player_record['game_date'] in dates:
                                        team_id = player_record['team_id']
                                        player_id = player_record['player_id']
                                        arg_tuple = (team_id, player_id)
                                        shot_chart_players |= {arg_tuple}
    return shot_chart_players
