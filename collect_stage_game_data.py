from datetime import datetime
from datetime import timedelta
from sqlalchemy import (and_, func)
from nba_data.utilities.proxy_queue import Proxies
from nba_data.utilities.sqlalchemy_utilities import bulk_insert_records
from nba_data.utilities.collection_config import (nba_league_id_dict,
                                                  period_min,
                                                  ot_min)
from nba_data.staging.db_config import (Base, Engine, Session)
from nba_data.staging.nba_staging_instances import (create_nba_staging_instances,
                                                    get_game_dates,
                                                    get_games_played,
                                                    get_starter_params,
                                                    get_teams,
                                                    get_players,
                                                    get_shot_chart_players)
from nba_data.staging.nba_staging_instance_config import (boxscores_config,
                                                          game_summary_config,
                                                          period_starters_config,
                                                          pbp_config,
                                                          schedule_config,
                                                          season_config,
                                                          shot_chart_config,
                                                          win_prob_config,
                                                          roster_config,
                                                          player_config)
from nba_data.staging.period_starters import StagePeriodStarters
from nba_data.staging.game_summary import StageGameSummary
from nba_data.staging.box_scores import StageBoxScore
from nba_data.staging.play_by_play import StagePlayByPlay
from nba_data.staging.schedule import StageSchedule
from nba_data.staging.season import StageSeason
from nba_data.staging.win_prob import StageWinProb
from nba_data.staging.shot_chart import StageShotChart
from nba_data.staging.roster import StageRoster
from nba_data.staging.player import StagePlayer
import sys

SESSION = None
SPORT = None
LEAGUE_ID = None
SEASON = None
SEASON_TYPE = None
GAME_DATE = None
GAME_ID = None
PERIOD = None
START_RANGE = None
END_RANGE = None
TEAM_ID = None
PLAYER_ID = None

SHOT_CHART_DATES = set()
SEASONS = []
SCHEDULES = []
WIN_PROBS = []
GAME_SUMMARIES = []
GAME_BOXES = []
PBPS = []
STARTERS = []
SHOT_CHARTS = []
ROSTERS = []
PLAYERS = []

MAX_SEASON_DATE = None
DOWNLOADED_DATES = None
DOWNLOADED_WIN_PROB = None
DOWNLOADED_GAME_SUMMARY = None
DOWNLOADED_GAME_BOXES = None
DOWNLOADED_PBP = None
DOWNLOADED_STARTERS = None
DOWNLOADED_ROSTERS = None
DOWNLOADED_PLAYERS = None

def get_max_season_date():
    global SESSION, SPORT, LEAGUE_ID
    max_season_date = (SESSION.query(func.max(StageSchedule.date).label('max_date_to'))
                              .filter(and_(StageSchedule.sport == SPORT,
                                           StageSchedule.league_id == LEAGUE_ID,
                                           StageSchedule.season == SEASON,
                                           StageSchedule.status_code == 200))
                              .group_by(StageSchedule.season)
                              .scalar())
    return max_season_date

def get_downloaded_dates():
    global SESSION, SPORT, LEAGUE_ID
    dates = set(SESSION.query(StageSchedule.date)
                       .filter(and_(StageSchedule.sport == SPORT,
                                    StageSchedule.league_id == LEAGUE_ID,
                                    StageSchedule.season == SEASON,
                                    StageSchedule.status_code == 200))
                             .all())
    dates = set((datetime(d[0].year, d[0].month, d[0].day),) for d in dates)
    return dates

def get_downloaded_game_ids(tableClass):
    global SESSION, SPORT, LEAGUE_ID
    query_records = set(SESSION.query(tableClass.game_id)
                               .filter(and_(tableClass.sport == SPORT,
                                            tableClass.league_id == LEAGUE_ID,
                                            tableClass.season == SEASON,
                                            tableClass.status_code == 200))
                               .all())
    return query_records

def get_downloaded_starters():
    global SESSION, SPORT, LEAGUE_ID, SEASON
    game_ids = set(SESSION.query(StagePeriodStarters.game_id,
                                 StagePeriodStarters.period)
                          .filter(and_(StagePeriodStarters.sport == SPORT,
                                       StagePeriodStarters.league_id == LEAGUE_ID,
                                       StagePeriodStarters.season == SEASON,
                                       StagePeriodStarters.status_code == 200))
                          .all())
    return game_ids

