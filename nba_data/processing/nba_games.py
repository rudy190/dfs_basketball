from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.dialects.sqlite import (BOOLEAN, DATE, DATETIME, INTEGER, VARCHAR)
from .db_config import Base

class Game(Base):
    __tablename__ = 'games'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    game_date_est = Column(DATE, nullable=False)
    arena_name = Column(VARCHAR, nullable=True)
    wh_status = Column(BOOLEAN, nullable=True, default=False)
    pt_available = Column(BOOLEAN, nullable=True, default=False)

    teams = relationship("GameTeam",
                         collection_class=attribute_mapped_collection('home_away'),
                         back_populates="game",
                         cascade= "all, delete, delete-orphan")
    officials = relationship("GameOfficial",
                             collection_class=attribute_mapped_collection('official_id'),
                             back_populates="game",
                             cascade= "all, delete, delete-orphan")
    events = relationship("GameEvent",
                          collection_class=attribute_mapped_collection('event_num'),
                          back_populates="game",
                          cascade= "all, delete, delete-orphan")
    win_prob_events = relationship("GameWinProbEvent",
                                   collection_class=attribute_mapped_collection('sec_remain'),
                                   back_populates="game",
                                   cascade= "all, delete, delete-orphan")

    __table_args__ = (UniqueConstraint(sport, season, game_id,
                                       name='uix_games'),
                      Index('ix_game_date', game_id, game_date_est),
                      Index('ix_games_container', sport, season, game_id),
                      {})
