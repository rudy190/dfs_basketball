from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (INTEGER, VARCHAR)
from ..utilities.collection_classes import FantasyPts
from .db_config import Base

class TeamBoxScore(Base):
    __tablename__ = 'team_boxscores'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    team_id = Column(INTEGER, nullable=False)
    min = Column(VARCHAR, nullable=True, default=0)
    sec = Column(INTEGER, nullable=True, default=0)
    fgm = Column(INTEGER, nullable=True, default=0)
    fga = Column(INTEGER, nullable=True, default=0)
    fg2m = Column(INTEGER, nullable=True, default=0)
    fg2a = Column(INTEGER, nullable=True, default=0)
    fg3m = Column(INTEGER, nullable=True, default=0)
    fg3a = Column(INTEGER, nullable=True, default=0)
    ftm = Column(INTEGER, nullable=True, default=0)
    fta = Column(INTEGER, nullable=True, default=0)
    oreb = Column(INTEGER, nullable=True, default=0)
    dreb = Column(INTEGER, nullable=True, default=0)
    reb = Column(INTEGER, nullable=True, default=0)
    ast = Column(INTEGER, nullable=True, default=0)
    stl = Column(INTEGER, nullable=True, default=0)
    blk = Column(INTEGER, nullable=True, default=0)
    tov = Column(INTEGER, nullable=True, default=0)
    pf = Column(INTEGER, nullable=True, default=0)
    pts = Column(INTEGER, nullable=True, default=0)
    plus_minus = Column(FantasyPts, nullable=True, default=0)

    team = relationship("GameTeam",
                        foreign_keys = [game_id, team_id],
                        back_populates = "stats")
    __table_args__ = (ForeignKeyConstraint([game_id, team_id],
                                           ["game_teams.game_id",
                                            "game_teams.team_id"]),
                      UniqueConstraint(game_id, team_id, name='uix_team_box'),
                      Index('ix_game_team_box', game_id, team_id),
                      Index('ix_team_boxes_container', sport, season, game_id,
                            team_id),
                      {})
