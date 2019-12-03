from sqlalchemy.orm import Bundle
from .nba_game_event_players import GameEventPlayer
from .nba_game_events import GameEvent
from .nba_game_officials import GameOfficial
from .nba_game_players import GamePlayer
from .nba_game_shots import GameShot
from .nba_game_starters import GameStarter
from .nba_game_teams import GameTeam
from .nba_game_win_prob import GameWinProbEvent
from .nba_games import Game
from .nba_player_boxes import PlayerBoxScore
from .nba_team_boxes import TeamBoxScore
from .nba_rosters import TeamRoster
from .nba_players import Player

basketball_resultSets={'games': ['GameHeader', 'Available'],
                       'game_shots': 'Shot_Chart_Detail',
                       'game_players': ['PlayerStats', 'InactivePlayers'],
                       'game_officials': 'Officials',
                       'game_teams': ['LineScore', 'OtherStats'],
                       'player_boxscores': 'PlayerStats',
                       'team_boxscores': 'TeamStats',
                       'team_rosters': 'CommonTeamRoster',
                       'game_starters': 'PlayerStats',
                       'game_events': 'PlayByPlay',
                       'game_event_players': 'PlayByPlay',
                       'game_win_prob_events': 'WinProbPBP',
                       'players': 'CommonPlayerInfo'}

basketball_bundles={'games': Bundle('game',
                                    Game.sport,
                                    Game.season,
                                    Game.game_id),
                    'game_teams': Bundle('team',
                                         GameTeam.game_id,
                                         GameTeam.team_id,
                                         GameTeam.home_away),
                    'game_officials': Bundle('official',
                                             GameOfficial.game_id,
                                             GameOfficial.official_id),
                    'game_events': Bundle('events',
                                          GameEvent.game_id,
                                          GameEvent.event_num),
                    'game_event_players': Bundle('event_players',
                                                 GameEventPlayer.game_id,
                                                 GameEventPlayer.event_num,
                                                 GameEventPlayer.player_num),
                    'game_win_prob_events': Bundle('win_prob_events',
                                                   GameWinProbEvent.game_id,
                                                   GameWinProbEvent.event_num,
                                                   GameWinProbEvent.period,
                                                   GameWinProbEvent.sec_remain),
                    'game_players': Bundle('players',
                                           GamePlayer.game_id,
                                           GamePlayer.team_id,
                                           GamePlayer.player_id),
                    'game_starters': Bundle('starters',
                                            GameStarter.game_id,
                                            GameStarter.team_id,
                                            GameStarter.player_id,
                                            GameStarter.period),
                    'game_shots': Bundle('shots',
                                         GameShot.game_id,
                                         GameShot.event_num,
                                         GameShot.player_id),
                    'player_boxscores': Bundle('player_boxes',
                                               PlayerBoxScore.game_id,
                                               PlayerBoxScore.team_id,
                                               PlayerBoxScore.player_id),
                    'team_boxscores': Bundle('team_boxes',
                                             TeamBoxScore.game_id,
                                             TeamBoxScore.team_id),
                    'team_rosters': Bundle('team_rosters',
                                           TeamRoster.season,
                                           TeamRoster.team_id,
                                           TeamRoster.player_id),
                    'players': Bundle('players',
                                      Player.player_id)}

basketball_rename_fields={'game_events': {'eventnum':'event_num'},
                          'game_event_players': {'persontype': 'player_type',
                                                 'player_team_id': 'team_id',
                                                 'player_team_nickname': 'team_nickname',
                                                 'player_team_abbreviation': 'team_abbrev',
                                                 'eventnum': 'event_num',
                                                 'homedescription': 'home_description',
                                                 'neutraldescription': 'neutral_description',
                                                 'visitordescription': 'away_description'},
                          'game_shots': {'game_event_id': 'event_num',
                                         'loc_x':'x',
                                         'loc_y':'y'},
                          'game_teams': {'team_abbreviation': 'team_abbrev'},
                          'game_win_prob_events': {'seconds_remaining': 'sec_remain',
                                                   'visitor_pts': 'away_pts',
                                                   'visitor_pct': 'away_pct'},
                          'player_boxscores': {'to':'tov',
                                               'start_position': 'start_pos'},
                          'team_boxscores': {'to':'tov'},
                          'team_rosters': {'player':'player_name',
                                           'exp':'yrs_exp',
                                           'teamid':'team_id'},
                          'players': {'person_id':'player_id',
                                      'teamid':'team_id'}}

basketball_date_fields={'games': ['game_date_est'],
                        'team_rosters': ['birth_date'],
                        'players': ['birthdate']}

basketball_integer_fields={'players': ['weight','draft_year','draft_round',
                                       'draft_number']}
