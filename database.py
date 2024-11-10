import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL="sqlite:///./smartloans.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread':False})

SessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine)

Base = sqlalchemy.orm.declarative_base()