import os
from dotenv import load_dotenv
import requests

def download_abi(
        chain_id: str,
        address: str
    ) -> dict[str]:
    load_dotenv()
    etherscan_api = os.getenv("ETHERSCAN_API")
    if etherscan_api is None:
        raise Exception("Set your etherscan api in the .env file")

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
