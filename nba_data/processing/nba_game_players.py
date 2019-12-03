from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from .db_config import Base

class GamePlayer(Base):
    __tablename__ = 'game_players'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    team_id = Column(INTEGER, nullable=False)
    player_id = Column(INTEGER, nullable=False)
    player_name = Column(VARCHAR, nullable=True)
    inactive = Column(BOOLEAN, nullable=True)
    comment = Column(VARCHAR, nullable=True)

    team = relationship("GameTeam",
                        foreign_keys = [sport, season, game_id, team_id],
                        back_populates = "players")
    stats = relationship("PlayerBoxScore",
                         uselist=False,
                         back_populates = "player")
    __table_args__ = (ForeignKeyConstraint([sport, season, game_id, team_id],
                                           ["game_teams.sport",
                                            "game_teams.season",
                                            "game_teams.game_id",
                                            "game_teams.team_id"]),
                      UniqueConstraint(game_id, team_id, player_id,
                                       name='uix_game_players'),
                      Index('ix_game_players', game_id, player_id, team_id,
                            player_name, inactive, comment),
                      Index('ix_game_players_container', sport, season, game_id,
                            team_id, player_id),
                      {})
