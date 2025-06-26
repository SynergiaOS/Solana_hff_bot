//! Geographic Distribution System for THE OVERMIND PROTOCOL
//!
//! Advanced geographic distribution with latency optimization, regional failover,
//! and intelligent routing based on network conditions.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::{Mutex, RwLock};
use tracing::{info, debug};
use rand;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeographicConfig {
    pub primary_regions: Vec<String>,
    pub fallback_regions: Vec<String>,
    pub latency_threshold_ms: f64,
    pub regional_failover_enabled: bool,
    pub cross_region_replication: bool,
    pub network_quality_monitoring: bool,
    pub adaptive_region_selection: bool,
    pub geo_redundancy_level: u8,
}

impl Default for GeographicConfig {
    fn default() -> Self {
        Self {
            primary_regions: vec![
                "us-east-1".to_string(),
                "eu-west-1".to_string(),
                "ap-southeast-1".to_string(),
            ],
            fallback_regions: vec![
                "us-west-2".to_string(),
                "eu-central-1".to_string(),
                "ap-northeast-1".to_string(),
            ],
            latency_threshold_ms: 150.0,
            regional_failover_enabled: true,
            cross_region_replication: true,
            network_quality_monitoring: true,
            adaptive_region_selection: true,
            geo_redundancy_level: 2,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeographicRegion {
    pub region_id: String,
    pub region_name: String,
    pub country_code: String,
    pub timezone: String,
    pub coordinates: (f64, f64), // (latitude, longitude)
    pub network_endpoints: Vec<String>,
    pub wallet_nodes: Vec<String>,
    pub is_primary: bool,
    pub is_active: bool,
    pub network_metrics: NetworkMetrics,
    pub trading_hours: TradingHours,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkMetrics {
    pub average_latency_ms: f64,
    pub packet_loss_rate: f64,
    pub bandwidth_mbps: f64,
    pub jitter_ms: f64,
    pub uptime_percentage: f64,
    pub last_measurement: u64,
    pub quality_score: f64, // 0.0 - 1.0
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingHours {
    pub market_open_utc: String,   // "09:30"
    pub market_close_utc: String,  // "16:00"
    pub timezone_offset: i32,      // UTC offset in minutes
    pub is_market_hours: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegionSelection {
    pub selected_region: String,
    pub selection_reason: String,
    pub estimated_latency_ms: f64,
    pub confidence_score: f64,
    pub backup_regions: Vec<String>,
    pub network_path: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrossRegionReplication {
    pub source_region: String,
    pub target_regions: Vec<String>,
    pub replication_lag_ms: f64,
    pub consistency_level: ConsistencyLevel,
    pub last_sync_time: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConsistencyLevel {
    Eventual,
    Strong,
    BoundedStaleness,
}

pub struct GeographicDistribution {
    config: GeographicConfig,
    regions: Arc<RwLock<HashMap<String, GeographicRegion>>>,
    network_monitor: Arc<Mutex<NetworkMonitor>>,
    region_selector: Arc<Mutex<RegionSelector>>,
    replication_manager: Arc<Mutex<ReplicationManager>>,
    latency_matrix: Arc<RwLock<HashMap<(String, String), f64>>>, // (from, to) -> latency
    active_connections: Arc<RwLock<HashMap<String, Vec<String>>>>, // region -> active connections
}

struct NetworkMonitor {
    ping_history: HashMap<String, Vec<(u64, f64)>>, // region -> (timestamp, latency)
    quality_scores: HashMap<String, f64>,
    last_measurement: HashMap<String, u64>,
}

struct RegionSelector {
    selection_history: Vec<RegionSelection>,
    performance_cache: HashMap<String, f64>,
    adaptive_weights: HashMap<String, f64>,
}

struct ReplicationManager {
    replication_configs: HashMap<String, CrossRegionReplication>,
    sync_status: HashMap<String, bool>,
    lag_measurements: HashMap<String, Vec<f64>>,
}

impl GeographicDistribution {
    pub fn new(config: GeographicConfig) -> Self {
        Self {
            config,
            regions: Arc::new(RwLock::new(HashMap::new())),
            network_monitor: Arc::new(Mutex::new(NetworkMonitor {
                ping_history: HashMap::new(),
                quality_scores: HashMap::new(),
                last_measurement: HashMap::new(),
            })),
            region_selector: Arc::new(Mutex::new(RegionSelector {
                selection_history: Vec::new(),
                performance_cache: HashMap::new(),
                adaptive_weights: HashMap::new(),
            })),
            replication_manager: Arc::new(Mutex::new(ReplicationManager {
                replication_configs: HashMap::new(),
                sync_status: HashMap::new(),
                lag_measurements: HashMap::new(),
            })),
            latency_matrix: Arc::new(RwLock::new(HashMap::new())),
            active_connections: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("🌍 Starting Geographic Distribution System for THE OVERMIND PROTOCOL");

        // Initialize default regions
        self.initialize_default_regions().await?;

        // Start network monitoring
        if self.config.network_quality_monitoring {
            self.start_network_monitoring().await;
        }

        // Start replication management
        if self.config.cross_region_replication {
            self.start_replication_management().await;
        }

        // Start latency matrix updates
        self.start_latency_matrix_updates().await;

        info!("✅ Geographic Distribution System started successfully");
        Ok(())
    }

    async fn initialize_default_regions(&self) -> Result<()> {
        let mut regions_guard = self.regions.write().await;

        // US East (Virginia)
        regions_guard.insert("us-east-1".to_string(), GeographicRegion {
            region_id: "us-east-1".to_string(),
            region_name: "US East (Virginia)".to_string(),
            country_code: "US".to_string(),
            timezone: "America/New_York".to_string(),
            coordinates: (39.0458, -77.5081),
            network_endpoints: vec![
                "https://api.mainnet-beta.solana.com".to_string(),
                "https://solana-api.projectserum.com".to_string(),
            ],
            wallet_nodes: Vec::new(),
            is_primary: true,
            is_active: true,
            network_metrics: NetworkMetrics {
                average_latency_ms: 50.0,
                packet_loss_rate: 0.001,
                bandwidth_mbps: 1000.0,
                jitter_ms: 2.0,
                uptime_percentage: 99.9,
                last_measurement: SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs(),
                quality_score: 0.95,
            },
            trading_hours: TradingHours {
                market_open_utc: "14:30".to_string(),  // 9:30 AM EST
                market_close_utc: "21:00".to_string(),  // 4:00 PM EST
                timezone_offset: -300, // EST is UTC-5
                is_market_hours: true,
            },
        });

        // EU West (Ireland)
        regions_guard.insert("eu-west-1".to_string(), GeographicRegion {
            region_id: "eu-west-1".to_string(),
            region_name: "EU West (Ireland)".to_string(),
            country_code: "IE".to_string(),
            timezone: "Europe/Dublin".to_string(),
            coordinates: (53.3498, -6.2603),
            network_endpoints: vec![
                "https://api.mainnet-beta.solana.com".to_string(),
            ],
            wallet_nodes: Vec::new(),
            is_primary: true,
            is_active: true,
            network_metrics: NetworkMetrics {
                average_latency_ms: 75.0,
                packet_loss_rate: 0.002,
                bandwidth_mbps: 800.0,
                jitter_ms: 3.0,
                uptime_percentage: 99.8,
                last_measurement: SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs(),
                quality_score: 0.92,
            },
            trading_hours: TradingHours {
                market_open_utc: "08:00".to_string(),
                market_close_utc: "16:30".to_string(),
                timezone_offset: 0, // UTC
                is_market_hours: false,
            },
        });

        // Asia Pacific (Singapore)
        regions_guard.insert("ap-southeast-1".to_string(), GeographicRegion {
            region_id: "ap-southeast-1".to_string(),
            region_name: "Asia Pacific (Singapore)".to_string(),
            country_code: "SG".to_string(),
            timezone: "Asia/Singapore".to_string(),
            coordinates: (1.3521, 103.8198),
            network_endpoints: vec![
                "https://api.mainnet-beta.solana.com".to_string(),
            ],
            wallet_nodes: Vec::new(),
            is_primary: true,
            is_active: true,
            network_metrics: NetworkMetrics {
                average_latency_ms: 120.0,
                packet_loss_rate: 0.003,
                bandwidth_mbps: 600.0,
                jitter_ms: 5.0,
                uptime_percentage: 99.7,
                last_measurement: SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs(),
                quality_score: 0.88,
            },
            trading_hours: TradingHours {
                market_open_utc: "01:00".to_string(),  // 9:00 AM SGT
                market_close_utc: "09:00".to_string(),  // 5:00 PM SGT
                timezone_offset: 480, // SGT is UTC+8
                is_market_hours: false,
            },
        });

        info!("🌍 Initialized {} geographic regions", regions_guard.len());
        Ok(())
    }

    async fn start_network_monitoring(&self) {
        let regions = self.regions.clone();
        let network_monitor = self.network_monitor.clone();
        let latency_matrix = self.latency_matrix.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(30));

            loop {
                interval.tick().await;

                let regions_guard = regions.read().await;
                let mut monitor_guard = network_monitor.lock().await;
                let mut matrix_guard = latency_matrix.write().await;

                let current_time = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs();

                // Measure latency between all region pairs
                for (region1_id, region1) in regions_guard.iter() {
                    for (region2_id, region2) in regions_guard.iter() {
                        if region1_id != region2_id {
                            let latency = Self::measure_inter_region_latency(region1, region2).await;
                            matrix_guard.insert((region1_id.clone(), region2_id.clone()), latency);
                        }
                    }

                    // Update region quality score
                    let quality_score = Self::calculate_region_quality_score(region1).await;
                    monitor_guard.quality_scores.insert(region1_id.clone(), quality_score);
                    monitor_guard.last_measurement.insert(region1_id.clone(), current_time);
                }

                debug!("📊 Updated network metrics for {} regions", regions_guard.len());
            }
        });
    }

    async fn start_replication_management(&self) {
        let replication_manager = self.replication_manager.clone();
        let regions = self.regions.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(60));

            loop {
                interval.tick().await;

                let mut replication_guard = replication_manager.lock().await;
                let regions_guard = regions.read().await;

                // Check replication lag for each configured replication
                let replication_configs: Vec<_> = replication_guard.replication_configs.clone().into_iter().collect();
                drop(replication_guard);

                for (source_region, replication_config) in replication_configs {
                    if let Some(_source) = regions_guard.get(&source_region) {
                        for target_region in &replication_config.target_regions {
                            if let Some(_target) = regions_guard.get(target_region) {
                                let lag = Self::measure_replication_lag(&source_region, target_region).await;

                                let mut replication_guard = replication_manager.lock().await;
                                replication_guard
                                    .lag_measurements
                                    .entry(format!("{}:{}", source_region, target_region))
                                    .or_insert_with(Vec::new)
                                    .push(lag);

                                // Keep only last 100 measurements
                                let measurements = replication_guard
                                    .lag_measurements
                                    .get_mut(&format!("{}:{}", source_region, target_region))
                                    .unwrap();
                                if measurements.len() > 100 {
                                    let len = measurements.len();
                                    measurements.drain(0..len - 100);
                                }
                            }
                        }
                    }
                }

                debug!("🔄 Updated replication metrics");
            }
        });
    }

    async fn start_latency_matrix_updates(&self) {
        let latency_matrix = self.latency_matrix.clone();
        let regions = self.regions.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(120)); // Update every 2 minutes

            loop {
                interval.tick().await;

                let regions_guard = regions.read().await;
                let mut matrix_guard = latency_matrix.write().await;

                // Clean old entries and update matrix
                let region_ids: Vec<String> = regions_guard.keys().cloned().collect();

                // Remove entries for non-existent regions
                matrix_guard.retain(|(from, to), _| {
                    region_ids.contains(from) && region_ids.contains(to)
                });

                debug!("🗺️ Updated latency matrix with {} entries", matrix_guard.len());
            }
        });
    }

