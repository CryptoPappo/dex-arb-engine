import pytest
import os
import sys
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from db.connection import create_connection
from db.models import Base, Chains, Dex
from db.populate_tables import populate_chains, populate_dex

def test_tables_created():
    engine = create_connection("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "chains" in tables
    assert "dex" in tables
    assert "tokens" in tables
    assert "pools" in tables

def test_populate_chains():
    engine = create_connection("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    populate_chains(Session)

    with Session() as session:
        eth = session.get(Chains, 1)
        assert eth.chain_id == 1
        assert eth.name == "Ethereum"
        assert eth.native_token == "ETH"
        assert eth.evm_compatible == True

def test_populate_dex():
    engine = create_connection("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    populate_dex(Session)

    with Session() as session:
        dex = session.get(Dex, 1)
        assert dex.chain_id == 1
        assert dex.name == "Uniswap"
        assert dex.dex_type == "V2"
        assert dex.factory_address == "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
        assert dex.quoter_address == "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
