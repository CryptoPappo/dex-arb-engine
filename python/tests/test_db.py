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
        Tokens,
        Pools
)
from db.populate_tables import (
        populate_chains,
        populate_dexs,
        populate_tokens,
        populate_pools
)

def mock_chains():
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
    
    return chains

def mock_dexs():
    dexs = [
            Dexs(
                dex_id=1,
                chain_id=1,
                name="Uniswap",
                dex_type="V2",
                factory_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                quoter_address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
            ),
            Dexs(
                dex_id=2,
                chain_id=1,
                name="Uniswap",
                dex_type="V3",
                factory_address="0x6C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                quoter_address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
            )
    ]

    return dexs

def mock_pools():
    pools = [
            Pools(
                chain_id=1,
                pool_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                dex_id=1,
                token0=1,
                token1=2,
                fee=100,
                tick_spacing=10
            ),
            Pools(
                chain_id=1,
                pool_address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                dex_id=1,
                token0=1,
                token1=2,
                fee=100,
                tick_spacing=10
            )
    ]
    
    return pools

def mock_tokens():
    tokens = [
            Tokens(
                coin_id=1,
                chain_id=1,
                name="Wrapped Bitcoin",
                symbol="WBTC",
                address="",
                decimals=8
            ),
            Tokens(
                coin_id=2,
                chain_id=1,
                name="Wrapped Ethereum",
                symbol="WETH",
                address="",
                decimals=18
            )
    ]
    
    return tokens

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
    
    chains = mock_chains() 
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

def test_populate_dexs():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    dexs = mock_dexs()
    populate_dexs(Session, dexs)

    with Session() as session:
        rows = session.scalars(select(Dexs)).all()
        assert len(rows) == 2
        dex = rows[0]
        assert dex.chain_id == 1
        assert dex.name == "Uniswap"
        assert dex.dex_type == "V2"
        assert dex.factory_address == "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
        assert dex.quoter_address == "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

def test_duplicates():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    chains = mock_chains()
    dexs = mock_dexs()

    Session = sessionmaker(bind=engine) 
    populate_chains(Session, chains)
    populate_dexs(Session, dexs)

    with Session() as session:
        rows_chains = session.scalars(select(Chains)).all()
        rows_dexs = session.scalars(select(Dexs)).all()
        initial_chains = len(rows_chains)
        initial_dexs = len(rows_dexs)

    populate_chains(Session, chains)
    populate_dexs(Session, dexs)

    with Session() as session:
        rows_chains = session.scalars(select(Chains)).all()
        rows_dexs = session.scalars(select(Dexs)).all()
        final_chains = len(rows_chains)
        final_dexs = len(rows_dexs)
    
    assert initial_chains == final_chains
    assert initial_dexs == final_dexs
    
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
    chains = mock_chains()
    populate_tokens(Session, chains) 
    
    with Session() as session:
        rows = session.scalars(select(Tokens)).all()
        assert len(rows) == 2
        wbtc = rows[0] 
        assert wbtc.address == "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"
        assert wbtc.decimals == 8

def test_populate_pools():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    chains = mock_chains()[:1]
    dexs = mock_dexs()[:1]
    tokens = mock_tokens()
    tokens_by_chain = {1: tokens}
    pools = mock_pools()

    fake_w3 = MagicMock()
    fake_w3_by_chain = {1: fake_w3}

    fake_adapter = MagicMock()
    fake_adapter.fetch_pools.return_value = pools

    def fake_adapter_factory(dex_name, dex_type, factory_contract, multicall_contract,
            tokens, chain_id, dex_id):
        return fake_adapter

    def fake_abi_loader(path, chain_id, address, save):
        return {"fake": "abi"}
    
    populate_pools(
            Session,
            chains=chains,
            dexs=dexs,
            tokens_by_chain=tokens_by_chain,
            web3_by_chain=fake_w3_by_chain,
            abi_loader=fake_abi_loader,
            adapter_factory=fake_adapter_factory
    )

    fake_adapter.fetch_pools.assert_called_once()
    with Session() as session:
        rows = session.scalars(select(Pools)).all()
        assert len(rows) == 2
        pool0 = rows[0]
        assert pool0.chain_id == 1
        assert pool0.pool_address == "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
        assert pool0.dex_id == 1
        assert pool0.token0 == 1
        assert pool0.token1 == 2
        assert pool0.fee == 100
        assert pool0.tick_spacing == 10
