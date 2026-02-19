use eyre::Result;
use log::info;
use alloy::sol;
use alloy::sol_types::SolEvent;
use alloy::providers::{Provider, ProviderBuilder, WsConnect};
use alloy::rpc::types::Filter;
use futures_util::StreamExt;

use crate::{
    config::{
        ChainConfig,
        DexConfig,
    },
    topics::{
        UNISWAP_V2_SYNC_TOPIC,
        UNISWAP_V3_SWAP_TOPIC,
    },
    dex::{
        DexDecoder,
        UniswapV2Decoder,
        UniswapV3Decoder,
    },
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
        dexs: Vec<DexConfig>
) -> Result<()> {
    let ws = WsConnect::new(chain.rpc_url);
    let provider = ProviderBuilder::new().connect_ws(ws).await?;
   
    let decoders: Vec<Box<dyn DexDecoder>> = vec![
        Box::new(UniswapV2Decoder {dex_id: 1}),
        Box::new(UniswapV3Decoder {dex_id: 2}),
    ];

    let topics = vec![
        UNISWAP_V2_SYNC_TOPIC,
        UNISWAP_V3_SWAP_TOPIC,
    ];
    let filter = Filter::new()
        .event_signature(topics);

    let sub = provider.subscribe_logs(&filter).await?;

    let mut stream = sub.into_stream().take(4);
    
    info!("Awaiting logs...");

    let handle = tokio::spawn(async move {
        while let Some(log) = stream.next().await {
            for decoder in &decoders {
                if decoder.is_relevant_log(&log) {
                    if let Some(event) = decoder.decode_swap(&log, 1) {
                        info!("Latest logs: {:?}", event);
                    }
                }
            }
        }
    });

    handle.await?;
    
    Ok(())
}
