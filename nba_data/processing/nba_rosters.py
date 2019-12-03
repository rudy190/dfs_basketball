from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (INTEGER, VARCHAR, DATETIME)
from ..utilities.collection_classes import FantasyPts
from .db_config import Base

class TeamRoster(Base):
    __tablename__ = 'team_rosters'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    team_id = Column(INTEGER, nullable=False)
    player_id = Column(INTEGER, nullable=False)
    player_name = Column(VARCHAR, nullable=False)
    position = Column(VARCHAR, nullable=True)
    height = Column(VARCHAR, nullable=True)
    weight = Column(VARCHAR, nullable=True)
    birth_date = Column(DATETIME, nullable=True)
    age = Column(INTEGER, nullable=True)
    yrs_exp = Column(INTEGER, nullable=True)

    __table_args__ = (UniqueConstraint(sport, season, team_id, player_id,
                                       name='uix_team_roster'),
                      Index('ix_team_roster', player_id),
                      {})
