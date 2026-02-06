import requests
import json

from db.utils.tools import require_env
from db.utils.logging import get_logger
logger = get_logger("abi")

def download_abi(
        chain_id: str,
        address: str
    ) -> dict[str]:
    etherscan_api = require_env("ETHERSCAN_API")
    url = "https://api.etherscan.io/v2/api"
    params = {
            "apikey": etherscan_api,
            "chainid": chain_id,
            "module": "contract",
            "action": "getabi",
            "address": address,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    abi = response.json()

    return abi

def require_abi(
        file_path: str,
        chain_id: int = 1,
        address: str = "",
        save: bool = True
    ) -> dict[str]:
    try:
        with open(file_path) as f:
            abi = json.load(f)
    except FileNotFoundError:
        abi = download_abi(chain_id, address)
        if save:
            try:
                with open(file_path, "w") as f:
                    json.dump(abi, file_path)
                logger.info(f"Abi successfully saved to {file_path}")
            except IOError as e:
                logger.warning(f"Error saving abi: {e}")

    return abi