def get_downloaded_rosters():
    global SESSION, SPORT, SEASON
    rosters = set(SESSION.query(StageRoster.sport,
                                StageRoster.season,
                                StageRoster.team_id)
                          .filter(and_(StageRoster.sport == SPORT,
                                       StageRoster.season == SEASON,
                                       StageRoster.status_code == 200))
                          .all())
    return rosters

def get_downloaded_players():
    global SESSION, PLAYER_ID
    players = set(SESSION.query(StagePlayer.player_id)
                         .filter(StagePlayer.status_code == 200)
                         .all())
    return players

def get_season_instance():
    global SEASON, SPORT, SEASON_TYPE, SEASONS
    if MAX_SEASON_DATE is not None:
        date_from = MAX_SEASON_DATE + timedelta(days=1)
    else:
        date_from = None
    date_to = datetime.now().date() + timedelta(days=-1)
    season_instance = create_nba_staging_instances(season_config['instance_template'],
                                                   season_config['rename_dict'],
                                                   date_from=date_from,
                                                   date_to=date_to,
                                                   season=SEASON,
                                                   sport=SPORT,
                                                   season_type=SEASON_TYPE,
                                                   endpoint='season',
                                                   participant='P',
                                                   proxies=Proxies)
    SEASONS.append(season_instance)
    return season_instance

def get_schedule_instance():
    global SEASON, SPORT, GAME_DATE, SCHEDULES, DOWNLOADED_DATES
    schedule_instance = create_nba_staging_instances(schedule_config['instance_template'],
                                                     schedule_config['rename_dict'],
                                                     season=SEASON,
                                                     sport=SPORT,
                                                     date=GAME_DATE,
                                                     endpoint='schedule',
                                                     proxies=Proxies)
    SCHEDULES.append(schedule_instance)
    DOWNLOADED_DATES |= {(GAME_DATE, )}
    return schedule_instance

def get_win_prob_instance():
    global SEASON, SPORT, GAME_ID, WIN_PROBS, DOWNLOADED_WIN_PROB
    win_prob_instance = create_nba_staging_instances(win_prob_config['instance_template'],
                                                     win_prob_config['rename_dict'],
                                                     season=SEASON,
                                                     sport=SPORT,
                                                     endpoint='win_prob',
                                                     game_id=GAME_ID,
                                                     proxies=Proxies)
    WIN_PROBS.append(win_prob_instance)
    DOWNLOADED_WIN_PROB |= {(GAME_ID, )}
    return win_prob_instance

def get_game_summary_instance():
    global SEASON, SPORT, GAME_ID, GAME_SUMMARIES, DOWNLOADED_GAME_SUMMARY
    game_summary_instance = create_nba_staging_instances(game_summary_config['instance_template'],
                                                         game_summary_config['rename_dict'],
                                                         season=SEASON,
                                                         sport=SPORT,
                                                         game_id=GAME_ID,
                                                         endpoint='game_summary',
                                                         proxies=Proxies)
    GAME_SUMMARIES.append(game_summary_instance)
    DOWNLOADED_GAME_SUMMARY |= {(GAME_ID, )}
    return game_summary_instance

def get_game_box_instance():
    global SEASON, SPORT, GAME_ID, GAME_BOXES, DOWNLOADED_GAME_BOXES
    game_box_instance = create_nba_staging_instances(boxscores_config['instance_template'],
                                                     boxscores_config['rename_dict'],
                                                     season=SEASON,
                                                     sport=SPORT,
                                                     game_id=GAME_ID,
                                                     endpoint='box_score',
                                                     proxies=Proxies)
    GAME_BOXES.append(game_box_instance)
    DOWNLOADED_GAME_BOXES |= {(GAME_ID, )}
    return game_box_instance

def get_pbp_instance():
    global SEASON, SPORT, GAME_ID, PBPS, DOWNLOADED_PBP
    pbp_instance = create_nba_staging_instances(pbp_config['instance_template'],
                                                pbp_config['rename_dict'],
                                                season=SEASON,
                                                sport=SPORT,
                                                game_id=GAME_ID,
                                                endpoint='pbp',
                                                proxies=Proxies)
    PBPS.append(pbp_instance)
    DOWNLOADED_PBP |= {(GAME_ID, )}
    return pbp_instance

