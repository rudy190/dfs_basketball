from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.dialects.sqlite import (BOOLEAN, INTEGER, VARCHAR)
from ..utilities.collection_classes import FantasyPts
from .db_config import Base

class GameSequence(Base):
    __tablename__ = 'game_sequences'

    id = Column(INTEGER, primary_key=True, nullable=False)
    sport = Column(VARCHAR(5), nullable=False)
    season = Column(INTEGER, nullable=False)
    game_id = Column(VARCHAR(10), nullable=False)
    period = Column(INTEGER, nullable=True)
    sec_remain = Column(INTEGER, nullable=True)
    event_num = Column(INTEGER, nullable=True)
    model_event_num = Column(INTEGER, nullable=True)
    sub_event_num = Column(INTEGER, nullable=True)
    eventmsgtype = Column(INTEGER, nullable=True)
    home_poss = Column(INTEGER, nullable=True)
    away_poss = Column(INTEGER, nullable=True)
    home_pts = Column(INTEGER, nullable=True)
    away_pts = Column(INTEGER, nullable=True)
    neutral_description = Column(VARCHAR, nullable=True)
    home_description = Column(VARCHAR, nullable=True)
    away_description = Column(VARCHAR, nullable=True)
    shot_event = Column(VARCHAR, nullable=True)
    shot_type = Column(VARCHAR, nullable=True)
    shot_zone_basic = Column(VARCHAR, nullable=True)
    shot_zone_area = Column(VARCHAR, nullable=True)
    shot_zone_range = Column(VARCHAR, nullable=True)
    stat_category = Column(VARCHAR, nullable=True)
    action_category = Column(VARCHAR, nullable=True)
    action_sub_category = Column(VARCHAR, nullable=True)
    person_id = Column(INTEGER, nullable=True)
    person_name = Column(VARCHAR, nullable=True)
    team_id = Column(INTEGER, nullable=True)
    team_nickname = Column(VARCHAR, nullable=True)
    opp_team_id = Column(INTEGER, nullable=True)
    away_team_id = Column(INTEGER, nullable=True)
    home_team_id = Column(INTEGER, nullable=True)
    pers_foul = Column(INTEGER, nullable=True)
    team_foul = Column(INTEGER, nullable=True)
    official = Column(VARCHAR, nullable=True)

    __table_args__ = (ForeignKeyConstraint([sport, season, game_id],
                                           ["games.sport",
                                            "games.season",
                                            "games.game_id"]),
                      UniqueConstraint(sport, season, game_id, model_event_num, sub_event_num),
                      Index('ix_game_seq_players', game_id, person_id),
                      Index('ix_game_seq_opp', game_id, opp_team_id),
                      Index('ix_game_seq_team', game_id, team_id),
                      {})
