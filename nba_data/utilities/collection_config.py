nba_league_id_dict = {'nba':'00', 'wnba':'10', 'g_lg':'20'}

period_min = {'nba':12,
              'wnba':10,
              'g_lg':12}

ot_min = {'nba':5,
          'wnba':5,
          'g_lg':5}

site_dict = {'fd':"fd",
             'fanduel':"fd",
             'FanDuel':"fd",
             'dk':"dk",
             'draftkings':"dk",
             'DraftKings':"dk"}

nba_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:70.0) Gecko/20100101 Firefox/70.0',
               'Referer': 'https://stats.nba.com'}

basketball_stats_urls = {
     'box_score': {'nba':'https://stats.nba.com/stats/boxscoretraditionalv2',
                   'wnba':'https://stats.nba.com/stats/boxscoretraditionalv2',
                   'g_lg':'https://stats.nba.com/stats/boxscoretraditionalv2'},
     'game_summary': {'nba':'https://stats.nba.com/stats/boxscoresummaryv2',
                      'wnba':'https://stats.nba.com/stats/boxscoresummaryv2',
                      'g_lg':'https://stats.nba.com/stats/boxscoresummaryv2'},
     'period_starters': {'nba':'https://stats.nba.com/stats/boxscoretraditionalv2',
                         'wnba':'https://stats.nba.com/stats/boxscoretraditionalv2',
                         'g_lg':'https://stats.nba.com/stats/boxscoretraditionalv2'},
     'pbp': {'nba':'https://stats.nba.com/stats/playbyplayv2',
             'wnba':'https://stats.nba.com/stats/playbyplayv2',
             'g_lg':'https://stats.nba.com/stats/playbyplayv2'},
     'schedule': {'nba':'https://stats.nba.com/stats/scoreboardv2',
                  'wnba':'https://stats.nba.com/stats/scoreboardv2',
                  'g_lg':'https://stats.nba.com/stats/scoreboardv2'},
     'season': {'nba':'https://stats.nba.com/stats/leaguegamelog',
                'wnba':'https://stats.nba.com/stats/leaguegamelog',
                'g_lg':'https://stats.nba.com/stats/leaguegamelog'},
     'shot_chart': {'nba':'https://stats.nba.com/stats/shotchartdetail',
                    'wnba':'https://stats.nba.com/stats/shotchartdetail',
                    'g_lg':'https://stats.nba.com/stats/shotchartdetail'},
     'win_prob': {'nba':'https://stats.nba.com/stats/winprobabilitypbp',
                  'wnba':'https://stats.nba.com/stats/winprobabilitypbp',
                  'g_lg':'https://stats.nba.com/stats/winprobabilitypbp'},
     'roster': {'nba':'https://stats.nba.com/stats/commonteamroster',
                'wnba':'https://stats.nba.com/stats/commonteamroster',
                'g_lg':'https://stats.nba.com/stats/commonteamroster'},
     'player': {'nba':'https://stats.nba.com/stats/commonplayerinfo',
                'wnba':'https://stats.nba.com/stats/commonplayerinfo',
                'g_lg':'https://stats.nba.com/stats/commonplayerinfo'}}
