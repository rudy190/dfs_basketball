from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from .db_config import Base
from ..utilities.collection_classes import (FantasyPts, FantasyStats)

class GameWinProbEvent(Base):
    __tablename__ = 'game_win_prob_events'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    event_num = Column(INTEGER, nullable=True)
    period = Column(INTEGER, nullable=True)
    pctimestring = Column(VARCHAR, nullable=True)
    sec_remain = Column(FantasyPts, nullable=True)
    description = Column(VARCHAR(10), nullable=True)
    location = Column(VARCHAR, nullable=True)
    home_pts = Column(INTEGER, nullable=True)
    home_pct = Column(FantasyStats, nullable=True)
    away_pts = Column(INTEGER, nullable=True)
    away_pct = Column(FantasyStats, nullable=True)
    home_poss_ind = Column(INTEGER, nullable=True)
    home_g = Column(FantasyPts, nullable=True)

    game = relationship("Game",
                        foreign_keys = [sport, season, game_id],
                        back_populates = "win_prob_events")

    __table_args__ = (ForeignKeyConstraint([sport, season, game_id],
                                           ["games.sport",
                                            "games.season",
                                            "games.game_id"]),
                      UniqueConstraint(game_id, event_num, period, sec_remain,
                                       name='uix_win_prob_events'),
                      Index('ix_game_win_prob_events', game_id, event_num, period,
                            sec_remain, home_poss_ind, home_pts, away_pts),
                      Index('ix_game_win_prob_container', sport, season, game_id,
                            event_num, period, sec_remain),
                      {})
