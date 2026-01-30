from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine

def create_connection(db_url: str) -> Engine:
    engine = create_engine(db_url)

    return engine
