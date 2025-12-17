use anyhow::Result;
use alloy::{
    eips::BlockNumberOrTag,
    primitives::Address,
    providers::{Provider, ProviderBuilder},
    rpc::types::Filter,
};
use log::info;

pub async fn pool_finder(
    latest_block: u64,
    factory_address: String,
) -> Result<()> {
    let rpc_url = std::env::var("HTTP_URL").unwrap().parse()?;
    let provider = ProviderBuilder::new().connect_http(rpc_url);
    
    let block = BlockNumberOrTag::Number(latest_block);
    let filter = Filter::new() 
        .event("PoolCreated(address,address,uint24,int24,address)")
        .address(factory_address.parse::<Address>().unwrap())
        .from_block(block);
    
    let logs = provider.get_logs(&filter).await?;
    
    for log in logs {
        info!("{log:?}");
    }

    Ok(())
}
