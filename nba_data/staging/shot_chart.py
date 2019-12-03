from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.sqlite import (DATE, DATETIME, JSON, VARCHAR, INTEGER,
                                        BOOLEAN)
from .db_config import Base

class StageShotChart(Base):
    __tablename__ = 'shot_chart_records'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    league_id = Column(VARCHAR(2), nullable=False)
    season = Column(INTEGER, nullable=False)
    season_type = Column(VARCHAR(15), nullable=False)
    start_date = Column(DATE, nullable=False)
    end_date = Column(DATE, nullable=False)
    team_id = Column(INTEGER, nullable=False)
    player_id = Column(INTEGER, nullable=False)
    context = Column(VARCHAR(5), nullable=False)
    status_code = Column(INTEGER, nullable=False)
    load_date = Column(DATETIME, nullable=False)
    status_reason = Column(VARCHAR(12), nullable=True)
    url = Column(VARCHAR(70), nullable=False)
    json = Column(JSON, nullable=True)
    processed = Column(BOOLEAN, nullable=True)
    processed_date = Column(DATETIME, nullable=True)

    __table_args__ = (UniqueConstraint(sport, league_id, season, season_type,
                                       start_date, end_date, team_id, player_id,
                                       context, url, status_code, load_date,
                                       name='uix_shot_chart_records'),
                      {})
