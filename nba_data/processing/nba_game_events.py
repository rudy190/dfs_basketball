from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from ..utilities.collection_classes import FantasyPts
from .db_config import Base

class GameEvent(Base):
    __tablename__ = 'game_events'

    id = Column(INTEGER, primary_key=True, nullable=False)
    event_id = Column(INTEGER, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    event_num = Column(INTEGER, nullable=False)
    wctimestring = Column(VARCHAR, nullable=True)
    eventmsgtype = Column(INTEGER, nullable=True)
    eventmsgactiontype = Column(INTEGER, nullable=True)
    period = Column(INTEGER, nullable=True)
    pctimestring = Column(VARCHAR, nullable=True)

    game = relationship("Game",
                        foreign_keys = [sport, season, game_id],
                        back_populates = "events")
    event_players = relationship("GameEventPlayer",
                                 collection_class=attribute_mapped_collection('player_num'),
                                 back_populates="event",
                                 cascade= "all, delete, delete-orphan")

    __table_args__ = (ForeignKeyConstraint([sport, season, game_id],
                                           ["games.sport",
                                            "games.season",
                                            "games.game_id"]),
                      UniqueConstraint(game_id, event_num,
                                       name='uix_game_events'),
                      Index('ix_game_event_ids', event_id),
                      Index('ix_game_events', game_id, event_num, eventmsgtype,
                            eventmsgactiontype),
                      Index('ix_game_events_container', sport, season, game_id,
                            event_num),
                      {})
