import requests
from typing import Union, Callable, TypeAlias
from web3 import Web3
from web3.contract.contract import Contract
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert, Insert
from sqlalchemy.orm.session import sessionmaker

from db.dex import DexAdapter, build_adapter
from db.utils.logging import get_logger 
from db.utils.tools import require_env
from db.utils.abi import require_abi
from db.config import (
        CHAINS,
        DEXS, 
        MULTICALL_ADDRESS,
        ChainConfig,
        DexConfig
)
from db.models import (
        Chains,
        Dexs,
        Tokens,
        Pools
)
AbiLoader: TypeAlias = Callable[
        [str, int, str, bool],
        list[dict[str, str]]
] 
AdapterFactory: TypeAlias = Callable[
        [str, str, Contract, Contract, list[Tokens], int, int],
        DexAdapter
]
logger = get_logger("populate_tables")

def populate_table(
        Session: sessionmaker,
        stmt: Insert
) -> int:
    with Session() as session:
        result = session.execute(stmt)
        inserted = result.rowcount
        session.commit()

    return inserted

def populate_chains(
        Session: sessionmaker,
        chains: list[Union[Chains, ChainConfig]]
):
    chains_dict = [
            {
                "chain_id": chain.chain_id,
                "name": chain.name,
                "native_token": chain.native_token,
                "evm": chain.evm
            }
            for chain in chains
    ]
    stmt = insert(Chains).values(chains_dict)
    stmt = stmt.on_conflict_do_nothing(
            index_elements=[Chains.chain_id]
    )
        
    inserted = populate_table(Session, stmt)
    logger.info(f"Chains insert: attempted={len(chains_dict)} inserted={inserted}")
    
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

    populate_table(Session, dexs)    
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

    populate_table(Session, tokens)
    logger.info(f"Inserted {len(tokens)} tokens")

def populate_pools(
        Session: sessionmaker,
        chains: list[ChainConfig],
        dexs: list[DexConfig],
        web3_by_chain: dict[int, Web3],
        abi_loader: AbiLoader = require_abi,
        adapter_factory: AdapterFactory = build_adapter
    ):
    multicall_abi = abi_loader(
            "db/abi/multicall_abi.json",
            1,
            MULTICALL_ADDRESS,
            True
    )

    for chain in chains.values():
        w3 = web3_by_chain[chain.chain_id]
        
        multicall_contract = w3.eth.contract(
                address=MULTICALL_ADDRESS,
                abi=multicall_abi
        )

        with Session() as session:
            tokens = session.scalars(
                    select(Tokens)
                    .where(Tokens.chain_id == chain.chain_id)
            ).all()

        for dex in dexs.values():
            abi = abi_loader(
                   f"db/abi/{dex.name}_{dex.dex_type}_abi.json",
                   dex.chain_id,
                   dex.factory_address,
                   True
            )
            factory_contract = w3.eth.contract(
                    address=dex.factory_address,
                    abi=abi
            )
            adapter = adapter_factory(
                    dex_name=dex.name,
                    dex_type=dex.dex_type,
                    factory_contract=factory_contract,
                    multicall_contract=multicall_contract,
                    tokens=tokens,
                    chain_id=dex.chain_id,
                    dex_id=dex.dex_id
            )
            pools = adapter.fetch_pools() 

            populate_table(Session, pools)
            logger.info(f"Inserted {len(pools)} pools: chain={dex.chain_id} dex={dex.name} {dex.dex_type}")
