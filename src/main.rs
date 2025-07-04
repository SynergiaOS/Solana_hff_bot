// THE OVERMIND PROTOCOL - AI-Enhanced High-Frequency Trading System for Solana
// Main entry point - SIMPLIFIED HTTP SERVER VERSION

#![allow(clippy::all)]
#![allow(unused_variables)]
#![allow(unused_mut)]
#![allow(dead_code)]

mod config;
mod modules;
mod monitoring;

use anyhow::Result;
use axum::{extract::State, http::StatusCode, response::Json, routing::get, Router};
use serde_json::{json, Value};
use std::sync::Arc;
use tracing::{error, info};

use config::Config;
use modules::ai_connector;

#[derive(Clone)]
struct AppState {
    config: Arc<Config>,
}

#[tokio::main(worker_threads = 6)]
async fn main() -> Result<()> {
    // Initialize comprehensive logging
    let log_level = std::env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string());

    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .with_target(true)
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true)
        .with_level(true)
        .json()
        .init();

    info!("🚀 THE OVERMIND PROTOCOL - Starting with comprehensive logging");
    info!("📊 Log Level: {}", log_level);
    info!("🎯 5-Layer Autonomous AI Trading System for Solana");

    // Load configuration
    let config = Arc::new(Config::from_env()?);
    info!("✅ Configuration loaded");
    info!("📊 Trading Mode: {}", config.trading_mode_str());
    info!(
        "🧠 AI Enabled: {}",
        std::env::var("OVERMIND_AI_MODE").unwrap_or_else(|_| "disabled".to_string())
    );
    info!("🌐 RPC URL: {}", config.solana.rpc_url);
    info!("🏦 Multi-Wallet: {}", config.solana.multi_wallet_enabled);
    info!("🔧 Server Port: {}", config.server.port);
    info!("🧠 OVERMIND Enabled: {}", config.overmind.enabled);

    // Create application state
    let app_state = AppState {
        config: config.clone(),
    };

    // Start AI Connector in background
    info!("🧠 Starting AI Connector for command processing...");
    let ai_config = config.clone();
    tokio::spawn(async move {
        if let Err(e) = ai_connector::listen_for_commands().await {
            error!("AI Connector error: {}", e);
        }
    });

    // Create HTTP server
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/metrics", get(metrics))
        .route("/status", get(status))
        .with_state(app_state);

    let port = config.server.port;
    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", port)).await?;

    info!("🌐 THE OVERMIND PROTOCOL server starting on port {}", port);
    info!("📊 Health check: http://localhost:{}/health", port);
    info!("📈 Metrics: http://localhost:{}/metrics", port);
    info!("📋 Status: http://localhost:{}/status", port);
    info!("🧠 AI Connector listening for commands on overmind:commands");

    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check(State(state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let health_status = json!({
        "status": "healthy",
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "version": "1.0.0",
        "system": "THE OVERMIND PROTOCOL",
        "components": {
            "config": "loaded",
            "server": "running"
        },
        "trading_mode": state.config.trading_mode_str(),
        "environment": "devnet",
        "overmind_enabled": state.config.overmind.enabled
    });

    Ok(Json(health_status))
}

async fn metrics(State(_state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let metrics = json!({
        "uptime_seconds": 0, // TODO: Calculate actual uptime
        "total_trades": 0,
        "successful_trades": 0,
        "failed_trades": 0,
        "current_positions": 0,
        "daily_pnl": 0.0,
        "ai_decisions": 0,
        "system_latency_ms": 0.0
    });

    Ok(Json(metrics))
}

async fn status(State(state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let status = json!({
        "system": "THE OVERMIND PROTOCOL",
        "mode": state.config.trading_mode_str(),
        "environment": "devnet",
        "overmind_enabled": state.config.overmind.enabled,
        "ai_mode": if state.config.overmind.enabled { "enabled" } else { "disabled" },
        "server_port": state.config.server.port,
        "timestamp": chrono::Utc::now().to_rfc3339()
    });

    Ok(Json(status))
}
