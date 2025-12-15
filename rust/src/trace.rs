use anyhow::Result;
use alloy::providers::{Provider, ProviderBuilder, WsConnect};

async fn pool_finder() -> Result<()> {
    let wss_url: String = std::env::var("WSS_URL").unwrap();
    let ws = WsConnect::new(wss_url);
    let provider = ProviderBuilder::new().connect_ws(ws).await?;
        
    Ok(())
}