def get_period_starter_instance(pbp_instance):
    global SEASON, SPORT, GAME_ID, PERIOD, STARTERS

    minutes_in_period = period_min[pbp_instance['sport']]
    minutes_in_ot = ot_min[pbp_instance['sport']]

    period_starters = set()

    dict_col_names = pbp_instance['json']['resultSets'][0]['headers']

    for play in pbp_instance['json']['resultSets'][0]['rowSet']:
        play_details = dict(zip(dict_col_names, play))
        PERIOD = play_details['PERIOD']
        pc_time = play_details['PCTIMESTRING']
        if play_details['EVENTMSGTYPE'] not in [10,12,13]:
            if PERIOD not in period_starters:
                minutes, seconds = pc_time.split(':')
                sec_remaining = (int(minutes) * 60 + int(seconds))
                if PERIOD < 5:
                    start_range = ((PERIOD - 1) * minutes_in_period * 60) * 10
                    end_range = (start_range + (minutes_in_period * 60 - sec_remaining) * 10)
                else:
                    start_range = (4 * minutes_in_period * 60
                                          + (PERIOD - 4) * minutes_in_ot * 60) * 10
                    end_range = (start_range + (minutes_in_ot * 60 - sec_remaining) * 10)
                starter_instance = create_nba_staging_instances(period_starters_config['instance_template'],
                                                                period_starters_config['rename_dict'],
                                                                season=SEASON,
                                                                sport=SPORT,
                                                                game_id=GAME_ID,
                                                                period=PERIOD,
                                                                start_range=start_range,
                                                                end_range=end_range,
                                                                range_type=2,
                                                                endpoint='period_starters',
                                                                proxies=Proxies)
                if starter_instance['json'] is not None:
                    if len(starter_instance['json']['resultSets'][0]['rowSet']) >= 10:
                        STARTERS.append(starter_instance)
                        period_starters |= {PERIOD}
    return starter_instance

def get_shot_chart_instance():
    global SEASON, SPORT, SEASON_TYPE, START_DATE, END_DATE, CONTEXT, PLAYER_ID, \
            TEAM_ID, SHOT_CHARTS
    shot_chart_instance = create_nba_staging_instances(shot_chart_config['instance_template'],
                                                       shot_chart_config['rename_dict'],
                                                       season=SEASON,
                                                       sport=SPORT,
                                                       season_type=SEASON_TYPE,
                                                       start_date=START_DATE,
                                                       end_date=END_DATE,
                                                       context=CONTEXT,
                                                       player_id=PLAYER_ID,
                                                       team_id=TEAM_ID,
                                                       endpoint='shot_chart',
                                                       proxies=Proxies)
    SHOT_CHARTS.append(shot_chart_instance)
    return shot_chart_instance

def get_roster_instance():
    global SEASON, SPORT, TEAM_ID, ROSTERS, DOWNLOADED_ROSTERS
    roster_instance = create_nba_staging_instances(roster_config['instance_template'],
                                                   roster_config['rename_dict'],
                                                   season=SEASON,
                                                   sport=SPORT,
                                                   team_id=TEAM_ID,
                                                   endpoint='roster',
                                                   proxies=Proxies)
    ROSTERS.append(roster_instance)
    DOWNLOADED_ROSTERS |= {(SPORT, SEASON, TEAM_ID)}
    return roster_instance

def get_player_instance():
    global SPORT, PLAYER_ID, PLAYERS, DOWNLOADED_PLAYERS
    player_instance = create_nba_staging_instances(player_config['instance_template'],
                                                   player_config['rename_dict'],
                                                   sport=SPORT,
                                                   player_id=PLAYER_ID,
                                                   endpoint='player',
                                                   proxies=Proxies)
    PLAYERS.append(player_instance)
    DOWNLOADED_PLAYERS |= {(PLAYER_ID, )}
    return player_instance

