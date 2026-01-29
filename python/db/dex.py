from typing import Optional, Iterator, Tuple, Any
from abc import ABC, abstractmethod
from web3 import Web3
from eth_abi import abi
from models import Tokens, Pools

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

def decode_data(
        function_names: list[str],
        data_list: list[bytes],
        pool_abi: list[dict]
    ) -> list[Any]:
    response = []
    for function_name, data in zip(function_names, data_list):
        function_types = []
        for item in pool_abi:
            try:
                name = item["name"]
            except KeyError:
                continue
            else:
                if name == function_name:
                    function_types = [outputs["internalType"] for outputs in item["outputs"]]
        if function_types:
            response.append(abi.decode(function_types, data))
    return response

def token_pair_fee_iter(
        tokens: list[Tokens],
        fees: Optional[list[int]] = None
) -> Iterator[Tuple[Tokens, Tokens, int | None]]:
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens)):
            if int(tokens[i].address, 16) < int(tokens[j].address):
                token0 = tokens[i]
                tokens1 = tokens[j]
            else:
                tokens0 = tokens[j]
                tokens1 = tokens[i]

            if fees is None:
                yield tokens0, tokens1
            else:
                for fee in fees:
                    yield tokens0, tokens1, fee

class DexAdapter(ABC):

    @abstractmethod
    def _pool_combinations(self) ->  Iterator[Tuple[Tokens, Tokens, int | None]]:
        """Iterator that yields tokens and fees combinations"""

    @abstractmethod
    def fetch_pools(self) -> list[Pools]:
        """Return pool data"""

class UniswapV2Adapter(DexAdapter):

    def __init__(
            self,
            web3: Web3,
            factory_address: str, 
            multicall_address: str,
            tokens: list[Tokens],
            chain_id: int,
            dex_id: int
    ):   
        with open("abi/uniswap_v2_abi.json") as f:
            abi_json = json.load(f)
            abi_factory = abi_json["abi"]
        self.factory_contract = web3.eth.contract(
                address=factory_address,
                abi=abi_factory
        )
        self.abi_factory = abi_factory
        with open("abi/multicall_abi.json") as f:
            abi_json = json.load(f)
            abi_multicall = abi_json["abi"]
        self.multicall_contract = web3.eth.contract(
                address=multicall_address,
                abi=abi_multicall
        )
        self.tokens = tokens
        self.chain_id = chain_id
        self.dex_id = dex_id

    def _pool_combinations(self) ->  Iterator[Tuple[Tokens, Tokens]]:
        yield from token_pair_fee_iter(self.tokens)

    def fetch_pools(self) -> list[Pools]:
        calls = []
        pools = []
        for token0, token1 in self._pool_combinations():
            calls.append(
                (
                    self.factory_contract.address,
                    True,
                    self.factory_contract.functions
                    .getPair(token0, token1)
                    ._encode_transaction_data(),
                )
            )
            pools.append(
                    Pools(
                        chain_id = self.chain_id,
                        dex_id = self.dex_id,
                        pool_address = "",
                        token0 = token0.address,
                        token1 = token1.address,
                        fee = 3000,
                    )
            )
        data_encoded = self.multicall_contract.functions.aggregate3(calls).call()
        
        for data, index in enumerate(data_encoded):
            pool_data = decode_data(
                    ["getPair"],
                    [data[1]],
                    self.abi_factory
            )
            pool_address = pool_data[0][0]

            if pool_address != ZERO_ADDRESS:
                pools[index].pool_address = pool_address
            else:
                _ = pools.pop(index)

        return pools
