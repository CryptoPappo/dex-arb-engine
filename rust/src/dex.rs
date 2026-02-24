use std::marker::Sync as sync;
use std::sync::Arc;
use async_trait::async_trait;
use log::warn;
use alloy::{
    sol,
    rpc::types::Log,
    sol_types::SolEvent,
    primitives::B256,
};
use crate::{
    config::DexConfig,
    topics::{
        UNISWAP_V2_SYNC_TOPIC,
        UNISWAP_V3_SWAP_TOPIC
    },
    proto::SwapEvent,
};

sol!(
    #[allow(missing_docs)]
    #[derive(Debug)]
    event Sync(uint112 reserve0, uint112 reserve1);
    #[derive(Debug)]
    event Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick);
);

static Q96: f64 = 79228162514264337593543950336.0;

pub fn build_decoders(
    dexs: &Vec<DexConfig>,
) -> Vec<Arc<dyn DexDecoder + Send + sync>> {
    let mut decoders: Vec<Arc<dyn DexDecoder + Send + sync>> = Vec::new();
    for dex in dexs {
        let decoder = match (dex.name.as_str(), dex.dex_type.as_str()) {
            ("Uniswap", "V2") => Some(
                Arc::new(UniswapV2Decoder {dex_id: dex.dex_id})
                    as Arc<dyn DexDecoder + Send + sync>
            ),
            ("Uniswap", "V3") => Some(
                Arc::new(UniswapV3Decoder {dex_id: dex.dex_id})
                    as Arc<dyn DexDecoder + Send + sync>
            ),
            _ => {
                warn!(
                    "Decoder for {} {} not available",
                    dex.name, dex.dex_type
                );
                None
            }
        };
        
        if let Some(decoder) = decoder {
            decoders.push(decoder);
        }
    }
    
    decoders
}

#[async_trait]
pub trait DexDecoder: Send + sync {
    fn is_relevant_log(&self, log: &Log) -> bool;
    fn decode_swap(&self, log: &Log, chain_id: u32) -> Option<SwapEvent>;
    fn get_topic(&self) -> B256;
}

pub struct UniswapV2Decoder {
    pub dex_id: u32,
}

impl DexDecoder for UniswapV2Decoder {
    fn is_relevant_log(&self, log: &Log) -> bool {
        let topic = log.topic0().unwrap();
        *topic == UNISWAP_V2_SYNC_TOPIC
    }
    
    fn decode_swap(&self, log: &Log, chain_id: u32) -> Option<SwapEvent> {
        let data = Sync::decode_log_data(log.data()).unwrap();
        let reserve0 = f64::from(data.reserve0);
        let reserve1 = f64::from(data.reserve1);
        let liquidity = (reserve0 * reserve1).sqrt() as u128;
        let price = (reserve1 / reserve0).sqrt(); 
        
        Some(
            SwapEvent {
                chain_id: chain_id,
                dex_id: self.dex_id,
                pool_address: log.inner.address.to_string(),
                price: price.to_string(),
                liquidity: liquidity.to_string(),
                block_number: log.block_number.unwrap(),
                tx_hash: log.transaction_hash.unwrap().to_string(),
                timestamp: log.block_timestamp.unwrap(),
            }
        )
    }

    fn get_topic(&self) -> B256 {
        UNISWAP_V2_SYNC_TOPIC
    }
}


pub struct UniswapV3Decoder {
    pub dex_id: u32,
}

impl DexDecoder for UniswapV3Decoder {
    fn is_relevant_log(&self, log: &Log) -> bool {
        let topic = log.topic0().unwrap();
        *topic == UNISWAP_V3_SWAP_TOPIC
    }
    
    fn decode_swap(&self, log: &Log, chain_id: u32) -> Option<SwapEvent> {
        let data = Swap::decode_log_data(log.data()).unwrap();
        let price = f64::from(data.sqrtPriceX96) / Q96;
        
        Some(
            SwapEvent {
                chain_id: chain_id,
                dex_id: self.dex_id,
                pool_address: log.inner.address.to_string(),
                price: price.to_string(),
                liquidity: liquidity.to_string(),
                block_number: log.block_number.unwrap(),
                tx_hash: log.transaction_hash.unwrap().to_string(),
                timestamp: log.block_timestamp.unwrap(),
            }
        )
    }

    fn get_topic(&self) -> B256 {
        UNISWAP_V3_SWAP_TOPIC
    }
}
