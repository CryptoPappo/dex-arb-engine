import pytest
import os
import sys
from unittest.mock import MagicMock
import eth_abi as eth
import eth_hash.auto as ethash
from web3 import Web3

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from db.models import Tokens
from db.dex import UniswapV2Adapter, UniswapV3Adapter, UniswapV4Adapter

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

def make_mock_factory_v2(return_map):
    factory = MagicMock()
    factory.address = ZERO_ADDRESS  
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
        pair_address = return_map.get((Web3.to_checksum_address(token0), Web3.to_checksum_address(token1)), ZERO_ADDRESS)
        encoded_data = MagicMock()
        encoded_data._encode_transaction_data.return_value = eth.encode(["address"], [pair_address])

        return encoded_data

    factory.functions.getPair.side_effect = get_pair
    
    return factory

def make_mock_factory_v3(return_map):
    factory = MagicMock()
    factory.address = ZERO_ADDRESS 
    factory.abi = {
            "name": "getPool",
            "outputs": [
                {
                    "internalType":"address",
                    "name":"",
                    "type":"address"
                 }
            ]
    }

    def get_pool(token0, token1, fee):
        pair_address = return_map.get((Web3.to_checksum_address(token0), Web3.to_checksum_address(token1), fee), ZERO_ADDRESS)
        encoded_data = MagicMock()
        encoded_data._encode_transaction_data.return_value = eth.encode(["address"], [pair_address])

        return encoded_data

    factory.functions.getPool.side_effect = get_pool
    
    return factory

def make_mock_factory_v4(return_map):
    factory = MagicMock()
    factory.address = ZERO_ADDRESS 
    factory.abi = {
            "name": "getLiquidity",
            "outputs": [
                {
                    "internalType":"uint128",
                    "name":"liquidity",
                    "type":"uint128"
                 }
            ]
    }

    def get_liquidity(pool_id):
        liquidity = return_map.get(pool_id, 0)
        encoded_data = MagicMock()
        encoded_data._encode_transaction_data.return_value = eth.encode(["uint128"], [liquidity])

        return encoded_data

    factory.functions.getLiquidity.side_effect = get_liquidity
    
    return factory

def make_mock_multicall():
    multicall = MagicMock()
    
    def aggregate(calls):
        data_encoded = [[True, data] for _, _, data in calls]
        call = MagicMock()
        call.call.return_value = data_encoded

        return call
    
    multicall.functions.aggregate3.side_effect = aggregate

    return multicall

def test_uniswap_v2_adapter_filters_zero_address():
    wbtc = Tokens(coin_id=1, chain_id=1, name="", symbol="WBTC", 
            address=Web3.to_checksum_address("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"), decimals=18)
    weth = Tokens(coin_id=2, chain_id=1, name="", symbol="WETH",
            address=Web3.to_checksum_address("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"), decimals=18)
    usdc = Tokens(coin_id=3, chain_id=1, name="", symbol="USDC",
            address=Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"), decimals=18)
    usdt = Tokens(coin_id=4, chain_id=1, name="", symbol="USDT",
            address=Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7"), decimals=18)

    tokens = [wbtc, weth, usdc, usdt]
    return_map = {
            (wbtc.address, weth.address): "0xCBCdF9626bC03E24f779434178A73a0B4bad62eD",
            (wbtc.address, usdc.address): "0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35",
            (weth.address, usdt.address): "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36",
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

def test_uniswap_v3_adapter_filters_zero_address():
    wbtc = Tokens(coin_id=1, chain_id=1, name="", symbol="WBTC",
            address=Web3.to_checksum_address("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"), decimals=18)
    weth = Tokens(coin_id=2, chain_id=1, name="", symbol="WETH",
            address=Web3.to_checksum_address("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"), decimals=18)
    usdc = Tokens(coin_id=3, chain_id=1, name="", symbol="USDC",
            address=Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"), decimals=18)
    usdt = Tokens(coin_id=4, chain_id=1, name="", symbol="USDT",
            address=Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7"), decimals=18)

    tokens = [wbtc, weth, usdc, usdt]
    return_map = {
            (wbtc.address, weth.address, 10000): "0xCBCdF9626bC03E24f779434178A73a0B4bad62eD",
            (wbtc.address, usdc.address, 3000): "0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35",
            (weth.address, usdt.address, 500): "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36",
    }
    
    factory = make_mock_factory_v3(return_map)
    multicall = make_mock_multicall()

    adapter = UniswapV3Adapter(
            factory_contract=factory,
            multicall_contract=multicall,
            tokens=tokens,
            chain_id=1,
            dex_id=1,
    )
    
    pools = adapter.fetch_pools()

    assert len(pools) == 3
    assert {pool.pool_address for pool in pools} == {pool for pool in return_map.values()}


def test_uniswap_v4_adapter_filters_zero_address():
    wbtc = Tokens(coin_id=1, chain_id=1, name="", symbol="WBTC", address="0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", decimals=18)
    weth = Tokens(coin_id=2, chain_id=1, name="", symbol="WETH", address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", decimals=18)
    usdc = Tokens(coin_id=3, chain_id=1, name="", symbol="USDC", address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", decimals=18)
    usdt = Tokens(coin_id=4, chain_id=1, name="", symbol="USDT", address="0xdac17f958d2ee523a2206206994597c13d831ec7", decimals=18)

    tokens = [wbtc, weth, usdc, usdt]
    pool0 = "0x" + ethash.keccak(
            eth.encode(
                ["address", "address", "uint24", "int24", "address"],
                [wbtc.address, weth.address, 10000, 200, ZERO_ADDRESS]
                )
    ).hex()
    pool1 = "0x" + ethash.keccak(
            eth.encode(
                ["address", "address", "uint24", "int24", "address"],
                [wbtc.address, usdc.address, 3000, 60, ZERO_ADDRESS]
                )
    ).hex()
    pool2 = "0x" + ethash.keccak(
            eth.encode(
                ["address", "address", "uint24", "int24", "address"],
                [weth.address, usdt.address, 500, 10, ZERO_ADDRESS]
                )
    ).hex() 
    return_map = {
            pool0: 10000,
            pool1: 1000,
            pool2: 10, 
    }
    
    factory = make_mock_factory_v4(return_map)
    multicall = make_mock_multicall()

    adapter = UniswapV4Adapter(
            factory_contract=factory,
            multicall_contract=multicall,
            tokens=tokens,
            chain_id=1,
            dex_id=1,
    )
    
    pools = adapter.fetch_pools()

    assert len(pools) == 3
    assert {pool.pool_address for pool in pools} == {pool for pool in return_map.keys()}
