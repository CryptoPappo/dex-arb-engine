use eyre::Result;
use alloy::sol;
use alloy::sol_types::SolEvent;
use alloy::providers::{Provider, ProviderBuilder, WsConnect};
use alloy::rpc::types::Filter;
use futures_util::StreamExt;

use crate::topics::{
    UNISWAP_V2_SYNC_TOPIC,
    UNISWAP_V3_SWAP_TOPIC,
};

sol!(
    #[allow(missing_docs)]
    #[derive(Debug)]
    event Sync(uint112 reserve0, uint112 reserve1);
    #[derive(Debug)]
    event Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick);
);

pub async fn chain_listener() -> Result<()> {
    let rpc_api = std::env::var("RPC_API").unwrap();
    let mut rpc_url = String::from("wss://eth-mainnet.g.alchemy.com/v2/");
    rpc_url = rpc_url + &rpc_api;
    let ws = WsConnect::new(rpc_url);
    let provider = ProviderBuilder::new().connect_ws(ws).await?;

    let topics = vec![
        UNISWAP_V2_SYNC_TOPIC,
        UNISWAP_V3_SWAP_TOPIC,
    ];
    let filter = Filter::new()
        .event_signature(UNISWAP_V2_SYNC_TOPIC);

    let sub = provider.subscribe_logs(&filter).await?;

    let mut stream = sub.into_stream().take(4);
    
    println!("Awaiting logs...");

    let handle = tokio::spawn(async move {
        while let Some(header) = stream.next().await {
            //let data = Swap::decode_log_data(&header.data());            
            println!("Latest logs: {:?}", header);
        }
    });

    handle.await?;
    
    Ok(())
}
