import requests
import os
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Chains, Dex, Tokens

def populate_chains(session: Session):
    chains = [
            Chains(chain_id=1, name="Ethereum", native_token="ETH", evm_compatible=True),
            Chains(chain_id=42161, name="Arbitrum", native_token="ETH", evm_compatible=True),
            Chains(chain_id=56, name="Bsc", native_token="BNB", evm_compatible=True)
    ]

    with session() as session:
        session.add_all(chains)
        session.commit()

def populate_dex(session: Session):
    dexs = [
            Dex(chain_id=1, name="Uniswap", dex_type="V2", 
                factory_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                quoter_address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"),
            Dex(chain_id=42161, name="Uniswap", dex_type="V2",
                factory_address="0xf1D7CC64Fb4452F05c498126312eBE29f30Fbcf9",
                quoter_address="0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24"),
            Dex(chain_id=56, name="Uniswap", dex_type="V2",
                factory_address="0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6",
                quoter_address="0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24"),
            Dex(chain_id=1, name="Uniswap", dex_type="V3",
                factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
                quoter_address="0x61fFE014bA17989E743c5F6cB21bF9697530B21e"),
            Dex(chain_id=42161, name="Uniswap", dex_type="V3",
                factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
                quoter_address="0x61fFE014bA17989E743c5F6cB21bF9697530B21e"),
            Dex(chain_id=56, name="Uniswap", dex_type="V3",
                factory_address="0xdB1d10011AD0Ff90774D0C6Bb92e5C5c8b4461F7",
                quoter_address="0x78D78E420Da98ad378D7799bE8f4AF69033EB077"),
            Dex(chain_id=1, name="Uniswap", dex_type="V4",
                factory_address="0x7ffe42c4a5deea5b0fec41c94c136cf115597227",
                quoter_address="0x52f0e24d1c21c8a0cb1e5a5dd6198556bd9e1203"),
            Dex(chain_id=42161, name="Uniswap", dex_type="V4",
                factory_address="0x76fd297e2d437cd7f76d50f01afe6160f86e9990",
                quoter_address="0x3972c00f7ed4885e145823eb7c655375d275a1c5"),
            Dex(chain_id=56, name="Uniswap", dex_type="V4",
                factory_address="0xd13dd3d6e93f276fafc9db9e6bb47c1180aee0c4",
                quoter_address="0x9f75dd27d6664c475b90e105573e550ff69437b0")
    ]

    with session() as session:
        session.add_all(dexs)
        session.commit()

def populate_tokens(session: Session):
    chain_ids = []
    with session() as session_:
        rows = session_.scalars(select(Chains)).all()
        for row in rows:
            chain_ids.append(row.chain_id)

    load_dotenv()
    coingecko_api = os.getenv("COINGECKO_API")

    platform_ids = []
    url = f"https://api.coingecko.com/api/v3/asset_platforms?x_cg_demo_api_key={coingecko_api}"
    response = requests.get(url)
    response.raise_for_status()
    chains = response.json()
    for chain in chains:
        if chain["chain_identifier"] in chain_ids:
            platform_ids.append(chain["id"])

    tokens_data = []
    for platform_id in platform_ids:
        url = f"https://api.coingecko.com/api/v3/token_lists/{platform_id}/all.json?x_cg_demo_api_key={coingecko_api}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        tokens_data.extend(data["tokens"])

    tokens = [
        Tokens(
            chain_id=token["chainId"],
            name=token["name"], 
            symbol=token["symbol"], 
            token_address=token["address"],
            decimals=token["decimals"]
          )
        for token in tokens_data
    ]

    with session() as session:
        session.add_all(tokens)
        session.commit()
