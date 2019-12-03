import pandas as pd
from .db_config import Session
from nba_data.processing.nba_game_starters import GameStarter

def remove_error_period_starters(game_ids):
    session = Session()
    period_starters_query = session.query(GameStarter).filter(GameStarter.game_id.in_(game_ids))
    period_starters = pd.read_sql_query(period_starters_query.statement, session.bind)
    starters_error_ids = []
    for group, df in period_starters.groupby(['sport','season','game_id','period',
                                              'team_id']):
        starters_error_ids.append(df.sort_values(by=['min'], ascending=False)[5:])
    if starters_error_ids:
        starters_error_ids = list(pd.concat(starters_error_ids, axis=0)['id'].values)
    else:
        starters_error_ids = []
    for error_id in starters_error_ids:
        delete_records = session.query(GameStarter).filter(GameStarter.id==str(error_id))
        delete_records.delete(synchronize_session=False)
    session.commit()
    session.close()
    return True