def gather_nba_staging_instances():
    global STAGE_SESSION, SEASON, SEASON_TYPE, SPORT, LEAGUE_ID, SEASON_TYPE, \
           START_DATE, END_DATE, CONTEXT, TEAM_ID, PLAYER_ID, SHOT_CHART_DATES, \
           MAX_SEASON_DATE, DOWNLOADED_DATES, DOWNLOADED_WIN_PROB, \
           DOWNLOADED_GAME_SUMMARY, DOWNLOADED_GAME_BOXES, DOWNLOADED_PBP, \
           DOWNLOADED_STARTERS, DOWNLOADED_ROSTERS, DOWNLOADED_PLAYERS, \
           GAME_DATE, GAME_ID, RANGE_TYPE, PERIOD, START_RANGE, END_RANGE

    print(SEASON, SEASON_TYPE)
    season_instance = get_season_instance()
    game_dates = get_game_dates(season_instance)
    for GAME_DATE in game_dates:
        if (GAME_DATE, ) not in DOWNLOADED_DATES:
            print(GAME_DATE)
            SHOT_CHART_DATES |= {GAME_DATE}
            schedule_instance = get_schedule_instance()
    games_played = get_games_played(season_instance)
    for game_played in (games_played - DOWNLOADED_WIN_PROB):
        GAME_ID = game_played[0]
        win_prob_instance = get_win_prob_instance()
    for game_played in (games_played - DOWNLOADED_GAME_SUMMARY):
        GAME_ID = game_played[0]
        game_summary_instance = get_game_summary_instance()
    for game_played in (games_played - DOWNLOADED_GAME_BOXES):
        GAME_ID = game_played[0]
        game_box_instance = get_game_box_instance()
    for game_played in (games_played - DOWNLOADED_PBP):
        GAME_ID = game_played[0]
        pbp_instance = get_pbp_instance()
        starter_instance = get_period_starter_instance(pbp_instance)
        # for params in starter_params:
        #     (GAME_ID, RANGE_TYPE, PERIOD, START_RANGE, END_RANGE) = params
        #     if (GAME_ID, PERIOD) not in DOWNLOADED_STARTERS:
        #         starter_instance = get_period_starter_instance()
    teams = get_teams(season_instance)
    for sport, season, TEAM_ID in (teams - DOWNLOADED_ROSTERS):
        roster_instance = get_roster_instance()
    players = get_players(season_instance)
    for player in (players - DOWNLOADED_PLAYERS):
        PLAYER_ID = player[0]
        player_instance = get_player_instance()
    if len(SHOT_CHART_DATES) > 0:
        SHOT_CHART_DATES = sorted(list(SHOT_CHART_DATES))
        START_DATE = SHOT_CHART_DATES[0]
        END_DATE = SHOT_CHART_DATES[-1]
        shot_chart_players = get_shot_chart_players(season_instance,
                                                    SHOT_CHART_DATES)
        for TEAM_ID, PLAYER_ID in shot_chart_players:
            for CONTEXT in ['FGA','PF']:
                shot_chart_instance = get_shot_chart_instance()
    return True

def insert_global_record_containers():
    global SEASONS, SCHEDULES, WIN_PROBS, GAME_SUMMARIES, GAME_BOXES, PBPS, \
           STARTERS, SHOT_CHARTS, ROSTERS, PLAYERS
    # if SEASONS:
    #     bulk_insert_records(Engine,
    #                         SEASONS,
    #                         StageSeason)
    if SCHEDULES:
        bulk_insert_records(Engine,
                            SCHEDULES,
                            StageSchedule)
    if WIN_PROBS:
        bulk_insert_records(Engine,
                            WIN_PROBS,
                            StageWinProb)
    if GAME_SUMMARIES:
        bulk_insert_records(Engine,
                            GAME_SUMMARIES,
                            StageGameSummary)
    if GAME_BOXES:
        bulk_insert_records(Engine,
                            GAME_BOXES,
                            StageBoxScore)
    if PBPS:
        bulk_insert_records(Engine,
                            PBPS,
                            StagePlayByPlay)
    if STARTERS:
        bulk_insert_records(Engine,
                            STARTERS,
                            StagePeriodStarters)
    if SHOT_CHARTS:
        bulk_insert_records(Engine,
                            SHOT_CHARTS,
                            StageShotChart)
    if ROSTERS:
        bulk_insert_records(Engine,
                            ROSTERS,
                            StageRoster)
    if PLAYERS:
        bulk_insert_records(Engine,
                            PLAYERS,
                            StagePlayer)
    init_global_record_containers()
    return True

def init_global_record_containers():
    global SEASONS, SCHEDULES, WIN_PROBS, GAME_SUMMARIES, GAME_BOXES, PBPS, \
           STARTERS, SHOT_CHARTS, SHOT_CHART_DATES, ROSTERS, PLAYERS
    SEASONS = []
    SCHEDULES = []
    WIN_PROBS = []
    GAME_SUMMARIES = []
    GAME_BOXES = []
    PBPS = []
    STARTERS = []
    SHOT_CHARTS = []
    SHOT_CHART_DATES = set()
    ROSTERS = []
    PLAYERS = []
    return True

