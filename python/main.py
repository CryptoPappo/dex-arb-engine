from web3 import Web3

from db.utils.logging import get_logger
from db.utils.tools import require_env
from db.connection import create_connection
from db.models import Base
from db.config import CHAINS, DEXS
from db.populate_tables import (
        populate_chains,
        populate_dex,
        populate_tokens,
        populate_pools
)
logger = get_logger("main")

def main():
    logger.info("Starting dex-arb-engine bootstrap")

    engine, session = create_connection("DATABASE_URL")

    logger.info("Creating database schema")
    Base.metadata.create_all(engine)

    logger.info("Populating chains")
    populate_chains(session)

    logger.info("Populating DEXs")
    populate_dex(session)

    logger.info("Populating tokens")
    populate_tokens(session)

    rpc_api = require_env("RPC_API")
    web3_by_chain = {}
    for chain in CHAINS.values():
        rpc_url = chain.rpc_url + rpc_api
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            raise RuntimeError(f"RPC down for chain {chain.name}")

    logger.info("Populating pools")
    populate_pools(
            session,
            CHAINS,
            DEXS,
            web3_by_chain,
    )

    logger.info("Bootstrap completed successfully")

with Session() as session:
            tokens = session.scalars(
                    select(Tokens)
                    .where(Tokens.chain_id == chain.chain_id)
            ).all()
if __name__ == "__main__":
    main()
