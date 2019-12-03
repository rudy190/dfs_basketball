import sqlite3
from nba_data.processing.db_config import db_path

def add_date_windows(game_ids):
    conn = sqlite3.connect(db_path)

    c = conn.cursor()

    stmnt = ("WITH RECURSIVE dates(date) AS (SELECT max(game_date_est) from games "\
                                             "UNION ALL "\
                                             "SELECT date(date, '-1 day') "\
                                             "FROM dates "\
                                             "WHERE date > '2015-01-01') "\
             "INSERT INTO date_windows "\
             "SELECT NULL as id, "\
                    "t1.game_date_est AS game_date, "\
                    "t2.date AS window_date, "\
                    "cast((julianday(t1.game_date_est) - "\
                          "julianday(t2.date)) AS INTEGER) AS days_lag "\
             "FROM (SELECT DISTINCT game_date_est FROM games where game_id = ?) t1 "\
             "JOIN dates t2 "\
             "ON datetime(t2.date) >= datetime(t1.game_date_est, '-30 days') "\
                "AND datetime(t2.date) < datetime(t1.game_date_est) "\
             "ORDER BY t1.game_date_est, "\
                      "t2.date;")
    for game_id in game_ids:
        try:
            c.execute(stmnt, (game_id,))
            conn.commit()
        except:
            pass
    conn.close()

    return True
