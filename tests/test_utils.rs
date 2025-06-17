// THE OVERMIND PROTOCOL - Test Utilities and Helpers
// Comprehensive testing infrastructure for all components

// Note: In integration tests, we need to reference the crate differently
// For now, we'll create mock structures for testing
// use snipercor::{...};
use std::time::{Duration, Instant};
use tokio::sync::mpsc;
use uuid::Uuid;

/// Test configuration builder for THE OVERMIND PROTOCOL
pub struct TestConfigBuilder {
    config: Config,
}

impl TestConfigBuilder {
    pub fn new() -> Self {
        let mut config = Config::default();
        
        // Set safe test defaults
        config.trading.mode = TradingMode::Paper;
        config.trading.max_position_size = 100.0;
        config.trading.max_daily_loss = 50.0;
        config.overmind.enabled = true;
        config.overmind.tensorzero_gateway_url = "http://localhost:3001".to_string();
        config.overmind.jito_endpoint = "http://localhost:3002".to_string();
        config.overmind.max_execution_latency_ms = 25;
        config.overmind.ai_confidence_threshold = 0.7;
        
        Self { config }
    }

    pub fn with_overmind_enabled(mut self, enabled: bool) -> Self {
        self.config.overmind.enabled = enabled;
        self
    }

    pub fn with_trading_mode(mut self, mode: TradingMode) -> Self {
        self.config.trading.mode = mode;
        self
    }

    pub fn with_tensorzero_url(mut self, url: String) -> Self {
        self.config.overmind.tensorzero_gateway_url = url;
        self
    }

    pub fn with_jito_endpoint(mut self, endpoint: String) -> Self {
        self.config.overmind.jito_endpoint = endpoint;
        self
    }

    pub fn with_max_latency(mut self, latency_ms: u64) -> Self {
        self.config.overmind.max_execution_latency_ms = latency_ms;
        self
    }

    pub fn with_ai_confidence_threshold(mut self, threshold: f64) -> Self {
        self.config.overmind.ai_confidence_threshold = threshold;
        self
    }

    pub fn build(self) -> Config {
        self.config
    }
}

/// HFT Config builder for testing
pub struct TestHFTConfigBuilder {
    config: HFTConfig,
}

impl TestHFTConfigBuilder {
    pub fn new() -> Self {
        Self {
            config: HFTConfig {
                tensorzero_gateway_url: "http://localhost:3001".to_string(),
                jito_endpoint: "http://localhost:3002".to_string(),
                max_execution_latency_ms: 25,
                max_bundle_size: 5,
                retry_attempts: 3,
                ai_confidence_threshold: 0.7,
            },
        }
    }

    pub fn with_tensorzero_url(mut self, url: String) -> Self {
        self.config.tensorzero_gateway_url = url;
        self
    }

    pub fn with_jito_endpoint(mut self, endpoint: String) -> Self {
        self.config.jito_endpoint = endpoint;
        self
    }

    pub fn with_max_latency(mut self, latency_ms: u64) -> Self {
        self.config.max_execution_latency_ms = latency_ms;
        self
    }

    pub fn with_ai_confidence_threshold(mut self, threshold: f64) -> Self {
        self.config.ai_confidence_threshold = threshold;
        self
    }

    pub fn build(self) -> HFTConfig {
        self.config
    }
}

/// Trading signal generator for testing
pub struct TestSignalGenerator;

impl TestSignalGenerator {
    /// Generate a test trading signal
    pub fn create_signal(
        strategy: StrategyType,
        action: TradingAction,
        confidence: f64,
    ) -> TradingSignal {
        TradingSignal {
            signal_id: Uuid::new_v4().to_string(),
            strategy_type: strategy,
            action,
            symbol: "SOL/USDC".to_string(),
            quantity: 100.0,
            target_price: 50.0,
            confidence,
            timestamp: chrono::Utc::now(),
            metadata: std::collections::HashMap::new(),
        }
    }

    /// Generate high confidence signal
    pub fn high_confidence_signal() -> TradingSignal {
        Self::create_signal(StrategyType::SoulMeteor, TradingAction::Buy, 0.95)
    }

    /// Generate low confidence signal
    pub fn low_confidence_signal() -> TradingSignal {
        Self::create_signal(StrategyType::SoulMeteor, TradingAction::Buy, 0.3)
    }

    /// Generate medium confidence signal
    pub fn medium_confidence_signal() -> TradingSignal {
        Self::create_signal(StrategyType::SoulMeteor, TradingAction::Buy, 0.7)
    }

    /// Generate approved signal from trading signal
    pub fn create_approved_signal(signal: TradingSignal, approved_quantity: f64) -> ApprovedSignal {
        ApprovedSignal {
            original_signal: signal,
            approved_quantity,
            risk_score: 0.5,
            approval_timestamp: chrono::Utc::now(),
        }
    }
}

/// Performance measurement utilities
pub struct PerformanceMeasurer {
    start_time: Instant,
    measurements: Vec<Duration>,
}

impl PerformanceMeasurer {
    pub fn new() -> Self {
        Self {
            start_time: Instant::now(),
            measurements: Vec::new(),
        }
    }

