import os
from typing import Tuple
from dotenv import load_dotenv
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.session import sessionmaker as Session

def create_connection(env_const: str) -> Tuple[Engine, Session]:
    load_dotenv()
    db_url = os.getenv(env_const)
    if db_url is None:
        raise Exception(".env constant not found.")

    engine = create_engine(db_url)
    session = sessionmaker(bind=engine)    

    return engine, session
