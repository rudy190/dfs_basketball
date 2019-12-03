from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from .db_config import Base

class GameShot(Base):
    __tablename__ = 'game_shots'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    event_num = Column(INTEGER, nullable=False)
    team_id = Column(INTEGER, nullable=False)
    player_id = Column(INTEGER, nullable=False)
    player_name = Column(VARCHAR, nullable=True)
    event_type = Column(VARCHAR, nullable=True)
    action_type = Column(VARCHAR, nullable=True)
    shot_type = Column(VARCHAR, nullable=True)
    shot_zone_basic = Column(VARCHAR, nullable=True)
    shot_zone_area = Column(VARCHAR, nullable=True)
    shot_zone_range = Column(VARCHAR, nullable=True)
    shot_distance = Column(INTEGER, nullable=True)
    x = Column(INTEGER, nullable=True)
    y = Column(INTEGER, nullable=True)
    shot_attempted_flag = Column(BOOLEAN, nullable=True)
    shot_made_flag = Column(BOOLEAN, nullable=True)

    event_player = relationship("GameEventPlayer",
                                foreign_keys = [game_id, event_num, player_id],
                                back_populates = "shot_chart")

    __table_args__ = (ForeignKeyConstraint([sport, season, game_id],
                                           ["games.sport",
                                            "games.season",
                                            "games.game_id"]),
                      ForeignKeyConstraint([game_id, team_id, player_id],
                                           ["game_players.game_id",
                                            "game_players.team_id",
                                            "game_players.player_id"]),
                      ForeignKeyConstraint([game_id, event_num],
                                           ["game_events.game_id",
                                            "game_events.event_num"]),
                      ForeignKeyConstraint([game_id, event_num, player_id],
                                           ["game_event_players.game_id",
                                            "game_event_players.event_num",
                                            "game_event_players.player_id"]),
                      UniqueConstraint(game_id, event_num, player_id,
                                       name='uix_game_shots'),
                      Index('ix_game_shots', game_id, event_num, player_id,
                            event_type, action_type, shot_type, shot_attempted_flag,
                            shot_made_flag),
                      Index('ix_game_shots_container', sport, season, game_id,
                            event_num, player_id),
                      {})
