use solana_client::{
    rpc_client::RpcClient,
    rpc_config::RpcAccountInfoConfig,
    rpc_response::Response,
};
use tokio::time::{interval, Duration};

pub async fn start_market_data_collection(
    config: MarketDataConfig,
    market_tx: UnboundedSender<MarketEvent>,
    dragonfly_client: redis::Client,
) -> Result<()> {
    let mut interval = interval(Duration::from_millis(config.polling_interval_ms));
    
    loop {
        interval.tick().await;
        
        // Collect market data from Solana
        let market_data = collect_market_data(&config).await?;
        
        // Send to internal channel
        if let Err(e) = market_tx.send(market_data.clone()) {
            error!("Failed to send market data internally: {}", e);
        }
        
        // Send to DragonflyDB for Python Brain
        let mut conn = dragonfly_client.get_async_connection().await?;
        let json_data = serde_json::to_string(&market_data)?;
        redis::cmd("LPUSH")
            .arg("overmind:market_events")
            .arg(json_data)
            .execute_async(&mut conn)
            .await?;
    }
}