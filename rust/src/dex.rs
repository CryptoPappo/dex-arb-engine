use alloy::{
    sol,
    rpc::types::Log,
};
use crate::{
    traits::DexDecoder,
    topics::{
        UNISWAP_V2_SYNC_TOPIC,
        UNISWAP_V3_SWAP_TOPIC
    },
    events::SwapEvent,
};

sol!(
    #[allow(missing_docs)]
    #[derive(Debug)]
    event Sync(uint112 reserve0, uint112 reserve1);
    #[derive(Debug)]
    event Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick);
);

static Q96: f64 = 7922816514264337593543950336.0;

pub struct UniswapV2Decoder {
    pub dex_id: u32,
}

impl DexDecoder for UniswapV2Decoder {
    fn is_relevant_log(&self, log: &Log) -> bool {
        let topic = log.topic0().unwrap();
        topic == UNISWAP_V2_SYNC_TOPIC
    }
    
    fn decode_swap(&self, log: &Log, chain_id: u32) -> Option<SwapEvent> {
        let data = Sync::decode_log_data(log.data())?;
        let reserve0 = data.reserve0 as f64;
        let reserve1 = data.reserve1 as f64;
        let liquidity = (reserve0 * reserve1).sqrt() as u128;
        let price = (reserve1 / reserve0).sqrt(); 
        
        Some(
            SwapEvent {
                chain_id: chain_id,
                dex_id: self.dex_id,
                pool_address: log.inner.address,
                block_number: log.block_number.unwrap(),
                tx_hash: log.transaction_hash.unwrap(),
                timestamp: log.block_timestamp.unwrap(),
                liquidity: liquidity,
                price: price,
            }
        )
    }
}


pub struct UniswapV3Decoder {
    pub dex_id: u32,
}

impl DexDecoder for UniswapV3Decoder {
    fn is_relevant_log(&self, log: &Log) -> bool {
        let topic = log.topic0().unwrap();
        topic == UNISWAP_V3_SWAP_TOPIC
    }
    
    fn decode_swap(&self, log: &Log, chain_id: u32) -> Option<SwapEvent> {
        let data = Swap::decode_log_data(log.data())?;
        let price = (data.sqrtPriceX96 as f64) / Q96; 
        
        Some(
            SwapEvent {
                chain_id: chain_id,
                dex_id: self.dex_id,
                pool_address: log.inner.address,
                block_number: log.block_number.unwrap(),
                tx_hash: log.transaction_hash.unwrap(),
                timestamp: log.block_timestamp.unwrap(),
                liquidity: data.liquidity,
                price: price,
            }
        )
    }
}
