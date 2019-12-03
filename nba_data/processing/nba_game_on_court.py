from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.sqlite import (INTEGER, VARCHAR)
from .db_config import Base

class GameOnCourt(Base):
    __tablename__ = 'game_on_court'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    period = Column(INTEGER, nullable=True)
    event_num = Column(INTEGER, nullable=True)
    model_event_num = Column(INTEGER, nullable=True)
    team_id = Column(INTEGER, nullable=True)
    person_id = Column(INTEGER, nullable=True)
    on_court_ind = Column(INTEGER, nullable=True, default=0)

    __table_args__ = (ForeignKeyConstraint([sport, season, game_id, model_event_num],
                                           ["game_sequences.sport",
                                            "game_sequences.season",
                                            "game_sequences.game_id",
                                            "game_sequences.model_event_num"]),
                      UniqueConstraint(sport, season, game_id, model_event_num,
                                       team_id, person_id),
                      Index('ix_game_on_court_players', game_id, model_event_num,
                            person_id, on_court_ind),
                      {})
