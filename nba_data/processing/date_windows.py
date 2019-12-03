from sqlalchemy import Column, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import (DATE, INTEGER)
from .db_config import Base

class DateWindow(Base):
    __tablename__ = 'date_windows'

    id = Column(INTEGER, primary_key=True, nullable=False)
    game_date_est = Column(DATE, nullable=False)
    window_date = Column(DATE, nullable=False)
    days_lag = Column(INTEGER, nullable=False)

    __table_args__ = (ForeignKeyConstraint([game_date_est],
                                           ["games.game_date_est"]),
                      UniqueConstraint(game_date_est, window_date, days_lag,
                                       name='uix_date_windows'),
                      Index('ix_date_windows', game_date_est, window_date, days_lag),
                      {})
