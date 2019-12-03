from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from .db_config import Base

class GameOfficial(Base):
    __tablename__ = 'game_officials'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    official_id = Column(INTEGER, nullable=False)
    first_name = Column(INTEGER, nullable=False)
    last_name = Column(INTEGER, nullable=False)
    official_name = Column(INTEGER, nullable=False)
    jersey_num = Column(VARCHAR, nullable=False)

    game = relationship("Game",
                        foreign_keys = [sport, season, game_id],
                        back_populates = "officials")

    __table_args__ = (ForeignKeyConstraint([sport, season, game_id],
                                           ["games.sport",
                                            "games.season",
                                            "games.game_id"]),
                      UniqueConstraint(game_id, official_id,
                                       name='uix_game_officials'),
                      Index('ix_game_official', game_id, official_id),
                      Index('ix_game_officials_container', sport, season, game_id,
                            official_id),
                      {})
