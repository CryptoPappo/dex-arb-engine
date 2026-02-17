use serde::{Serialize};

#[derive(Serialize)]
pub struct SwapEvent {
    pub chain_id: u32,
    pub dex_id: u32,
    pub pool_address: String,
    pub block_number: u64,
    pub tx_hash: String,
    pub timestamp: u64,
    pub liquidity: u128,
    pub price: f64,
}
