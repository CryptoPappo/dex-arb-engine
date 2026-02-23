use eyre::Result;
use log::{info, error};
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::config::ClientConfig;

use crate::events::SwapEvent;

pub fn create_producer() -> FutureProducer {
    ClientConfig::new()
        .set("bootstrap.servers", "localhost:9092")
        .set("message.timeout.ms", "5000")
        .create()
        .expect("Producer creation failed")
}

pub async fn send_swap(
    producer: &FutureProducer,
    event: &SwapEvent,
) -> {
    let payload = serde_json::to_vec(event)?;

    let produce_future = producer.send(
        FutureRecord::to("dex.swaps.raw")
            .key(event.pool_address.as_str())
            .payload(&payload),
        std::time::Duration::from_secs(0),
    );
    match produce_future.await {
        Ok(delivery) => info!("Sent: {:?}", delivery),
        Err((e, _)) => error!("Kafka send failed: {:?}", e),
    }
}
