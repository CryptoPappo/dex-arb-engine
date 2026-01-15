from typing import Union
from connection import create_connection
from models import Base

def init_db(db_url: Union[str, None] = None):
    engine = create_connection(db_url)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