def main(season):
    global SESSION, SEASON, SPORT, LEAGUE_ID, SEASON_TYPE, MAX_SEASON_DATE, \
           DOWNLOADED_DATES, DOWNLOADED_WIN_PROB, DOWNLOADED_GAME_SUMMARY, \
           DOWNLOADED_GAME_BOXES, DOWNLOADED_PBP, DOWNLOADED_STARTERS, \
           DOWNLOADED_ROSTERS, DOWNLOADED_PLAYERS

    Base.metadata.create_all(bind=Engine, checkfirst=True)

    SEASON = season

    for SPORT in ['nba','wnba','g_lg']:
        LEAGUE_ID = nba_league_id_dict[SPORT]
        print(SPORT)
        for SEASON_TYPE in ['Regular Season','Pre Season','Playoffs', 'All Star']:
            SESSION = Session()

            MAX_SEASON_DATE = get_max_season_date()
            DOWNLOADED_DATES = get_downloaded_dates()
            DOWNLOADED_WIN_PROB = get_downloaded_game_ids(StageWinProb)
            DOWNLOADED_GAME_SUMMARY = get_downloaded_game_ids(StageGameSummary)
            DOWNLOADED_GAME_BOXES = get_downloaded_game_ids(StageBoxScore)
            DOWNLOADED_PBP = get_downloaded_game_ids(StagePlayByPlay)
            DOWNLOADED_STARTERS = get_downloaded_starters()
            DOWNLOADED_ROSTERS = get_downloaded_rosters()
            DOWNLOADED_PLAYERS = get_downloaded_players()

            gather_nba_staging_instances()

            insert_global_record_containers()

            SESSION.close()

    return True

if __name__ == "__main__":
    season = int(sys.argv[1])
    main(season)

