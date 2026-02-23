use std::sync::Arc;
use eyre::Result;
use log::info;
use alloy::sol;
use alloy::providers::{Provider, ProviderBuilder, WsConnect};
use alloy::rpc::types::Filter;
use futures_util::StreamExt;
use rdkafka::producer::FutureProducer; 

use crate::{
    config::{
        ChainConfig,
        DexConfig,
    },
    dex::build_decoders,
    kafka::send_swap,
};

sol!(
    #[allow(missing_docs)]
    #[derive(Debug)]
    event Sync(uint112 reserve0, uint112 reserve1);
    #[derive(Debug)]
    event Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick);
);

pub async fn chain_listener(
        chain: ChainConfig,
        dexs: Arc<Vec<DexConfig>>,
        producer: FutureProducer,
) -> Result<()> {
    let ws = WsConnect::new(chain.rpc_url);
    let provider = ProviderBuilder::new().connect_ws(ws).await?;
  
    let decoders = build_decoders(&dexs); 

    let mut topics = Vec::new();
    for decoder in &decoders {
        topics.push(decoder.get_topic());
    }

    let filter = Filter::new()
        .event_signature(topics);

    let sub = provider.subscribe_logs(&filter).await?;

    let mut stream = sub.into_stream().take(4);
    
    info!("Awaiting logs...");

    let handle = tokio::spawn(async move {
        while let Some(log) = stream.next().await {
            for decoder in &decoders {
                if decoder.is_relevant_log(&log) {
                    if let Some(event) = decoder.decode_swap(&log, chain.chain_id) {
                        send_swap(&producer, &event).await; 
                    }
                }
            }
        }
    });

    handle.await?;
    
    Ok(())
}
