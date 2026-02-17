use async_trait::async_trait;
use alloy::rpc::types::Log;
use eyre::Result;

#[async_trait]
pub trait DexDecoder: Send + Sync {
    fn is_relevant_log(&self, log: &Log) -> bool;
    fn decode_swap(&self, log: &Log) -> Result<()>;
}
