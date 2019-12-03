from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

db_path = '/Volumes/Sports Data/nba_staging_data.db'

Engine = create_engine('sqlite:///{}'.format(db_path))

Session = sessionmaker(bind=Engine)
