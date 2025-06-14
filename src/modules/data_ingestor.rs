// Data Ingestor Module
// Handles real-time market data ingestion from Helius and QuickNode

use anyhow::Result;
use serde::{Deserialize, Serialize};
use tokio::sync::mpsc;
use tracing::{info, error, debug};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub symbol: String,
    pub price: f64,
    pub volume: f64,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub source: DataSource,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DataSource {
    Helius,
    QuickNode,
}

pub struct DataIngestor {
    market_data_sender: mpsc::UnboundedSender<MarketData>,
    helius_api_key: String,
    quicknode_api_key: String,
    is_running: bool,
}

impl DataIngestor {
    pub fn new(
        market_data_sender: mpsc::UnboundedSender<MarketData>,
        helius_api_key: String,
        quicknode_api_key: String,
    ) -> Self {
        Self {
            market_data_sender,
            helius_api_key,
            quicknode_api_key,
            is_running: false,
        }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("🔄 DataIngestor starting...");
        self.is_running = true;

        // TODO: Implement actual WebSocket connections to Helius and QuickNode
        // For now, simulate market data
        self.simulate_market_data().await?;

        Ok(())
    }

    pub async fn stop(&mut self) {
        info!("🛑 DataIngestor stopping...");
        self.is_running = false;
    }

    async fn simulate_market_data(&self) -> Result<()> {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_millis(100));
        
        while self.is_running {
            interval.tick().await;
            
            let market_data = MarketData {
                symbol: "SOL/USDC".to_string(),
                price: 100.0 + (0.5 - 0.5) * 10.0, // Simplified for now
                volume: 1000.0, // Fixed value for now
                timestamp: chrono::Utc::now(),
                source: DataSource::Helius,
            };

            if let Err(e) = self.market_data_sender.send(market_data) {
                error!("Failed to send market data: {}", e);
                break;
            }
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_data_ingestor_creation() {
        let (tx, _rx) = mpsc::unbounded_channel();
        let ingestor = DataIngestor::new(
            tx,
            "test_helius_key".to_string(),
            "test_quicknode_key".to_string(),
        );
        
        assert!(!ingestor.is_running);
    }
}
