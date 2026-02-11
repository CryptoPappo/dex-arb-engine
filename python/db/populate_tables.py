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
    
def populate_dexs(
        Session: sessionmaker,
        dexs: list[Union[Dexs, DexConfig]]
):
    dexs_dict = [
            {
                "dex_id": dex.dex_id,
                "chain_id": dex.chain_id,
                "name": dex.name,
                "dex_type": dex.dex_type,
                "factory_address": dex.factory_address,
                "quoter_address": dex.quoter_address,
            }
            for dex in dexs
    ]
    stmt = insert(Dexs).values(dexs_dict)
    stmt = stmt.on_conflict_do_nothing(
            constraint="uq_dex_address_chain"
    )
    
    inserted = populate_table(Session, stmt)    
    logger.info(f"Dexs insert: attempted={len(dexs_dict)} inserted={inserted}")

def populate_tokens(
        Session: sessionmaker,
        chains: list[Union[Chains, ChainConfig]],
):
    chain_ids = [chain.chain_id for chain in chains]
    coingecko_api = require_env("COINGECKO_API")
    platform_ids = []
    url = f"https://api.coingecko.com/api/v3/asset_platforms?x_cg_demo_api_key={coingecko_api}"
    response = requests.get(url)
    response.raise_for_status()
    chains_gecko = response.json()
    for chain in chains_gecko:
        if chain["chain_identifier"] in chain_ids:
            platform_ids.append(chain["id"])

    tokens_data = []
    for platform_id in platform_ids:
        url = f"https://api.coingecko.com/api/v3/token_lists/{platform_id}/all.json?x_cg_demo_api_key={coingecko_api}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        tokens_data.extend(data["tokens"])

    tokens_dict = [
            {
                "chain_id": token["chainId"],
                "name": token["name"], 
                "symbol": token["symbol"], 
                "address": token["address"],
                "decimals": token["decimals"]
            }
            for token in tokens_data
    ]
    stmt = insert(Tokens).values(tokens_dict)
    stmt = stmt.on_conflict_do_nothing(
            constraint="uq_tokens_address_chain"
    )

    inserted = populate_table(Session, stmt)
    logger.info(f"Tokens insert: attempted={len(tokens_dict)} inserted={inserted}")

def populate_pools(
        Session: sessionmaker,
        chains: list[Union[Chains, ChainConfig]],
        dexs: list[Union[Dexs, DexConfig]],
        tokens_by_chain: dict[int, list[Tokens]],
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

    for chain in chains:
        w3 = web3_by_chain[chain.chain_id]
        multicall_contract = w3.eth.contract(
                address=Web3.to_checksum_address(MULTICALL_ADDRESS),
                abi=multicall_abi
        )
        tokens = tokens_by_chain[chain.chain_id]
        for dex in dexs:
            abi = abi_loader(
                   f"db/abi/{dex.name}_{dex.dex_type}_abi.json",
                   dex.chain_id,
                   dex.factory_address,
                   True
            )
            factory_contract = w3.eth.contract(
                    address=Web3.to_checksum_address(dex.factory_address),
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
            
            if len(pools) == 0:
                continue

            pools_dict = [
                    {
                        "chain_id": pool.chain_id,
                        "pool_address": pool.pool_address,
                        "dex_id": pool.dex_id,
                        "token0": pool.token0,
                        "token1": pool.token1,
                        "fee": pool.fee,
                        "tick_spacing": pool.tick_spacing,
                    }
                    for pool in pools
            ]
            stmt = insert(Pools).values(pools_dict)
            stmt = stmt.on_conflict_do_nothing(
                   constraint="pools_pkey"
            )

            inserted = populate_table(Session, stmt)
            logger.info(f"Pools chain={dex.chain_id} dex={dex.name}-{dex.dex_type} insert: \
attempted={len(pools_dict)} inserted={inserted}")
