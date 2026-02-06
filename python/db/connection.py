from typing import Tuple
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.session import sessionmaker as Session

from db.utils.tools import require_env

def create_connection(env_const: str) -> Tuple[Engine, Session]:
    db_url = require_env(env_const)
    engine = create_engine(db_url)
    session = sessionmaker(bind=engine)    

    return engine, session
