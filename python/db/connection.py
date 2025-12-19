import os
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine

def create_connection() -> Engine:
    db_url = os.getenv("DB_URL")
    engine = create_engine(db_url)

    return engine