    pub fn start_measurement(&mut self) {
        self.start_time = Instant::now();
    }

    pub fn end_measurement(&mut self) -> Duration {
        let duration = self.start_time.elapsed();
        self.measurements.push(duration);
        duration
    }

    pub fn average_duration(&self) -> Duration {
        if self.measurements.is_empty() {
            return Duration::from_millis(0);
        }
        
        let total_nanos: u64 = self.measurements.iter().map(|d| d.as_nanos() as u64).sum();
        Duration::from_nanos(total_nanos / self.measurements.len() as u64)
    }

    pub fn max_duration(&self) -> Duration {
        self.measurements.iter().max().copied().unwrap_or(Duration::from_millis(0))
    }

    pub fn min_duration(&self) -> Duration {
        self.measurements.iter().min().copied().unwrap_or(Duration::from_millis(0))
    }

    pub fn percentile(&self, percentile: f64) -> Duration {
        if self.measurements.is_empty() {
            return Duration::from_millis(0);
        }
        
        let mut sorted = self.measurements.clone();
        sorted.sort();
        
        let index = ((sorted.len() as f64 - 1.0) * percentile / 100.0) as usize;
        sorted[index]
    }
}

/// Test environment setup
pub struct TestEnvironment {
    pub tensorzero_port: u16,
    pub jito_port: u16,
}

impl TestEnvironment {
    pub fn new() -> Self {
        Self {
            tensorzero_port: 3001,
            jito_port: 3002,
        }
    }

    pub async fn setup(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // Start mock servers
        self.start_mock_servers().await?;
        
        // Wait for servers to be ready
        tokio::time::sleep(Duration::from_millis(100)).await;
        
        Ok(())
    }

    async fn start_mock_servers(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // Start TensorZero mock server
        let tensorzero_config = crate::mock_tensorzero_server::MockServerConfig::default();
        let tensorzero_server = crate::mock_tensorzero_server::MockTensorZeroServer::new(
            self.tensorzero_port,
            tensorzero_config,
        );
        
        tokio::spawn(async move {
            if let Err(e) = tensorzero_server.start().await {
                eprintln!("TensorZero mock server error: {}", e);
            }
        });

        // Start Jito mock server
        let jito_config = crate::mock_jito_server::JitoServerConfig::default();
        let jito_server = crate::mock_jito_server::MockJitoServer::new(
            self.jito_port,
            jito_config,
        );
        
        tokio::spawn(async move {
            if let Err(e) = jito_server.start().await {
                eprintln!("Jito mock server error: {}", e);
            }
        });

        Ok(())
    }

    pub async fn health_check(&self) -> bool {
        let client = reqwest::Client::new();
        
        // Check TensorZero
        let tensorzero_health = client
            .get(&format!("http://localhost:{}/health", self.tensorzero_port))
            .send()
            .await
            .map(|r| r.status().is_success())
            .unwrap_or(false);
        
        // Check Jito
        let jito_health = client
            .get(&format!("http://localhost:{}/health", self.jito_port))
            .send()
            .await
            .map(|r| r.status().is_success())
            .unwrap_or(false);
        
        tensorzero_health && jito_health
    }
}

/// Assertion helpers for testing
pub struct TestAssertions;

impl TestAssertions {
    /// Assert latency is within acceptable range
    pub fn assert_latency_acceptable(duration: Duration, max_ms: u64) {
        assert!(
            duration.as_millis() <= max_ms as u128,
            "Latency {}ms exceeds maximum {}ms",
            duration.as_millis(),
            max_ms
        );
    }

    /// Assert AI confidence is within valid range
    pub fn assert_confidence_valid(confidence: f64) {
        assert!(
            confidence >= 0.0 && confidence <= 1.0,
            "AI confidence {} is not in valid range [0.0, 1.0]",
            confidence
        );
    }

    /// Assert trading signal is valid
    pub fn assert_signal_valid(signal: &TradingSignal) {
        assert!(!signal.signal_id.is_empty(), "Signal ID cannot be empty");
        assert!(signal.quantity > 0.0, "Quantity must be positive");
        assert!(signal.target_price > 0.0, "Target price must be positive");
        Self::assert_confidence_valid(signal.confidence);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_builder() {
        let config = TestConfigBuilder::new()
            .with_overmind_enabled(true)
            .with_trading_mode(TradingMode::Paper)
            .with_max_latency(50)
            .build();
        
        assert!(config.overmind.enabled);
        assert_eq!(config.overmind.max_execution_latency_ms, 50);
    }

    #[test]
    fn test_signal_generator() {
        let signal = TestSignalGenerator::high_confidence_signal();
        TestAssertions::assert_signal_valid(&signal);
        assert!(signal.confidence >= 0.9);
    }

    #[test]
    fn test_performance_measurer() {
        let mut measurer = PerformanceMeasurer::new();
        
        measurer.start_measurement();
        std::thread::sleep(Duration::from_millis(10));
        let duration = measurer.end_measurement();
        
        assert!(duration.as_millis() >= 10);
    }
}