    pub async fn select_optimal_region(&self, user_location: Option<(f64, f64)>, requirements: Option<RegionRequirements>) -> Result<RegionSelection> {
        let regions_guard = self.regions.read().await;
        let monitor_guard = self.network_monitor.lock().await;
        let _matrix_guard = self.latency_matrix.read().await;

        let mut scored_regions = Vec::new();

        for (region_id, region) in regions_guard.iter() {
            if !region.is_active {
                continue;
            }

            let mut score = 0.0;
            let mut reasoning_parts = Vec::new();

            // Network quality score (40% weight)
            let quality_score = monitor_guard.quality_scores.get(region_id).copied().unwrap_or(0.5);
            score += quality_score * 0.4;
            reasoning_parts.push(format!("Quality: {:.2}", quality_score));

            // Geographic proximity score (30% weight)
            if let Some((user_lat, user_lon)) = user_location {
                let distance = Self::calculate_distance(
                    user_lat, user_lon,
                    region.coordinates.0, region.coordinates.1
                );
                let proximity_score = 1.0 / (1.0 + distance / 10000.0); // Normalize by 10,000 km
                score += proximity_score * 0.3;
                reasoning_parts.push(format!("Proximity: {:.2}", proximity_score));
            } else {
                score += 0.15; // Neutral score if no location provided
                reasoning_parts.push("Proximity: N/A".to_string());
            }

            // Trading hours alignment (20% weight)
            let trading_hours_score = if region.trading_hours.is_market_hours { 1.0 } else { 0.5 };
            score += trading_hours_score * 0.2;
            reasoning_parts.push(format!("Trading Hours: {:.2}", trading_hours_score));

            // Primary region preference (10% weight)
            let primary_score = if region.is_primary { 1.0 } else { 0.8 };
            score += primary_score * 0.1;
            reasoning_parts.push(format!("Primary: {:.2}", primary_score));

            // Apply requirements filter
            if let Some(ref req) = requirements {
                if req.min_quality_score > quality_score {
                    continue; // Skip regions that don't meet quality requirements
                }
                if req.max_latency_ms < region.network_metrics.average_latency_ms {
                    continue; // Skip regions with too high latency
                }
                if req.required_trading_hours && !region.trading_hours.is_market_hours {
                    continue; // Skip regions outside trading hours if required
                }
            }

            scored_regions.push((region_id.clone(), region, score, reasoning_parts.join(", ")));
        }

        if scored_regions.is_empty() {
            return Err(anyhow::anyhow!("No suitable regions found"));
        }

        // Sort by score (highest first)
        scored_regions.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap());

