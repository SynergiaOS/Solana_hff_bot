/*
THE OVERMIND PROTOCOL - Rugpull Scanner
Zero-jedynkowy system dyskwalifikacji tokenów

Centralny system agregujący wszystkie testy rugpull i implementujący
CRITICAL risk flagging z natychmiastową dyskwalifikacją tokenów.
*/

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{Duration, Instant};
use tokio::sync::mpsc;
use tracing::{error, info, warn};

// Import AI connector for Python brain communication
use crate::modules::ai_connector::AIConnector;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RiskLevel {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ScanVerdict {
    Pass,
    ConditionalPass,
    Disqualified,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RugpullScanResult {
    pub token_address: String,
    pub scan_timestamp: String,
    pub overall_risk: RiskLevel,
    pub verdict: ScanVerdict,
    pub recommendation: String,
    pub scan_levels: HashMap<String, serde_json::Value>,
    pub risk_summary: RiskSummary,
    pub critical_failures: Vec<String>,
    pub high_risks: Vec<String>,
    pub warnings: Vec<String>,
    pub scan_duration_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskSummary {
    pub total_scans: u32,
    pub critical_failures: u32,
    pub high_risks: u32,
    pub warnings: u32,
    pub passes: u32,
}

#[derive(Debug, Clone)]
pub struct RugpullScannerConfig {
    pub enable_level1_contract: bool,
    pub enable_level2_social: bool,
    pub enable_level3_rag: bool,
    pub enable_holder_analysis: bool,
    pub critical_failure_threshold: u32, // Max critical failures before disqualification
    pub high_risk_threshold: u32,        // Max high risks before disqualification
    pub scan_timeout_seconds: u64,
    pub ai_brain_timeout_seconds: u64,
}

impl Default for RugpullScannerConfig {
    fn default() -> Self {
        Self {
            enable_level1_contract: true,
            enable_level2_social: true,
            enable_level3_rag: true,
            enable_holder_analysis: true,
            critical_failure_threshold: 0, // Zero tolerance for critical failures
            high_risk_threshold: 2,        // Max 2 high risks
            scan_timeout_seconds: 30,
            ai_brain_timeout_seconds: 10,
        }
    }
}

pub struct RugpullScanner {
    config: RugpullScannerConfig,
    ai_connector: AIConnector,
    scan_results_sender: mpsc::UnboundedSender<RugpullScanResult>,
    metrics: RugpullScannerMetrics,
}

#[derive(Debug, Default)]
pub struct RugpullScannerMetrics {
    pub total_scans: u64,
    pub disqualified_tokens: u64,
    pub passed_tokens: u64,
    pub conditional_passes: u64,
    pub scan_errors: u64,
    pub avg_scan_time_ms: f64,
}

impl RugpullScanner {
    pub fn new(
        config: RugpullScannerConfig,
        ai_connector: AIConnector,
        scan_results_sender: mpsc::UnboundedSender<RugpullScanResult>,
    ) -> Self {
        info!("🛡️ Initializing THE OVERMIND PROTOCOL Rugpull Scanner");
        info!(
            "⚡ Zero-tolerance mode: {} critical failures allowed",
            config.critical_failure_threshold
        );

        Self {
            config,
            ai_connector,
            scan_results_sender,
            metrics: RugpullScannerMetrics::default(),
        }
    }

    /// Perform complete rugpull scan with all enabled levels
    pub async fn perform_complete_scan(
        &mut self,
        token_address: &str,
        developer_address: Option<&str>,
    ) -> Result<RugpullScanResult> {
        let scan_start = Instant::now();
        info!(
            "🔍 Starting complete rugpull scan for token: {}",
            token_address
        );

        let mut scan_result = RugpullScanResult {
            token_address: token_address.to_string(),
            scan_timestamp: chrono::Utc::now().to_rfc3339(),
            overall_risk: RiskLevel::LOW,
            verdict: ScanVerdict::Pass,
            recommendation: "PROCEED".to_string(),
            scan_levels: HashMap::new(),
            risk_summary: RiskSummary {
                total_scans: 0,
                critical_failures: 0,
                high_risks: 0,
                warnings: 0,
                passes: 0,
            },
            critical_failures: Vec::new(),
            high_risks: Vec::new(),
            warnings: Vec::new(),
            scan_duration_ms: 0,
        };

        // Level 1: Contract Analysis (LP, Mint Authority, etc.)
        if self.config.enable_level1_contract {
            match self.perform_level1_contract_scan(token_address).await {
                Ok(level1_result) => {
                    scan_result
                        .scan_levels
                        .insert("level1_contract".to_string(), level1_result.clone());
                    self.aggregate_scan_results(
                        &mut scan_result,
                        &level1_result,
                        "Level 1 Contract",
                    );
                }
                Err(e) => {
                    error!("❌ Level 1 contract scan failed: {}", e);
                    scan_result
                        .critical_failures
                        .push("Level 1 contract scan error".to_string());
                }
            }
        }

        // Early termination check after Level 1
        if self.should_terminate_scan(&scan_result) {
            scan_result.verdict = ScanVerdict::Disqualified;
            scan_result.recommendation = "REJECT_IMMEDIATELY".to_string();
            scan_result.overall_risk = RiskLevel::CRITICAL;

            self.finalize_scan_result(&mut scan_result, scan_start);
            return Ok(scan_result);
        }

        // Level 2: Holder Distribution Analysis
        if self.config.enable_holder_analysis {
            match self.perform_holder_distribution_scan(token_address).await {
                Ok(holder_result) => {
                    scan_result
                        .scan_levels
                        .insert("holder_distribution".to_string(), holder_result.clone());
                    self.aggregate_scan_results(
                        &mut scan_result,
                        &holder_result,
                        "Holder Distribution",
                    );
                }
                Err(e) => {
                    error!("❌ Holder distribution scan failed: {}", e);
                    scan_result
                        .high_risks
                        .push("Holder distribution scan error".to_string());
                }
            }
        }

        // Level 3: Social Analysis
        if self.config.enable_level2_social {
            match self.perform_level2_social_scan(token_address).await {
                Ok(social_result) => {
                    scan_result
                        .scan_levels
                        .insert("level2_social".to_string(), social_result.clone());
                    self.aggregate_scan_results(&mut scan_result, &social_result, "Level 2 Social");
                }
                Err(e) => {
                    error!("❌ Level 2 social scan failed: {}", e);
                    scan_result
                        .high_risks
                        .push("Social analysis scan error".to_string());
                }
            }
        }

        // Level 4: RAG Developer History (if developer address provided)
        if self.config.enable_level3_rag && developer_address.is_some() {
            match self
                .perform_level3_rag_scan(developer_address.unwrap())
                .await
            {
                Ok(rag_result) => {
                    scan_result
                        .scan_levels
                        .insert("level3_rag".to_string(), rag_result.clone());
                    self.aggregate_scan_results(&mut scan_result, &rag_result, "Level 3 RAG");
                }
                Err(e) => {
                    error!("❌ Level 3 RAG scan failed: {}", e);
                    scan_result
                        .high_risks
                        .push("RAG developer history scan error".to_string());
                }
            }
        }

        // Final verdict determination
        self.determine_final_verdict(&mut scan_result);
        self.finalize_scan_result(&mut scan_result, scan_start);

        // Send result to monitoring system
        if let Err(e) = self.scan_results_sender.send(scan_result.clone()) {
            warn!("Failed to send scan result to monitoring: {}", e);
        }

        Ok(scan_result)
    }

    /// Check if scan should be terminated early due to critical failures
    fn should_terminate_scan(&self, scan_result: &RugpullScanResult) -> bool {
        scan_result.risk_summary.critical_failures > self.config.critical_failure_threshold
    }

    /// Aggregate results from individual scan levels
    fn aggregate_scan_results(
        &self,
        main_result: &mut RugpullScanResult,
        level_result: &serde_json::Value,
        level_name: &str,
    ) {
        // Extract risk information from level result
        if let Some(verdict) = level_result.get("verdict").and_then(|v| v.as_str()) {
            match verdict {
                "DISQUALIFIED"
                | "SOCIAL_MANIPULATION_DETECTED"
                | "DEVELOPER_HISTORY_DISQUALIFIED" => {
                    main_result.risk_summary.critical_failures += 1;
                    main_result
                        .critical_failures
                        .push(format!("{}: {}", level_name, verdict));
                }
                "CONDITIONAL_PASS" | "CONDITIONAL_REJECT" => {
                    if let Some(risk) = level_result.get("overall_risk").and_then(|r| r.as_str()) {
                        match risk {
                            "CRITICAL" => {
                                main_result.risk_summary.critical_failures += 1;
                                main_result
                                    .critical_failures
                                    .push(format!("{}: Critical risk", level_name));
                            }
                            "HIGH" => {
                                main_result.risk_summary.high_risks += 1;
                                main_result
                                    .high_risks
                                    .push(format!("{}: High risk", level_name));
                            }
                            _ => {
                                main_result.risk_summary.warnings += 1;
                                main_result
                                    .warnings
                                    .push(format!("{}: Warning", level_name));
                            }
                        }
                    }
                }
                "PASS" => {
                    main_result.risk_summary.passes += 1;
                }
                _ => {
                    main_result.risk_summary.warnings += 1;
                    main_result
                        .warnings
                        .push(format!("{}: Unknown verdict", level_name));
                }
            }
        }

        main_result.risk_summary.total_scans += 1;
    }

    /// Determine final verdict based on aggregated results
    fn determine_final_verdict(&self, scan_result: &mut RugpullScanResult) {
        let critical_count = scan_result.risk_summary.critical_failures;
        let high_count = scan_result.risk_summary.high_risks;

        if critical_count > self.config.critical_failure_threshold {
            scan_result.verdict = ScanVerdict::Disqualified;
            scan_result.overall_risk = RiskLevel::CRITICAL;
            scan_result.recommendation = "REJECT_IMMEDIATELY".to_string();

            error!(
                "🚨 TOKEN DISQUALIFIED: {} critical failures detected for {}",
                critical_count, scan_result.token_address
            );
        } else if high_count > self.config.high_risk_threshold {
            scan_result.verdict = ScanVerdict::Disqualified;
            scan_result.overall_risk = RiskLevel::HIGH;
            scan_result.recommendation = "REJECT_DUE_TO_HIGH_RISKS".to_string();

            warn!(
                "⚠️ TOKEN DISQUALIFIED: {} high risks detected for {}",
                high_count, scan_result.token_address
            );
        } else if high_count > 0 || critical_count > 0 {
            scan_result.verdict = ScanVerdict::ConditionalPass;
            scan_result.overall_risk = RiskLevel::HIGH;
            scan_result.recommendation = "PROCEED_WITH_EXTREME_CAUTION".to_string();

            warn!(
                "⚠️ CONDITIONAL PASS: Risks detected for {}",
                scan_result.token_address
            );
        } else if scan_result.risk_summary.warnings > 0 {
            scan_result.verdict = ScanVerdict::ConditionalPass;
            scan_result.overall_risk = RiskLevel::MEDIUM;
            scan_result.recommendation = "PROCEED_WITH_CAUTION".to_string();

            info!(
                "✅ CONDITIONAL PASS: Minor warnings for {}",
                scan_result.token_address
            );
        } else {
            scan_result.verdict = ScanVerdict::Pass;
            scan_result.overall_risk = RiskLevel::LOW;
            scan_result.recommendation = "PROCEED".to_string();

            info!(
                "✅ FULL PASS: No risks detected for {}",
                scan_result.token_address
            );
        }
    }

    /// Finalize scan result with timing and metrics
    fn finalize_scan_result(&mut self, scan_result: &mut RugpullScanResult, scan_start: Instant) {
        let scan_duration = scan_start.elapsed();
        scan_result.scan_duration_ms = scan_duration.as_millis() as u64;

        // Update metrics
        self.metrics.total_scans += 1;
        match scan_result.verdict {
            ScanVerdict::Disqualified => self.metrics.disqualified_tokens += 1,
            ScanVerdict::Pass => self.metrics.passed_tokens += 1,
            ScanVerdict::ConditionalPass => self.metrics.conditional_passes += 1,
            ScanVerdict::Error => self.metrics.scan_errors += 1,
        }

        // Update average scan time
        let total_time = self.metrics.avg_scan_time_ms * (self.metrics.total_scans - 1) as f64;
        self.metrics.avg_scan_time_ms =
            (total_time + scan_duration.as_millis() as f64) / self.metrics.total_scans as f64;

        info!(
            "📊 Rugpull scan completed for {} in {}ms - Verdict: {:?}",
            scan_result.token_address, scan_result.scan_duration_ms, scan_result.verdict
        );
    }

    // AI Brain Communication Functions

    /// Perform Level 1 contract analysis via AI Brain
    async fn perform_level1_contract_scan(&self, token_address: &str) -> Result<serde_json::Value> {
        info!("🔍 Performing Level 1 contract scan for: {}", token_address);

        let request = serde_json::json!({
            "action": "rugpull_level1_scan",
            "token_address": token_address,
            "scan_type": "contract_analysis"
        });

        let timeout = Duration::from_secs(self.config.ai_brain_timeout_seconds);

        match tokio::time::timeout(timeout, self.ai_connector.send_request(request)).await {
            Ok(Ok(response)) => {
                info!("✅ Level 1 contract scan completed for: {}", token_address);
                Ok(response)
            }
            Ok(Err(e)) => {
                error!("❌ Level 1 contract scan failed: {}", e);
                Err(anyhow::anyhow!("AI Brain communication error: {}", e))
            }
            Err(_) => {
                error!("⏰ Level 1 contract scan timed out for: {}", token_address);
                Err(anyhow::anyhow!("Level 1 scan timeout"))
            }
        }
    }

    /// Perform holder distribution analysis via AI Brain
    async fn perform_holder_distribution_scan(
        &self,
        token_address: &str,
    ) -> Result<serde_json::Value> {
        info!(
            "📊 Performing holder distribution scan for: {}",
            token_address
        );

        let request = serde_json::json!({
            "action": "holder_distribution_scan",
            "token_address": token_address,
            "scan_type": "holder_analysis"
        });

        let timeout = Duration::from_secs(self.config.ai_brain_timeout_seconds);

        match tokio::time::timeout(timeout, self.ai_connector.send_request(request)).await {
            Ok(Ok(response)) => {
                info!(
                    "✅ Holder distribution scan completed for: {}",
                    token_address
                );
                Ok(response)
            }
            Ok(Err(e)) => {
                error!("❌ Holder distribution scan failed: {}", e);
                Err(anyhow::anyhow!("AI Brain communication error: {}", e))
            }
            Err(_) => {
                error!(
                    "⏰ Holder distribution scan timed out for: {}",
                    token_address
                );
                Err(anyhow::anyhow!("Holder distribution scan timeout"))
            }
        }
    }

    /// Perform Level 2 social analysis via AI Brain
    async fn perform_level2_social_scan(&self, token_address: &str) -> Result<serde_json::Value> {
        info!("🕵️ Performing Level 2 social scan for: {}", token_address);

        let request = serde_json::json!({
            "action": "social_rugpull_scan",
            "token_address": token_address,
            "scan_type": "social_analysis"
        });

        let timeout = Duration::from_secs(self.config.ai_brain_timeout_seconds);

        match tokio::time::timeout(timeout, self.ai_connector.send_request(request)).await {
            Ok(Ok(response)) => {
                info!("✅ Level 2 social scan completed for: {}", token_address);
                Ok(response)
            }
            Ok(Err(e)) => {
                error!("❌ Level 2 social scan failed: {}", e);
                Err(anyhow::anyhow!("AI Brain communication error: {}", e))
            }
            Err(_) => {
                error!("⏰ Level 2 social scan timed out for: {}", token_address);
                Err(anyhow::anyhow!("Level 2 social scan timeout"))
            }
        }
    }

    /// Perform Level 3 RAG developer history analysis via AI Brain
    async fn perform_level3_rag_scan(&self, developer_address: &str) -> Result<serde_json::Value> {
        info!(
            "🧠 Performing Level 3 RAG scan for developer: {}",
            developer_address
        );

        let request = serde_json::json!({
            "action": "developer_rag_scan",
            "developer_address": developer_address,
            "scan_type": "rag_analysis"
        });

        let timeout = Duration::from_secs(self.config.ai_brain_timeout_seconds);

        match tokio::time::timeout(timeout, self.ai_connector.send_request(request)).await {
            Ok(Ok(response)) => {
                info!(
                    "✅ Level 3 RAG scan completed for developer: {}",
                    developer_address
                );
                Ok(response)
            }
            Ok(Err(e)) => {
                error!("❌ Level 3 RAG scan failed: {}", e);
                Err(anyhow::anyhow!("AI Brain communication error: {}", e))
            }
            Err(_) => {
                error!(
                    "⏰ Level 3 RAG scan timed out for developer: {}",
                    developer_address
                );
                Err(anyhow::anyhow!("Level 3 RAG scan timeout"))
            }
        }
    }

    /// Get scanner metrics for monitoring
    pub fn get_metrics(&self) -> &RugpullScannerMetrics {
        &self.metrics
    }

    /// Reset scanner metrics
    pub fn reset_metrics(&mut self) {
        self.metrics = RugpullScannerMetrics::default();
        info!("📊 Rugpull scanner metrics reset");
    }

    /// Quick scan for high-priority tokens (reduced checks)
    pub async fn perform_quick_scan(&mut self, token_address: &str) -> Result<RugpullScanResult> {
        let scan_start = Instant::now();
        info!(
            "⚡ Starting quick rugpull scan for token: {}",
            token_address
        );

        let mut scan_result = RugpullScanResult {
            token_address: token_address.to_string(),
            scan_timestamp: chrono::Utc::now().to_rfc3339(),
            overall_risk: RiskLevel::LOW,
            verdict: ScanVerdict::Pass,
            recommendation: "PROCEED".to_string(),
            scan_levels: HashMap::new(),
            risk_summary: RiskSummary {
                total_scans: 0,
                critical_failures: 0,
                high_risks: 0,
                warnings: 0,
                passes: 0,
            },
            critical_failures: Vec::new(),
            high_risks: Vec::new(),
            warnings: Vec::new(),
            scan_duration_ms: 0,
        };

        // Quick scan: Only Level 1 contract analysis (most critical)
        if let Ok(level1_result) = self.perform_level1_contract_scan(token_address).await {
            scan_result
                .scan_levels
                .insert("level1_contract".to_string(), level1_result.clone());
            self.aggregate_scan_results(&mut scan_result, &level1_result, "Level 1 Contract");
        } else {
            scan_result
                .critical_failures
                .push("Level 1 contract scan failed".to_string());
            scan_result.risk_summary.critical_failures += 1;
        }

        self.determine_final_verdict(&mut scan_result);
        self.finalize_scan_result(&mut scan_result, scan_start);

        info!(
            "⚡ Quick scan completed for {} in {}ms",
            token_address, scan_result.scan_duration_ms
        );
        Ok(scan_result)
    }
}
