from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (INTEGER, VARCHAR, DATETIME)
from ..utilities.collection_classes import FantasyPts
from .db_config import Base

class Player(Base):
    __tablename__ = 'players'

    id = Column(INTEGER, primary_key=True, nullable=False)
    player_id = Column(INTEGER, nullable=False)
    first_name = Column(VARCHAR, nullable=False)
    last_name = Column(VARCHAR, nullable=False)
    display_first_last = Column(VARCHAR, nullable=False)
    display_last_comma_first = Column(VARCHAR, nullable=True)
    display_fi_last = Column(VARCHAR, nullable=True)
    birthdate = Column(DATETIME, nullable=True)
    school = Column(VARCHAR, nullable=True)
    country = Column(VARCHAR, nullable=True)
    last_affiliation = Column(VARCHAR, nullable=True)
    height = Column(VARCHAR, nullable=True)
    weight = Column(VARCHAR, nullable=True)
    season_exp = Column(INTEGER, nullable=True)
    jersey = Column(VARCHAR, nullable=True)
    position = Column(VARCHAR, nullable=True)
    playercode = Column(VARCHAR, nullable=True)
    from_year = Column(INTEGER, nullable=True)
    to_year = Column(INTEGER, nullable=True)
    draft_year = Column(INTEGER, nullable=True)
    draft_round = Column(INTEGER, nullable=True)
    draft_number = Column(INTEGER, nullable=True)

    __table_args__ = (UniqueConstraint(player_id,
                                       name='uix_player'),
                      Index('ix_players', player_id),
                      {})
