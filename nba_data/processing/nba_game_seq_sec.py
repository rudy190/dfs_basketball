from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from ..utilities.collection_classes import FantasyPts
from .db_config import Base

class GameSequenceSec(Base):
    __tablename__ = 'game_sequence_seconds'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    period = Column(INTEGER, nullable=True)
    model_event_num = Column(INTEGER, nullable=True)
    sec_elapsed = Column(INTEGER, nullable=True)
    clipped_sec_elapsed = Column(INTEGER, nullable=True)

    __table_args__ = (ForeignKeyConstraint([sport, season, game_id],
                                           ["games.sport",
                                            "games.season",
                                            "games.game_id"]),
                      UniqueConstraint(sport, season, game_id, model_event_num),
                      Index('ix_game_seq_sec_model_nums', game_id, model_event_num),
                      {})
