import pytest
import os
import sys
from unittest.mock import MagicMock
from eth_abi import encode

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from db.models import Tokens
from db.dex import UniswapV2Adapter

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

def make_mock_factory_v2(return_map):
    factory = MagicMock()
    factory.address = ""
    factory.abi = {
            "name": "getPair",
            "outputs": [
                {
                    "internalType":"address",
                    "name":"",
                    "type":"address"
                 }
            ]
    }

    def get_pair(token0, token1):
        pair_address = return_map.get((token0.symbol, token1.symbol), ZERO_ADDRESS)
        encoded_data = MagicMock()
        encoded_data._encode_transaction_data.return_value = pair_address

        return encoded_data

    factory.functions.getPair.side_effect = get_pair
    
    return factory

def make_mock_multicall():
    multicall = MagicMock()
    
    def aggregate(calls):
        addresses = [[True, encode(["address"], [address])] for _, _, address in calls]
        call = MagicMock()
        call.call.return_value = addresses

        return call
    
    multicall.functions.aggregate3.side_effect = aggregate

    return multicall

def test_uniswap_v2_adapter_filters_zero_address():
    tokens = [
            Tokens(coin_id=1, chain_id=1, name="", symbol="WBTC", address="0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", decimals=18),
            Tokens(coin_id=2, chain_id=1, name="", symbol="WETH", address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", decimals=18),
            Tokens(coin_id=3, chain_id=1, name="", symbol="USDC", address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", decimals=18),
            Tokens(coin_id=4, chain_id=1, name="", symbol="USDT", address="0xdac17f958d2ee523a2206206994597c13d831ec7", decimals=18),
    ]
    return_map = {
            ("WBTC", "WETH"): "0xCBCdF9626bC03E24f779434178A73a0B4bad62eD",
            ("WBTC", "USDC"): "0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35",
            ("WETH", "USDT"): "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36",
    }
    
    factory = make_mock_factory_v2(return_map)
    multicall = make_mock_multicall()

    adapter = UniswapV2Adapter(
            factory_contract=factory,
            multicall_contract=multicall,
            tokens=tokens,
            chain_id=1,
            dex_id=1,
    )
    
    pools = adapter.fetch_pools()

    assert len(pools) == 3
    assert {pool.pool_address for pool in pools} == {pool for pool in return_map.values()}

