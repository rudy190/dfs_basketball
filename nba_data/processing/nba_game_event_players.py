from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from .db_config import Base

class GameEventPlayer(Base):
    __tablename__ = 'game_event_players'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    event_num = Column(INTEGER, nullable=False)
    player_num = Column(INTEGER, nullable=False)
    home_description = Column(VARCHAR, nullable=True)
    neutral_description = Column(VARCHAR, nullable=True)
    away_description = Column(VARCHAR, nullable=True)
    player_id = Column(INTEGER, nullable=True)
    player_type = Column(INTEGER, nullable=True)
    player_name = Column(VARCHAR, nullable=True)
    team_id = Column(INTEGER, nullable=True, default=0)
    team_nickname = Column(VARCHAR, nullable=True)
    team_abbrev = Column(VARCHAR, nullable=True)

    event = relationship("GameEvent",
                         foreign_keys = [sport, season, game_id, event_num],
                         back_populates = "event_players")
    shot_chart = relationship("GameShot",
                              uselist=False,
                              back_populates="event_player",
                              cascade= "all, delete, delete-orphan")

    __table_args__ = (ForeignKeyConstraint([sport, season, game_id, event_num],
                                           ["game_events.sport",
                                            "game_events.season",
                                            "game_events.game_id",
                                            "game_events.event_num"]),
                      UniqueConstraint(game_id, event_num, player_num,
                                       name='uix_game_event_players'),
                      Index('ix_game_event_players', game_id, event_num, player_id,
                            player_num, player_type, home_description,
                            neutral_description, home_description),
                      Index('ix_game_event_player_teams', game_id, event_num,
                            player_id, team_id),
                      Index('ix_game_event_players_container', sport, season,
                            game_id, event_num, player_num),
                      {})
