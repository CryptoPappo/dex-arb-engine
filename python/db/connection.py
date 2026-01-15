import os
from typing import Union
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine

def create_connection(db_url: Union[str, None] = None) -> Engine:
    if db_url is None: 
        db_url = os.getenv("DB_URL")
    engine = create_engine(db_url)

    return engine