# boxscore_advanced
# url = 'https://stats.nba.com/stats/boxscoreadvancedv2'
# params = {'GameID':'0021700807',
#           'RangeType':0,
#           'StartPeriod':1,
#           'EndPeriod':1,
#           'StartRange':0,
#           'EndRange':0}
#
# boxscore_four
# url='https://stats.nba.com/stats/boxscorefourfactorsv2'
# params = {'GameID':'0021700807',
#           'RangeType':0,
#           'StartPeriod':1,
#           'EndPeriod':1,
#           'StartRange':0,
#           'EndRange':0}
#
# boxscore_misc
# url='https://stats.nba.com/stats/boxscoremiscv2'
# params = {'GameID':'0021700807',
#           'RangeType':0,
#           'StartPeriod':1,
#           'EndPeriod':1,
#           'StartRange':0,
#           'EndRange':0}
#
# boxscore_scoring
# url='https://stats.nba.com/stats/boxscorescoringv2'
# params = {'GameID':'0021700807',
#           'RangeType':0,
#           'StartPeriod':1,
#           'EndPeriod':1,
#           'StartRange':0,
#           'EndRange':0}
#
# boxscore_traditional
# url='https://stats.nba.com/stats/boxscoretraditionalv2'
# params = {'GameID':'0021700807',
#           'RangeType':0,
#           'StartPeriod':1,
#           'EndPeriod':1,
#           'StartRange':0,
#           'EndRange':0}
#
# boxscore_usage
# url='https://stats.nba.com/stats/boxscoreusagev2'
# params = {'GameID':'0021700807',
#           'RangeType':0,
#           'StartPeriod':1,
#           'EndPeriod':1,
#           'StartRange':0,
#           'EndRange':0}
#
# boxscore_defensive
# url='https://stats.nba.com/stats/boxscoredefensive'
# params = {'GameID':'0021700807'}
#
# boxscore_matchups
# url='https://stats.nba.com/stats/boxscorematchups'
# params = {'GameID':'0021700807'}
#
# boxscore_player_track
# url = 'https://stats.nba.com/stats/boxscoreplayertrackv2'
# params = {'GameID':'0021700807'}
#
# boxscore_summary
# url='https://stats.nba.com/stats/boxscoresummaryv2'
# params = {'GameID':'0021700807'}
# # GET HUSTLE BOXSCORE STATUS AND PT STATUS
#
# dash_player_track
# url = 'https://stats.nba.com/stats/leaguedashptstats'
# params = {'College':',
#           'Conference':'',
#           'Country':'',
#           'DateFrom':game_date,
#           'DateTo':game_date,
#           'Division':'',
#           'DraftPick':'',
#           'DraftYear':'',
#           'GameScope':'',
#           'Height':'',
#           'LastNGames':0,
#           'LeagueID':'',
#           'Location':'',
#           'Month':0,
#           'OpponentTeamID':0,
#           'Outcome':'',
#           'PORound':'',
#           'PerMode':'Totals',
#           'PlayerExperience':'',
#           'PlayerOrTeam':('Player' or 'Team'),
#           'PlayerPosition':('F','C','G','C-F','F-C','G-F','F-G'),
#           'PtMeasureType':('SpeedDistance', 'Rebounding',
#                            'Possessions','CatchShoot',
#                            'PullUpShot','Defense','Drives',
#                            'Passing','ElbowTouch','PostTouch',
#                            'PaintTouch','Efficiency'),
#           'Season':'2018-19',
#           'SeasonSegment':'',
#           'SeasonType':'Regular Season',
#           'StarterBench':'',
#           'TeamID':'',
#           'VsConference':'',
#           'VsDivision':'',
#           'Weight':''}
#
# dash_player_track_defend
# url = 'https://stats.nba.com/stats/leaguedashptdefend'
# params = {'College':',
#           'Conference':'',
#           'Country':'',
#           'DateFrom':game_date,
#           'DateTo':game_date,
#           'DefenseCategory':('Overall','3 Pointers','2 Pointers',
#                              'Less Than 6Ft','Less Than 10Ft',
#                              'Greater Than 15Ft'),
#           'Division':'',
#           'DraftPick':'',
#           'DraftYear':'',
#           'GameSegment':'',
#           'Height':'',
#           'LastNGames':'',
#           'LeagueID':'00',
#           'Location':'',
#           'Month':'',
#           'OpponentTeamID':'',
#           'Outcome':'',
#           'PORound':'',
#           'PerMode':'Totals',
#           'Period':'',
#           'PlayerExperience':'',
#           'PlayerID':'',
#           'PlayerPosition':'',
#           'Season':'2018-19',
#           'SeasonSegment':'',
#           'SeasonType':'Regular Season',
#           'StarterBench':'',
#           'TeamID':'',
#           'VsConference':'',
#           'VsDivision':'',
#           'Weight':''}
#
# dash_player_track_shots
# url = 'https://stats.nba.com/stats/playerdashptshots'
# params = {'DateFrom':'',
#           'DateTo':'',
#           'GameSegment':'',
#           'LastNGames':0,
#           'LeagueID':'00',
#           'Location':'',
#           'Month':0,
#           'OpponentTeamID':0,
#           'Outcome':'',
#           'PerMode':'Totals',
#           'Period':0,
#           'PlayerID':2544,
#           'Season';'2018-19',
#           'SeasonSegment':'',
#           'SeasonType':'Regular Season',
#           'TeamID':1610612739,
#           'VsConference':'',
#           'VsDivision':''}
#
#
# shot_chart:
# url = 'https://stats.nba.com/stats/shotchartdetail
# params = {'AheadBehind':'',
#           'ClutchTime':'',
#           'ContextFilter':'',
#           'ContextMeasure':('FGA' or 'PF'),
#           'DateFrom':'',
#           'DateTo':'',
#           'EndPeriod':'',
#           'EndRange':'',
#           'GameID':'',
#           'GameSegment':'',
#           'LastNGames':'0',
#           'LeagueID':('00' or '10', or '20'),
#           'Location':'',
#           'Month':'0',
#           'OpponentTeamID':'0',
#           'Outcome':'',
#           'Period':'0',
#           'PlayerID':2544,
#           'PlayerPosition':'',
#           'PointDiff':'',
#           'Position':'',
#           'RangeType':'',
#           'RookieYear':'',
#           'Season':'',
#           'SeasonSegment':'',
#           'SeasonType':'Regular Season',
#           'StartPeriod':'',
#           'StartRange':'',
#           'TeamID':1610612739,
#           'VsConference':'',
#           'VsDivision':''}
#
#
# url = 'https://stats.nba.com/stats/leaguedashplayerbiostats'
# params = {'College':'',
#           'Conference':'',
#           'Country':'',
#           'DateFrom':'',
#           'DateTo':'',
#           'Division':'',
#           'DraftPick':'',
#           'DraftYear':'',
#           'GameScope':'',
#           'GameSegment':'',
#           'Height':'',
#           'LastNGames':'',
#           'LeagueID':('00' or '10', or '20'),
#           'Location':'',
#           'Month':'',
#           'OpponentTeamID':'',
#           'Outcome':'',
#           'PORound':'',
#           'PerMode':'Totals',
#           'Period':'',
#           'PlayerExperience':'',
#           'PlayerPosition':'',
#           'Season':'2018-19',
#           'SeasonSegment':'',
#           'SeasonType':'Regular Season',
#           'ShotClockRange':'',
#           'StarterBench':'',
#           'TeamID':'',
#           'VsConference':'',
#           'VsDivision':'',
#           'Weight':''}
