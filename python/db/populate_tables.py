import requests
from web3 import Web3
from sqlalchemy import select
from sqlalchemy.orm.session import sessionmaker

from db.models import Chains, Dex, Tokens
from db.dex import build_adapter
from db.utils.logging import get_logger 
from db.utils.tools import require_env
from db.utils.abi import require_abi
from db.config import CHAINS, DEXS, MULTICALL_ADDRESS
logger = get_logger("populate_tables")

def populate_chains(Session: sessionmaker):
    chains = [
            Chains(
                chain_id=chain.chain_id,
                name=chain.name,
                native_token=chain.native_token,
                evm=chain.evm,
            )
            for chain in CHAINS.values()
    ]

    with Session() as session:
        session.add_all(chains)
        session.commit()
    
    logger.info(f"Inserted {len(chains)} chains")
    
def populate_dex(Session: sessionmaker):
    dexs = [
            Dex(
                dex_id=dex.dex_id,
                chain_id=dex.chain_id,
                name=dex.name,
                dex_type=dex.dex_type,
                factory_address=dex.factory_address,
                quoter_address=dex.quoter_address,
            )
            for dex in DEXS.values()
    ]

    with Session() as session:
        session.add_all(dexs)
        session.commit()
    
    logger.info(f"Inserted {len(dexs)} dexs")

def populate_tokens(Session: sessionmaker):
    chain_ids = CHAINS.keys()
    coingecko_api = require_env("COINGECKO_API")
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
            address=token["address"],
            decimals=token["decimals"]
          )
        for token in tokens_data
    ]

    with Session() as session:
        session.add_all(tokens)
        session.commit()

    logger.info(f"Inserted {len(tokens)} tokens")

def populate_pools(Session: sessionmaker):
    rpc_api = require_env("ALCHEMY_API")
    multicall_abi = require_abi(
            file_path="db/abi/multicall_abi.json",
            address=MULTICALL_ADDRESS
    )

    for chain in CHAINS.values():
        rpc_url = chain.rpc_url + rpc_api
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise RuntimeError(f"Failed to connect to RPC at {rpc_url}")
        
        multicall_contract = w3.eth.contract(
                address=MULTICALL_ADDRESS,
                abi=multicall_abi
        )

        with Session() as session:
            tokens = session.scalars(
                    select(Tokens)
                    .where(Tokens.chain_id == chain.chain_id)
            ).all()

        for dex in DEXS.values():
            abi = require_abi(
                   file_path=f"db/abi/{dex.name}_{dex.dex_type}_abi.json",
                   chain_id=dex.chain_id,
                   address=dex.factory_address
            )
            factory_contract = w3.eth.contract(
                    address=dex.factory_address,
                    abi=abi
            )
            adapter = build_adapter(
                    dex_name=dex.name,
                    dex_type=dex.dex_type,
                    factory_contract=factory_contract,
                    multicall_contract=multicall_contract,
                    tokens=tokens,
                    chain_id=dex.chain_id,
                    dex_id=dex.dex_id
            )
            
            pools = adapter.fetch_pools() 
            with Session() as session:
                session.add_all(pools)
                session.commit()
            
            logger.info(f"Inserted {len(pools)} pools: chain={dex.chain_id} dex={dex.name} {dex.dex_type}")
