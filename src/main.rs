// THE OVERMIND PROTOCOL - AI-Enhanced High-Frequency Trading System for Solana
// Main entry point - SIMPLIFIED VERSION for AI Connector testing

mod config;
mod modules;
mod monitoring;

use anyhow::Result;
use tracing::info;

use modules::ai_connector;

#[tokio::main(worker_threads = 1)]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    info!("🧠 THE OVERMIND PROTOCOL - ROZDZIAŁ 1: Budowa Układu Nerwowego");
    info!("🎯 Starting simple AI Connector for Python-Rust communication testing");

    // Start the simple command listener
    info!("🚀 Starting AI Connector command listener...");
    ai_connector::listen_for_commands().await?;

    Ok(())
}
