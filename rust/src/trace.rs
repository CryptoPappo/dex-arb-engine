use anyhow::{Result, Ok};
use alloy::{
    eips::BlockNumberOrTag,
    primitives::Address,
    providers::{Provider, ProviderBuilder},
    rpc::types::Filter,
};
use reqwest::Client;
use log::info;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct ApiResponse {
    data: Vec<Item>,
    status: Status,
}

#[derive(Debug, Deserialize)]
struct Item {
    id: u32,
    rank: u32,
    name: String,
    symbol: String,
    slug: String,
    status: u8,
    platform: Option<Platform>,
}

#[derive(Debug, Deserialize)]
struct Platform {
    id: u32,
    name: String,
    symbol: String,
    slug: String,
    token_address: String,
}

#[derive(Debug, Deserialize)]
struct Status {
    timestamp: String,
    error_code: u32,
    elapsed: u32,
    credit_count: u8,
    notice: Option<String>,
}

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

pub async fn get_tokens() -> Result<()> {
    let client = Client::new();
    let url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map";
    let api_key = std::env::var("COINMARKET_API").unwrap();
    let params = [("start",  "1"), ("limit", "10"), ("aux", "platform")];
    
    let response = client.get(url)
        .header("Accepts", "application/json")
        .header("X-CMC_PRO_API_KEY", api_key)
        .query(&params)
        .send()
        .await?;

    println!("Status: {}", response.status());
    //let body = response.text().await?;
    let body = response.json::<ApiResponse>().await?;
    println!("{:#?}", body);

    Ok(())
}
