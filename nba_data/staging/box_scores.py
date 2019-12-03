from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.sqlite import (DATETIME, JSON, VARCHAR, INTEGER, BOOLEAN)
from .db_config import Base

class StageBoxScore(Base):
    __tablename__ = 'box_score_records'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    league_id = Column(VARCHAR(2), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    status_code = Column(INTEGER, nullable=True)
    load_date = Column(DATETIME, nullable=False)
    status_reason = Column(VARCHAR(12), nullable=True)
    url = Column(VARCHAR(70), nullable=False)
    json = Column(JSON, nullable=True)
    processed = Column(BOOLEAN, nullable=True)
    processed_date = Column(DATETIME, nullable=True)

    __table_args__ = (UniqueConstraint(sport, league_id, season, game_id,
                                       url, status_code, load_date,
                                       name='uix_box_score_records'),
                      {})
