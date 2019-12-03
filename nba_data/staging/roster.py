from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.sqlite import (DATETIME, JSON, VARCHAR, INTEGER, BOOLEAN)
from .db_config import Base

class StageRoster(Base):
    __tablename__ = 'rosters'

    id = Column(INTEGER, primary_key=True, nullable=False)
    team_id = Column(INTEGER, nullable=False)
    sport = Column(VARCHAR, nullable=False)
    season = Column(INTEGER, nullable=False)
    status_code = Column(INTEGER, nullable=False)
    load_date = Column(DATETIME, nullable=False)
    status_reason = Column(VARCHAR(12), nullable=True)
    url = Column(VARCHAR(70), nullable=False)
    json = Column(JSON, nullable=True)
    processed = Column(BOOLEAN, nullable=True)
    processed_date = Column(DATETIME, nullable=True)

    __table_args__ = (UniqueConstraint(team_id, sport, season, url, status_code,
                                       load_date, name='uix_rosters'),
                      {})
