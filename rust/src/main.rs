use anyhow::{Ok, Result};
use fern::colors::{Color, ColoredLevelConfig};
use log::LevelFilter;
use rust::trace::pool_finder;

pub fn setup_logger() -> Result<()> {
    let log_path = std::path::Path::new("root/dex-arb-engine/rust/logs/pools.log");
    let file = std::fs::OpenOptions::new()
        .write(true)
        .append(true)
        .create(true)
        .open(log_path)?;

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
        .chain(file)
        .level(LevelFilter::Error)
        .level_for("rust", LevelFilter::Info)
        .apply()?;

    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    setup_logger()?;
    
    let uniswap_v3_factory = String::from("0x1F98431c8aD98523631AE4a59f267346ea31F984");
    pool_finder(411676800, uniswap_v3_factory).await?;

    Ok(())
}
