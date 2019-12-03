from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.sqlite import (DATE, DATETIME, JSON, VARCHAR, INTEGER,
                                        BOOLEAN)
from .db_config import Base

class StageSchedule(Base):
    __tablename__ = 'schedule_dates'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    league_id = Column(VARCHAR(2), nullable=False)
    season = Column(INTEGER, nullable=False)
    date = Column(DATE, nullable=False)
    status_code = Column(INTEGER, nullable=False)
    load_date = Column(DATETIME, nullable=False)
    url = Column(VARCHAR(85), nullable=False)
    status_reason = Column(VARCHAR(12), nullable=True)
    json = Column(JSON, nullable=True)
    processed = Column(BOOLEAN, nullable=True)
    processed_date = Column(DATETIME, nullable=True)

    __table_args__ = (UniqueConstraint(sport, league_id, season, date,
                                       url, status_code, load_date,
                                       name='uix_schedule_dates'),
                      {})
