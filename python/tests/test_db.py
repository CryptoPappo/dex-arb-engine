import pytest
import os
import sys
import responses
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from db.models import (
        Base,
        Chains,
        Dexs,
        Tokens
)
from db.populate_tables import (
        populate_chains,
        populate_dex,
        populate_tokens,
        populate_pools
)

def test_tables_created():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "chains" in tables
    assert "dexs" in tables
    assert "tokens" in tables
    assert "pools" in tables

def test_populate_chains():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    chains = [
            Chains(
                chain_id=1,
                name="Ethereum",
                native_token="ETH",
                evm=True
            ),
            Chains(
                chain_id=56,
                name="Binance Smart Chain",
                native_token="BNB",
                evm=True
            )
    ]
    Session = sessionmaker(bind=engine)
    populate_chains(Session, chains)

    with Session() as session:
        rows = session.scalars(select(Chains)).all()
        assert len(rows) == 2
        eth = rows[0]
        assert eth.chain_id == 1
        assert eth.name == "Ethereum"
        assert eth.native_token == "ETH"
        assert eth.evm == True

def test_populate_dex():
    engine = create_engine("sqlite:///:memory:")
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

def test_duplicates():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine) 
    populate_chains(Session)
    populate_dex(Session)

    with pytest.raises(IntegrityError) as excinfo_chains:
        populate_chains(Session)
    
    with pytest.raises(IntegrityError) as excinfo_dex:
        populate_dex(Session)
    
    assert excinfo_chains.type is IntegrityError
    assert excinfo_dex.type is IntegrityError

@responses.activate
def test_populate_tokens():
    load_dotenv()
    coingecko_api = os.getenv("COINGECKO_API")
    url_chains = f"https://api.coingecko.com/api/v3/asset_platforms?x_cg_demo_api_key={coingecko_api}"
    mock_data_chains = [
            {
                "id": "ethereum",
                "chain_identifier": 1,
                "name": "Ethereum",
                "shortname": "",
                "native_coin_id": "ethereum",
                "image": {
                    "thumb": "",
                    "small": "",
                    "large": ""
                }
            }
    ]
    responses.add(
            responses.GET,
            url_chains,
            json=mock_data_chains,
            status=200
    )

    url_tokens = f"https://api.coingecko.com/api/v3/token_lists/ethereum/all.json?x_cg_demo_api_key={coingecko_api}"
    mock_data_tokens = {
        "name": "CoinGecko",
        "logoURI": "", 
        "keywords": ["defi"],
        "timestamp": "",
        "tokens": [
            {
                "chainId": 1,
                "address": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                "name": "Wrapped Bitcoin",
                "symbol": "WBTC",
                "decimals": 8,
                "logoURI": ""
            },
            {
                "chainId": 1,
                "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", 
                "name": "Wrapped Ethereum",
                "symbol": "WETH",
                "decimals": 18,
                "logoURI": ""
            }
        ]
    }
    
    responses.add(
            responses.GET,
            url_tokens,
            json=mock_data_tokens,
            status=200
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    populate_chains(Session)
    populate_tokens(Session) 
    
    with Session() as session:
        rows = session.scalars(select(Tokens)).all()
        assert len(rows) != 0
        
        wbtc = session.scalars(
                select(Tokens)
                .where(Tokens.chain_id == 1)
                .where(Tokens.symbol == "WBTC")
                ).first()
        assert wbtc.address == "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"
        assert wbtc.decimals == 8

def test_populate_pools():
    Session = MagicMock()

    fake_chain = MagicMock(chain_id=1, name="Ethereum")
    fake_chains = {1: fake_chain}
    fake_dex = MagicMock(dex_id=1, name="Uniswap", dex_type="V2", chain_id=1, factory_address="0x")
    fake_dexs = {1: fake_dex}
    fake_w3 = MagicMock()
    fake_w3_by_chain = {1: fake_w3}

    fake_adapter = MagicMock()
    fake_adapter.fetch_pools.return_value = ["pool1", "pool2"]

    def fake_adapter_factory(dex_name, dex_type, factory_contract, multicall_contract,
            tokens, chain_id, dex_id):
        return fake_adapter

    def fake_abi_loader(path, chain_id, address, save):
        return {"fake": "abi"}
    
    with patch("db.populate_tables.populate_table") as insert_mock:
        populate_pools(
                Session,
                chains=fake_chains,
                dexs=fake_dexs,
                web3_by_chain=fake_w3_by_chain,
                abi_loader=fake_abi_loader,
                adapter_factory=fake_adapter_factory
        )

    fake_adapter.fetch_pools.assert_called_once()
    insert_mock.assert_called_once_with(Session, ["pool1", "pool2"])
