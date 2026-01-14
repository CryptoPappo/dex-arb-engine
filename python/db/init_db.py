from connection import create_connection
from models import Base

def init_db():
    engine = create_connection()
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