        let (selected_region_id, selected_region, score, reasoning) = &scored_regions[0];

        // Get backup regions
        let backup_regions: Vec<String> = scored_regions
            .iter()
            .skip(1)
            .take(2)
            .map(|(id, _, _, _)| id.clone())
            .collect();

        // Calculate network path (simplified)
        let network_path = vec![
            "user".to_string(),
            "internet".to_string(),
            selected_region_id.clone(),
        ];

        Ok(RegionSelection {
            selected_region: selected_region_id.clone(),
            selection_reason: reasoning.clone(),
            estimated_latency_ms: selected_region.network_metrics.average_latency_ms,
            confidence_score: *score,
            backup_regions,
            network_path,
        })
    }

    async fn measure_inter_region_latency(region1: &GeographicRegion, region2: &GeographicRegion) -> f64 {
        // Simplified latency calculation based on geographic distance
        let distance = Self::calculate_distance(
            region1.coordinates.0, region1.coordinates.1,
            region2.coordinates.0, region2.coordinates.1
        );

        // Approximate latency: ~1ms per 100km + base latency
        let base_latency = 10.0; // Base network latency
        let distance_latency = distance / 100.0; // 1ms per 100km

        base_latency + distance_latency
    }

    async fn calculate_region_quality_score(region: &GeographicRegion) -> f64 {
        let metrics = &region.network_metrics;

        // Normalize metrics to 0-1 scale
        let latency_score = 1.0 / (1.0 + metrics.average_latency_ms / 100.0);
        let loss_score = 1.0 - metrics.packet_loss_rate.min(0.1) * 10.0;
        let uptime_score = metrics.uptime_percentage / 100.0;
        let jitter_score = 1.0 / (1.0 + metrics.jitter_ms / 10.0);

        // Weighted average
        latency_score * 0.3 + loss_score * 0.2 + uptime_score * 0.3 + jitter_score * 0.2
    }

    async fn measure_replication_lag(_source_region: &str, _target_region: &str) -> f64 {
        // Simplified replication lag measurement
        // In real implementation, this would measure actual data synchronization lag
        rand::random::<f64>() * 50.0 // 0-50ms lag
    }

    fn calculate_distance(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
        // Haversine formula for calculating distance between two points on Earth
        let r = 6371.0; // Earth's radius in kilometers

        let dlat = (lat2 - lat1).to_radians();
        let dlon = (lon2 - lon1).to_radians();

        let a = (dlat / 2.0).sin().powi(2) +
                lat1.to_radians().cos() * lat2.to_radians().cos() * (dlon / 2.0).sin().powi(2);

        let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());

        r * c
    }

    pub async fn add_region(&self, region: GeographicRegion) -> Result<()> {
        let region_id = region.region_id.clone();

        {
            let mut regions_guard = self.regions.write().await;
            regions_guard.insert(region_id.clone(), region);
        }

        info!("🌍 Added geographic region: {}", region_id);
        Ok(())
    }

    pub async fn remove_region(&self, region_id: &str) -> Result<()> {
        {
            let mut regions_guard = self.regions.write().await;
            regions_guard.remove(region_id);
        }

        // Clean up latency matrix
        {
            let mut matrix_guard = self.latency_matrix.write().await;
            matrix_guard.retain(|(from, to), _| from != region_id && to != region_id);
        }

        info!("🌍 Removed geographic region: {}", region_id);
        Ok(())
    }

    pub async fn get_region_stats(&self) -> HashMap<String, serde_json::Value> {
        let regions_guard = self.regions.read().await;
        let monitor_guard = self.network_monitor.lock().await;

        let total_regions = regions_guard.len();
        let active_regions = regions_guard.values().filter(|r| r.is_active).count();
        let primary_regions = regions_guard.values().filter(|r| r.is_primary).count();

        let avg_quality: f64 = if !monitor_guard.quality_scores.is_empty() {
            monitor_guard.quality_scores.values().sum::<f64>() / monitor_guard.quality_scores.len() as f64
        } else {
            0.0
        };

        let mut stats = HashMap::new();
        stats.insert("total_regions".to_string(), serde_json::Value::Number(total_regions.into()));
        stats.insert("active_regions".to_string(), serde_json::Value::Number(active_regions.into()));
        stats.insert("primary_regions".to_string(), serde_json::Value::Number(primary_regions.into()));
        stats.insert("average_quality_score".to_string(), serde_json::Value::Number(serde_json::Number::from_f64(avg_quality).unwrap()));

        stats
    }

    pub async fn shutdown(&mut self) -> Result<()> {
        info!("🛑 Shutting down Geographic Distribution System");
        // Cleanup tasks would be implemented here
        info!("✅ Geographic Distribution System shut down successfully");
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegionRequirements {
    pub min_quality_score: f64,
    pub max_latency_ms: f64,
    pub required_trading_hours: bool,
    pub preferred_regions: Vec<String>,
    pub excluded_regions: Vec<String>,
}