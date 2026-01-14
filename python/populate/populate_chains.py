from db.connection import create_connection
from db.models import Chains
from sqlalchemy.orm import sessionmaker

def populate_chains():
    engine = create_connection()
    Session = sessionmaker(engine)
    
    chains = [
            Chains(chain_id=1, name="Ethereum", native_token="ETH", evm_compatible=True),
            Chains(chain_id=42161, name="Arbitrum", native_token="ETH", evm_compatible=True),
            Chain(chain_id=56, name="Bsc", native_token="BNB", evm_compatible=True)
    ]

    with Session() as session:
        session.add_all(chains)
        session.commit()
