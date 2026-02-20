use std::sync::Arc;
use eyre::Result;
use fern::colors::{Color, ColoredLevelConfig};
use log::{LevelFilter, info};
use rust_listener::{
    evm_listener::chain_listener,
    config::{
        load_chains,
        load_dexs,
        map_chain_dex
    },
};


pub fn setup_logger() -> Result<()> {
    let colors = ColoredLevelConfig {
        trace: Color::Cyan,
        debug: Color::Magenta,
        info: Color::Green,
        warn: Color::Red,
        error: Color::BrightRed,
        ..ColoredLevelConfig::new()
    };

    fern::Dispatch::new()
        .format(move |out, message, record| {
            out.finish(format_args!(
                "{}[{}] {}",
                chrono::Local::now().format("[%Y-%m-%d  %H:%M:%S]"),
                colors.color(record.level()),
                message
            ))
        })
        .chain(std::io::stdout())
        .chain(fern::log_file("pools.log")?)
        .level(LevelFilter::Error)
        .level_for("rust_listener", LevelFilter::Info)
        .apply()?;

    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    dotenv::dotenv().ok();
    setup_logger()?;
   
    info!("Loading chains...");
    let chains = load_chains()?;
    
    info!("Loading dexs...");
    let dexs = load_dexs()?;
    let dexs_by_chain = Arc::new(map_chain_dex(dexs));

    let mut handles = vec![];

    info!("Initializing chains listeners");
    for chain in chains {
        let dex = Arc::clone(
            dexs_by_chain.get(&chain.chain_id).unwrap()
        );

        handles.push(tokio::spawn(async move {
            chain_listener(chain, dex).await
        }));
    }
    
    for handle in handles {
        handle.await??;
    }

    Ok(())
}
