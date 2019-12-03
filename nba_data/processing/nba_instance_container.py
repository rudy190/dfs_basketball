import pandas as pd
from nba_data.utilities.sqlalchemy_utilities import bulk_insert_records
from .db_config import (Engine, Session)
from .processing_config import basketball_resultSets as resultSets
from .processing_config import basketball_bundles as bundles
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
from .nba_instance import NBADataInstance

class NBAInstanceContainer():
    def __init__(self, tableClass, sport, season):
        self.tableClass=tableClass
        self.table_name=tableClass.__table__.name
        self.set_resultSets()
        self.instances=[]
        self.set_constraints(sport, season)

    def set_resultSets(self):
        if self.table_name in resultSets:
            self.resultSets=resultSets[self.table_name]
        else:
            self.resultSets=None

    def set_constraints(self, sport, season):
        session=Session()
        if self.table_name!='players':
            query_records=(session.query(bundles[self.table_name])
                                  .filter(self.tableClass.sport==sport)
                                  .filter(self.tableClass.season==season)
                                  .all())
        else:
            query_records=(session.query(bundles[self.table_name])
                                  .all())
        self.constraints=set(record[0] for record in query_records)
        session.close()

    def update_constraints(self, instance_contraints):
        self.constraints|={instance_contraints}

    def get_instance_contraints(self, instance):
        instance_contraints=tuple(instance[c.name] for c in bundles[self.table_name].c)
        return instance_contraints

    def add(self, data, **kwargs):
        row_data=self.transform_data(data)
        for i, row in enumerate(row_data):
            event_id = i + 1
            nba_instance=NBADataInstance(self.tableClass, row, event_id=event_id, **kwargs)
            if self.validate_instance(nba_instance.instance):
                self.instances.append(nba_instance.instance)
            # else:
            #     print('Error duplicate record for: {}\n'.format(self.table_name))
            #     print(nba_instance.instance)

    def insert(self):
        if self.instances:
            bulk_insert_records(Engine, self.instances, self.tableClass, batchsize=500000)
            self.flush()

    def validate_instance(self, instance):
        instance_contraints=self.get_instance_contraints(instance)
        if instance_contraints not in self.constraints:
            self.update_constraints(instance_contraints)
            return True
        else:
            return False

    def flush(self):
        self.instances=[]

    def transform_data(self, data):
        if self.table_name == 'game_players':
            box_score_data, game_summary_data=data[0], data[1]
            row_data=self.get_nba_data_game_players(box_score_data, game_summary_data)
        elif self.table_name == 'games':
            row_data=self.get_nba_data_games(data)
        elif self.table_name == 'game_teams':
            row_data=self.get_nba_data_game_teams(data)
        elif self.table_name == 'game_event_players':
            row_data=self.get_nba_data_event_players(data)
        elif self.table_name == 'game_officials':
            row_data=self.get_nba_data_game_officials(data)
        else:
            row_data=self.get_nba_data_single_result_set(data)
        return row_data

    def get_nba_data_game_players(self, box_score_data, game_summary_data):
        row_data = {}
        for result_set in box_score_data['resultSets']:
            if result_set['name'] == 'PlayerStats':
                keys = [h.lower() for h in result_set['headers']]
                for row_set in result_set['rowSet']:
                    row=dict(zip(keys, row_set))
                    row.update({'inactive': False})
                    row_data.update({row['player_id']: row})
        for result_set in game_summary_data['resultSets']:
            if result_set['name'] == 'InactivePlayers':
                keys = [h.lower() for h in result_set['headers']]
                for row_set in result_set['rowSet']:
                    row=dict(zip(keys, row_set))
                    if 'player_id' in row:
                        if row['player_id'] in row_data:
                            row_data[row['player_id']].update({'inactive': True})
                        else:
                            player_name='{} {}'.format(row['first_name'], row['last_name'])
                            row.update({'inactive': True})
                            row.update({'player_name': player_name})
                            row_data.update({row['player_id']: row})
        return list(row_data.values())

    def get_nba_data_games(self, schedule_data):
        row_data = {}
        for result_set in schedule_data['resultSets']:
            if result_set['name'] == 'GameHeader':
                keys = [h.lower() for h in result_set['headers']]
                for row_set in result_set['rowSet']:
                    row=dict(zip(keys, row_set))
                    if row['game_id'] not in row_data:
                        row_data.update({row['game_id']: row})
        for result_set in schedule_data['resultSets']:
            if result_set['name'] == 'Available':
                keys = [h.lower() for h in result_set['headers']]
                for row_set in result_set['rowSet']:
                    row=dict(zip(keys, row_set))
                    if 'game_id' in row:
                        if row['game_id'] in row_data:
                            row_data[row['game_id']].update({'pt_available': row['pt_available']})
        return list(row_data.values())

    def get_nba_data_game_teams(self, nba_data):
        row_data = {}
        for result_set_name in self.resultSets:
            for result_set in nba_data['resultSets']:
                if result_set['name'] == result_set_name:
                    keys = [h.lower() for h in result_set['headers']]
                    for row_set in result_set['rowSet']:
                        row=dict(zip(keys, row_set))
                        if 'team_id' in row:
                            if row['team_id'] not in row_data:
                                row_data.update({row['team_id']: row})
                            else:
                                row_data[row['team_id']] = {**row_data[row['team_id']],
                                                            **row}
        return list(row_data.values())

    def get_nba_data_event_players(self, nba_event_data):
        event_data=self.get_nba_data_single_result_set(nba_event_data)
        row_data=[]
        for event in event_data:
            event_player_set=set()
            if event['eventmsgtype'] in [9, 12, 13, 18]:
                player_num_range = range(1,2)
            elif event['eventmsgtype'] in [5,8]:
                player_num_range = range(1,3)
            else:
                player_num_range = range(1,4)
            for player_num in player_num_range:
                row={'game_id': event['game_id'],
                     'eventnum': event['eventnum'],
                     'player_num': player_num,
                     'persontype': None,
                     'player_id': None,
                     'player_name': None,
                     'team_id': None,
                     'team_name': None,
                     'team_nickname': None,
                     'team_abbreviation': None}
                for key, value in event.items():
                    if str(player_num) in key:
                        new_key=key.replace(str(player_num), '')
                        row[new_key]=value
                    elif key in ['homedescription', 'neutraldescription',
                                 'visitordescription']:
                        row.update({key: value})
                if event['eventmsgtype'] in [8, 9, 12, 13, 18]:
                    if row['player_id'] is not None:
                        if row['player_id'] != 0:
                            if row['player_id'] not in event_player_set:
                                event_player_set |= {row['player_id']}
                                row_data.append(row)
                else:
                    if row['player_id'] is not None:
                        if row['player_id'] != 0:
                            if row['player_id'] not in event_player_set:
                                event_player_set |= {row['player_id']}
                                row_data.append(row)
        return row_data

    def get_nba_data_game_officials(self, nba_event_data):
        row_data = self.get_nba_data_single_result_set(nba_event_data)
        for row in row_data:
            if (('first_name' in row)
                and ('last_name' in row)):
                if ((row['first_name'] is not None)
                    and (row['last_name'] is not None)):
                    official_name = '{}.{}'.format(row['first_name'][:1].upper(),
                                                   row['first_name'].title())
                    row.update({'official_name': official_name})
        return row_data

    def get_nba_data_single_result_set(self, nba_data):
        row_data=[]
        for result_set in nba_data['resultSets']:
            if result_set['name']==self.resultSets:
                keys=[h.lower() for h in result_set['headers']]
                for row_set in result_set['rowSet']:
                    row=dict(zip(keys, row_set))
                    row_data.append(row)
        return row_data
