from nba_data.processing.db_config import Base, Engine
from nba_data.processing.nba_game_event_players import GameEventPlayer
from nba_data.processing.nba_game_events import GameEvent
from nba_data.processing.nba_game_seq import GameSequence
from nba_data.processing.nba_game_seq_starts import GameSequenceStarters
from nba_data.processing.nba_game_seq_sec import GameSequenceSec
from nba_data.processing.nba_game_on_court import GameOnCourt
from nba_data.processing.nba_game_officials import GameOfficial
from nba_data.processing.nba_game_players import GamePlayer
from nba_data.processing.nba_game_shots import GameShot
from nba_data.processing.nba_game_starters import GameStarter
from nba_data.processing.nba_game_teams import GameTeam
from nba_data.processing.nba_game_win_prob import GameWinProbEvent
from nba_data.processing.nba_games import Game
from nba_data.processing.nba_player_boxes import PlayerBoxScore
from nba_data.processing.nba_team_boxes import TeamBoxScore
from nba_data.processing.nba_rosters import TeamRoster
from nba_data.processing.nba_players import Player
from nba_data.processing.nba_instance_container import NBAInstanceContainer
from nba_data.processing.nba_unprocessed import UnprocessedData
from nba_data.processing.process_date_windows import add_date_windows
from nba_data.processing.process_nba_seq_records import process_game_sequences
from nba_data.processing.process_error_period_starters import remove_error_period_starters
import sys

SEASON=2019

def process_nba_staging_instances():
    global SEASON

    season = SEASON

    for sport in ['nba','wnba','g_lg']:

        print('Processing {} - season {}'.format(sport, season))

        unprocessed_data=UnprocessedData(sport, season)

        if unprocessed_data.unprocessed_date_count > 0:

            games=NBAInstanceContainer(Game, sport, season)
            game_teams=NBAInstanceContainer(GameTeam, sport, season)
            game_officials=NBAInstanceContainer(GameOfficial, sport, season)
            player_boxes=NBAInstanceContainer(PlayerBoxScore, sport, season)
            team_boxes=NBAInstanceContainer(TeamBoxScore, sport, season)
            game_events=NBAInstanceContainer(GameEvent, sport, season)
            game_event_players=NBAInstanceContainer(GameEventPlayer, sport, season)
            game_starters=NBAInstanceContainer(GameStarter, sport, season)
            win_prob_events=NBAInstanceContainer(GameWinProbEvent, sport, season)
            game_shots=NBAInstanceContainer(GameShot, sport, season)
            game_players=NBAInstanceContainer(GamePlayer, sport, season)
            team_rosters=NBAInstanceContainer(TeamRoster, sport, season)
            players=NBAInstanceContainer(Player, sport, season)

            for schedule_date in unprocessed_data.dates:
                games.add(schedule_date.json,
                          sport=sport,
                          season=season)

            for box_data, game_summary in unprocessed_data.game_players:
                game_players.add((box_data.json, game_summary.json),
                                 game_id=game_summary.game_id,
                                 sport=sport,
                                 season=season)

            for game_summary in unprocessed_data.game_summaries:
                home_team_id = game_summary.json['resultSets'][0]['rowSet'][0][6]
                game_teams.add(game_summary.json,
                               game_id=game_summary.game_id,
                               home_team_id=home_team_id,
                               sport=sport,
                               season=season)
                game_officials.add(game_summary.json,
                                   game_id=game_summary.game_id,
                                   sport=sport,
                                   season=season)

            for box_score in unprocessed_data.box_scores:
                player_boxes.add(box_score.json,
                                 game_id=box_score.game_id,
                                 sport=sport,
                                 season=season)
                team_boxes.add(box_score.json,
                               game_id=box_score.game_id,
                               sport=sport,
                               season=season)

            for event in unprocessed_data.events:
                game_events.add(event.json,
                                game_id=event.game_id,
                                sport=sport,
                                season=season)
                game_event_players.add(event.json,
                                       game_id=event.game_id,
                                       sport=sport,
                                       season=season)

            for starter in unprocessed_data.starters:
                game_starters.add(starter.json,
                                  game_id=starter.game_id,
                                  period=starter.json['parameters']['StartPeriod'],
                                  sport=sport,
                                  season=season)

            for win_prob_event in unprocessed_data.win_prob_events:
                win_prob_events.add(win_prob_event.json,
                                    game_id=win_prob_event.game_id,
                                    sport=sport,
                                    season=season)

            for shot_chart in unprocessed_data.shot_charts:
                game_shots.add(shot_chart.json,
                               sport=sport,
                               season=season)

            for team_roster in unprocessed_data.team_rosters:
                team_rosters.add(team_roster.json,
                                 sport=sport,
                                 season=season)

            for player in unprocessed_data.players:
                players.add(player.json)

            print('\t- processed: {} games'.format(len(games.instances)))

            insert_instances(games, game_teams, game_officials, player_boxes,
                             team_boxes, game_events, game_event_players,
                             game_starters, win_prob_events, game_shots,
                             game_players, team_rosters, players)

            unprocessed_data.commit()

            add_date_windows(unprocessed_data.game_ids)

            remove_error_period_starters(unprocessed_data.game_ids)

            if len(unprocessed_data.game_ids):
                process_game_sequences(unprocessed_data.game_ids)

        else:
            print('\t- processed: 0 games')

    return True

def insert_instances(*args):
    for container in args:
        container.insert()
    return True

def main():

    Base.metadata.create_all(bind=Engine, checkfirst=True)

    process_nba_staging_instances()

    return True


if __name__ == "__main__":
    main()
