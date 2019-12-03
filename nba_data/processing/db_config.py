from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_path = '/Volumes/Sports Data/nba_data.db'

Base = declarative_base()

Engine = create_engine('sqlite:///{}'.format(db_path))

Session = sessionmaker(bind=Engine)
