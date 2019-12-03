from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from .db_config import Base

class GameStarter(Base):
    __tablename__ = 'game_starters'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    team_id = Column(INTEGER, nullable=False)
    player_id = Column(INTEGER, nullable=False)
    period = Column(INTEGER, nullable=True)
    min = Column(VARCHAR, nullable=True)
    min = Column(INTEGER, nullable=True)
    start_position = Column(VARCHAR, nullable=True)

    team = relationship("GameTeam",
                        foreign_keys = [sport, season, game_id, team_id],
                        back_populates = "period_starters")
    __table_args__ = (ForeignKeyConstraint([sport, season, game_id, team_id],
                                           ["game_teams.sport",
                                            "game_teams.season",
                                            "game_teams.game_id",
                                            "game_teams.team_id"]),
                      UniqueConstraint(game_id, team_id, player_id, period,
                                       name='uix_game_starters'),
                      Index('ix_game_starters', game_id, player_id, period,
                            start_position),
                      Index('ix_game_starters_container', sport, season, game_id,
                            team_id, player_id, period),
                      {})
