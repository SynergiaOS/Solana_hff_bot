// THE OVERMIND PROTOCOL - AI-Enhanced High-Frequency Trading System for Solana
// Main entry point for the monolithic trading application with TensorZero optimization

mod config;
mod modules;
mod monitoring;

use anyhow::Result;
use tokio::sync::mpsc;
use tracing::{error, info, warn};
// use uuid::Uuid; // Commented out to avoid unused import warning

use config::Config;
use modules::{
    data_ingestor::{DataIngestor, MarketData},
    executor::{ExecutionResult, Executor},
    hft_engine::HFTConfig,
    persistence::{PersistenceManager, PersistenceMessage},
    risk::{ApprovedSignal, RiskManager, RiskParameters},
    strategy::{StrategyEngine, TradingSignal},
};
use monitoring::{create_monitoring_router, MonitoringState};

#[tokio::main(worker_threads = 6)]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    info!("🧠 Starting THE OVERMIND PROTOCOL - AI-Enhanced Solana HFT Trading System");

    // Load configuration
    let config = Config::from_env()?;

    // Safety check for trading mode
    match config.trading.mode {
        config::TradingMode::Paper => {
            info!("📝 Running in PAPER TRADING mode - No real transactions");
        }
        config::TradingMode::Live => {
            warn!("🔴 LIVE TRADING MODE ENABLED - Real money at risk!");
            warn!("🔴 Ensure all risk parameters are properly configured");
        }
    }

    // THE OVERMIND PROTOCOL status
    if config.is_overmind_enabled() {
        info!("🧠 THE OVERMIND PROTOCOL: ENABLED");
        info!("🤖 TensorZero Gateway: {}", config.overmind.tensorzero_gateway_url);
        info!("⚡ Jito Endpoint: {}", config.overmind.jito_endpoint);
        info!("⏱️ Max Latency Target: {}ms", config.overmind.max_execution_latency_ms);
        info!("🎯 AI Confidence Threshold: {:.1}%", config.overmind.ai_confidence_threshold * 100.0);
        warn!("🧠 AI-ENHANCED EXECUTION ACTIVE - TensorZero optimization enabled");
    } else {
        info!("🤖 THE OVERMIND PROTOCOL: DISABLED (Standard mode)");
    }

    // Create communication channels between modules
    let (market_data_tx, market_data_rx) = mpsc::unbounded_channel::<MarketData>();
    let (signal_tx, signal_rx) = mpsc::unbounded_channel::<TradingSignal>();
    let (execution_tx, execution_rx) = mpsc::unbounded_channel::<ApprovedSignal>();
    let (execution_result_tx, execution_result_rx) = mpsc::unbounded_channel::<ExecutionResult>();
    let (_persistence_tx, persistence_rx) = mpsc::unbounded_channel::<PersistenceMessage>();

    info!("📡 Communication channels established");

    // Initialize monitoring
    let monitoring_state = MonitoringState::new();
    let monitoring_router = create_monitoring_router(monitoring_state.clone());

    // Start monitoring server
    let monitoring_port = config.server.port;
    let _monitoring_server = tokio::spawn(async move {
        let addr = format!("0.0.0.0:{}", monitoring_port);
        let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
        info!("🔍 Monitoring server listening on http://{}", addr);
        info!("📊 Health: http://{}/health", addr);
        info!("📈 Metrics: http://{}/metrics", addr);
        info!("🎯 Prometheus: http://{}/metrics/prometheus", addr);
        axum::serve(listener, monitoring_router).await.unwrap();
    });

    // Initialize all modules
    let mut data_ingestor = DataIngestor::new(
        market_data_tx,
        config.api.helius_api_key.clone(),
        config.api.quicknode_api_key.clone(),
    );

    let mut strategy_engine = StrategyEngine::new(market_data_rx, signal_tx);

    let risk_params = RiskParameters {
        max_position_size: config.trading.max_position_size,
        max_daily_loss: config.trading.max_daily_loss,
        min_confidence_threshold: 0.6, // Default confidence threshold
    };

    let mut risk_manager = RiskManager::new(signal_rx, execution_tx, risk_params);

    // Initialize Executor with optional HFT Engine
    let mut executor = if config.is_overmind_enabled() {
        info!("🧠 Initializing THE OVERMIND PROTOCOL Executor with AI enhancement...");

        let hft_config = HFTConfig {
            tensorzero_gateway_url: config.overmind.tensorzero_gateway_url.clone(),
            jito_endpoint: config.overmind.jito_endpoint.clone(),
            max_execution_latency_ms: config.overmind.max_execution_latency_ms,
            max_bundle_size: 5,
            retry_attempts: 3,
            ai_confidence_threshold: config.overmind.ai_confidence_threshold,
        };

        // Create HFT-enabled executor
        match Executor::new_with_hft(
            execution_rx,
            execution_result_tx,
            config.trading.mode.clone(),
            config.solana.rpc_url.clone(),
            config.solana.wallet_private_key.clone(),
            hft_config,
        ) {
            Ok(executor) => {
                info!("✅ THE OVERMIND PROTOCOL Executor initialized successfully");
                executor
            }
            Err(e) => {
                error!("❌ Failed to initialize HFT Engine: {}", e);
                error!("🛑 Cannot start THE OVERMIND PROTOCOL without HFT Engine");
                return Err(e);
            }
        }
    } else {
        info!("⚡ Initializing standard Executor...");
        Executor::new(
            execution_rx,
            execution_result_tx,
            config.trading.mode.clone(),
            config.solana.rpc_url.clone(),
            config.solana.wallet_private_key.clone(),
        )
    };

    let mut persistence_manager = PersistenceManager::new(
        persistence_rx,
        execution_result_rx,
        config.database.url.clone(),
    );

    info!("🔧 All modules initialized");

    // Start all modules concurrently
    info!("▶️  Starting all modules...");

    let data_ingestor_task = tokio::spawn(async move {
        if let Err(e) = data_ingestor.start().await {
            error!("DataIngestor failed: {}", e);
        }
    });

    let strategy_engine_task = tokio::spawn(async move {
        if let Err(e) = strategy_engine.start().await {
            error!("StrategyEngine failed: {}", e);
        }
    });

    let risk_manager_task = tokio::spawn(async move {
        if let Err(e) = risk_manager.start().await {
            error!("RiskManager failed: {}", e);
        }
    });

    let executor_task = tokio::spawn(async move {
        if let Err(e) = executor.start().await {
            error!("Executor failed: {}", e);
        }
    });

    let persistence_task = tokio::spawn(async move {
        if let Err(e) = persistence_manager.start().await {
            error!("PersistenceManager failed: {}", e);
        }
    });

    info!("✅ All modules started successfully");

    if config.is_overmind_enabled() {
        info!("🧠 THE OVERMIND PROTOCOL is now operational and monitoring markets");
        info!("🤖 AI-Enhanced execution with TensorZero optimization: ACTIVE");
        info!("⚡ Jito Bundle execution for MEV protection: ACTIVE");
    } else {
        info!("🎯 SNIPERCOR is now operational and monitoring markets");
    }

    info!("📊 Trading Mode: {}", config.trading_mode_str());
    info!("🤖 AI Mode: {}", config.overmind_mode_str());
    info!(
        "💰 Max Position Size: ${}",
        config.trading.max_position_size
    );
    info!("🛡️ Max Daily Loss: ${}", config.trading.max_daily_loss);

    // Wait for all tasks to complete (or fail)
    tokio::try_join!(
        data_ingestor_task,
        strategy_engine_task,
        risk_manager_task,
        executor_task,
        persistence_task,
    )?;

    if config.is_overmind_enabled() {
        info!("🛑 THE OVERMIND PROTOCOL shutdown complete");
    } else {
        info!("🛑 SNIPERCOR shutdown complete");
    }
    Ok(())
}
