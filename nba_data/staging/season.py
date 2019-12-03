from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.sqlite import (DATE, DATETIME, JSON, VARCHAR, INTEGER, BOOLEAN)
from .db_config import Base

class StageSeason(Base):
    __tablename__ = 'seasons'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    league_id = Column(VARCHAR(2), nullable=False)
    season = Column(INTEGER, nullable=False)
    date_from = Column(DATE, nullable=False)
    date_to = Column(DATE, nullable=False)
    season_type = Column(VARCHAR(15), nullable=False)
    status_code = Column(INTEGER, nullable=False)
    load_date = Column(DATETIME, nullable=False)
    status_reason = Column(VARCHAR(12), nullable=True)
    url = Column(VARCHAR(70), nullable=False)
    json = Column(JSON, nullable=True)
    processed = Column(BOOLEAN, nullable=True)
    processed_date = Column(DATETIME, nullable=True)

    __table_args__ = (UniqueConstraint(sport, league_id, season, season_type,
                                       url, status_code, load_date,
                                       name='uix_seasons'),
                      {})
