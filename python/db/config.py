from dataclasses import dataclass
from pathlib import Path
import json
import os

@dataclass(frozen=True)
class ChainConfig:
    chain_id: int
    name: str
    native_token: str
    evm: bool
    rpc_url: str

@dataclass(frozen=True)
class DexConfig:
    dex_id: int
    chain_id: int
    name: str
    dex_type: str
    factory_address: str
    quoter_address: str | None = None

MULTICALL_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"
CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"

def load_chains() -> list[ChainConfig]:
    with open(CONFIG_DIR / "chains.json") as f:
        data = json.load(f) 

    chains = []
    for chain in data:
        rpc_url = os.environ[chain["rpc_url"].strip("${}")]
        chains.append(
                ChainConfig(
                    chain_id=chain["chain_id"],
                    name=chain["name"],
                    native_token=chain["native_token"],
                    evm=chain["evm"],
                    rpc_url=rpc_url,
                )
        )
    
    return chains

def load_dexs() -> list[DexConfig]:
    with open(CONFIG_DIR / "dexs.json") as f:
        data = json.load(f) 

    dexs = []
    for dex in data:
        rpc_url = os.environ[dex["rpc_url"].strip("${}")]
        dexs.append(
                DexConfig(
                    dex_id=dex["dex_id"],
                    chain_id=dex["chain_id"],
                    name=dex["name"],
                    dex_type=dex["dex_type"],
                    factory_address=dex["factory_address"],
                    quoter_address=dex["quoter_address"],
                )
        )

    return dexs
