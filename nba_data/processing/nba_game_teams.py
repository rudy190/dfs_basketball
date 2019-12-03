from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from .db_config import Base

class GameTeam(Base):
    __tablename__ = 'game_teams'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    team_id = Column(INTEGER, nullable=False)
    team_nickname = Column(VARCHAR, nullable=True)
    team_abbrev = Column(VARCHAR, nullable=True)
    home_away = Column(BOOLEAN, nullable=False)

    game = relationship("Game",
                        foreign_keys = [sport, season, game_id],
                        back_populates = "teams")
    players = relationship("GamePlayer",
                           collection_class=attribute_mapped_collection('player_id'),
                           back_populates="team",
                           cascade= "all, delete, delete-orphan")
    period_starters = relationship("GameStarter",
                                   back_populates="team",
                                   cascade= "all, delete, delete-orphan")
    stats = relationship("TeamBoxScore",
                         uselist=False,
                         back_populates = "team")
    __table_args__ = (ForeignKeyConstraint([sport, season, game_id],
                                           ["games.sport",
                                            "games.season",
                                            "games.game_id"]),
                      UniqueConstraint(game_id, team_id, home_away,
                                       name='uix_game_teams'),
                      Index('ix_game_teams', game_id, team_id, home_away),
                      Index('ix_game_teams_container', sport, season, game_id,
                            team_id, home_away),
                      {})
