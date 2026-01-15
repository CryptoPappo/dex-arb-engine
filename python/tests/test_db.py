import pytest
import os
import sys
from sqlalchemy import inspect

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from db.connection import create_connection
from db.models import Base

def test_tables_created():
    engine = create_connection("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "chains" in tables
    assert "dex" in tables
    assert "tokens" in tables
    assert "pools" in tables

