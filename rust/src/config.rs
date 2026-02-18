use eyre::Result;
use serde::Deserialize;
use std::{fs, env};

#[derive(Deserialize)]
pub struct ChainConfig {
   pub chain_id: u32,
   pub name: String,
   pub native_token: String,
   pub evm: bool,
   pub rpc_url: String,
}

#[derive(Deserialize)]
pub struct DexConfig {
    pub dex_id: u32,
    pub chain_id: u32,
    pub name: String,
    pub dex_type: String,
    pub factory_address: String,
    pub quoter_address: String,
}

pub fn load_chains() -> Result<Vec<ChainConfig>> {
    let raw = fs::read_to_string("configs/chains.json")?;
    let mut chains: Vec<ChainConfig> = serde_json::from_str(&raw)?;

    for chain in &mut chains {
        if chain.rpc_url.starts_with("${") {
            let key = chain.rpc_url.trim_matches(&['$', '{', '}'][..]);
            chain.rpc_url = env::var(key)?;
        }
    }

    Ok(chains)
}

pub fn load_dexs() -> Result<Vec<DexConfig>> {
    let raw = fs::read_to_string("configs/dexs.json")?;
    let mut dexs: Vec<DexConfig> = serde_json::from_str(&raw)?;

    Ok(dexs)
}
