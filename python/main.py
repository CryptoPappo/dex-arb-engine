
from db.utils.logging import get_logger
from db.connection import create_connection
from db.models import Base
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

    logger.info("Populating pools")
    populate_pools(session)

    logger.info("Bootstrap completed successfully")

if __name__ == "__main__":
    main()
