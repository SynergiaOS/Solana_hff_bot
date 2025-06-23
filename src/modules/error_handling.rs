//! Error Handling Module
//! 
//! Provides comprehensive error handling, recovery mechanisms,
//! and detailed error reporting for THE OVERMIND PROTOCOL.

use anyhow::Result;
use thiserror::Error;
use tracing::{error, warn, info, debug};
use std::time::{Duration, Instant};
use tokio::time::sleep;

/// Custom error types for THE OVERMIND PROTOCOL
#[derive(Error, Debug)]
pub enum OvermindError {
    #[error("Network error: {message}")]
    Network { message: String, retryable: bool },
    
    #[error("RPC error: {message}")]
    Rpc { message: String, endpoint: String },
    
    #[error("Transaction error: {message}")]
    Transaction { message: String, signature: Option<String> },
    
    #[error("TensorZero optimization error: {message}")]
    TensorZero { message: String },
    
    #[error("Jito bundle error: {message}")]
    Jito { message: String, bundle_id: Option<String> },
    
    #[error("DEX integration error: {message}")]
    Dex { message: String, dex_type: String },
    
    #[error("Configuration error: {message}")]
    Configuration { message: String },
    
    #[error("Wallet error: {message}")]
    Wallet { message: String },
    
    #[error("Rate limit exceeded: {message}")]
    RateLimit { message: String, retry_after: Option<Duration> },
    
    #[error("Insufficient funds: {message}")]
    InsufficientFunds { message: String, required: u64, available: u64 },
    
    #[error("Market data error: {message}")]
    MarketData { message: String },
    
    #[error("Critical system error: {message}")]
    Critical { message: String },
}

/// Error recovery strategy
#[derive(Debug, Clone)]
pub enum RecoveryStrategy {
    /// Retry with exponential backoff
    Retry { max_attempts: u32, base_delay: Duration },
    /// Switch to fallback service
    Fallback { fallback_service: String },
    /// Circuit breaker - stop operations temporarily
    CircuitBreaker { cooldown: Duration },
    /// Fail fast - don't retry
    FailFast,
    /// Emergency stop - halt all operations
    EmergencyStop,
}

/// Error context for detailed reporting
#[derive(Debug, Clone)]
pub struct ErrorContext {
    pub operation: String,
    pub component: String,
    pub timestamp: Instant,
    pub additional_data: std::collections::HashMap<String, String>,
}

/// Error handler for THE OVERMIND PROTOCOL
pub struct ErrorHandler {
    /// Circuit breaker states
    circuit_breakers: std::collections::HashMap<String, CircuitBreakerState>,
    /// Error statistics
    error_stats: ErrorStatistics,
}

/// Circuit breaker state
#[derive(Debug, Clone)]
struct CircuitBreakerState {
    is_open: bool,
    failure_count: u32,
    last_failure: Option<Instant>,
    cooldown_duration: Duration,
}

/// Error statistics
#[derive(Debug, Default)]
struct ErrorStatistics {
    total_errors: u64,
    network_errors: u64,
    rpc_errors: u64,
    transaction_errors: u64,
    critical_errors: u64,
}

impl ErrorHandler {
    /// Create a new error handler
    pub fn new() -> Self {
        Self {
            circuit_breakers: std::collections::HashMap::new(),
            error_stats: ErrorStatistics::default(),
        }
    }

    /// Handle an error with appropriate recovery strategy
    pub async fn handle_error(&mut self, error: &OvermindError, context: ErrorContext) -> RecoveryStrategy {
        // Update error statistics
        self.update_error_stats(error);
        
        // Log the error with context
        self.log_error(error, &context);
        
        // Determine recovery strategy
        let strategy = self.determine_recovery_strategy(error, &context);
        
        // Execute recovery strategy
        self.execute_recovery_strategy(&strategy, &context).await;
        
        strategy
    }

    /// Execute retry with exponential backoff
    pub async fn retry_with_backoff<F, T, E>(
        &self,
        operation: F,
        max_attempts: u32,
        base_delay: Duration,
        operation_name: &str,
    ) -> Result<T, E>
    where
        F: Fn() -> Result<T, E>,
        E: std::fmt::Display,
    {
        let mut attempt = 1;
        
        loop {
            match operation() {
                Ok(result) => {
                    if attempt > 1 {
                        info!("✅ {} succeeded after {} attempts", operation_name, attempt);
                    }
                    return Ok(result);
                }
                Err(e) => {
                    if attempt >= max_attempts {
                        error!("❌ {} failed after {} attempts: {}", operation_name, attempt, e);
                        return Err(e);
                    }
                    
                    let delay = base_delay * 2_u32.pow(attempt - 1);
                    warn!("⚠️ {} attempt {}/{} failed: {}. Retrying in {:?}", 
                          operation_name, attempt, max_attempts, e, delay);
                    
                    sleep(delay).await;
                    attempt += 1;
                }
            }
        }
    }

    /// Check if circuit breaker is open for a service
    pub fn is_circuit_breaker_open(&self, service: &str) -> bool {
        if let Some(state) = self.circuit_breakers.get(service) {
            if state.is_open {
                // Check if cooldown period has passed
                if let Some(last_failure) = state.last_failure {
                    if last_failure.elapsed() > state.cooldown_duration {
                        return false; // Cooldown passed, allow retry
                    }
                }
                return true;
            }
        }
        false
    }

    /// Trip circuit breaker for a service
    pub fn trip_circuit_breaker(&mut self, service: &str, cooldown: Duration) {
        let state = CircuitBreakerState {
            is_open: true,
            failure_count: self.circuit_breakers
                .get(service)
                .map(|s| s.failure_count + 1)
                .unwrap_or(1),
            last_failure: Some(Instant::now()),
            cooldown_duration: cooldown,
        };
        
        self.circuit_breakers.insert(service.to_string(), state);
        warn!("🔴 Circuit breaker tripped for {}: cooldown {:?}", service, cooldown);
    }

    /// Reset circuit breaker for a service
    pub fn reset_circuit_breaker(&mut self, service: &str) {
        if let Some(state) = self.circuit_breakers.get_mut(service) {
            state.is_open = false;
            state.failure_count = 0;
            state.last_failure = None;
            info!("🟢 Circuit breaker reset for {}", service);
        }
    }

    /// Get error statistics
    #[allow(private_interfaces)]
    pub fn get_error_stats(&self) -> &ErrorStatistics {
        &self.error_stats
    }

    /// Update error statistics
    fn update_error_stats(&mut self, error: &OvermindError) {
        self.error_stats.total_errors += 1;
        
        match error {
            OvermindError::Network { .. } => self.error_stats.network_errors += 1,
            OvermindError::Rpc { .. } => self.error_stats.rpc_errors += 1,
            OvermindError::Transaction { .. } => self.error_stats.transaction_errors += 1,
            OvermindError::Critical { .. } => self.error_stats.critical_errors += 1,
            _ => {}
        }
    }

    /// Log error with appropriate level and context
    fn log_error(&self, error: &OvermindError, context: &ErrorContext) {
        let error_msg = format!("Error in {}.{}: {}", 
                               context.component, context.operation, error);
        
        match error {
            OvermindError::Critical { .. } => {
                error!("🚨 CRITICAL: {}", error_msg);
            }
            OvermindError::Network { retryable: true, .. } |
            OvermindError::Rpc { .. } |
            OvermindError::RateLimit { .. } => {
                warn!("⚠️ RETRYABLE: {}", error_msg);
            }
            _ => {
                error!("❌ ERROR: {}", error_msg);
            }
        }
        
        // Log additional context
        if !context.additional_data.is_empty() {
            debug!("Error context: {:?}", context.additional_data);
        }
    }

    /// Determine appropriate recovery strategy
    fn determine_recovery_strategy(&self, error: &OvermindError, _context: &ErrorContext) -> RecoveryStrategy {
        match error {
            OvermindError::Network { retryable: true, .. } => {
                RecoveryStrategy::Retry {
                    max_attempts: 3,
                    base_delay: Duration::from_millis(500),
                }
            }
            OvermindError::Rpc { .. } => {
                RecoveryStrategy::Fallback {
                    fallback_service: "backup_rpc".to_string(),
                }
            }
            OvermindError::RateLimit { retry_after, .. } => {
                RecoveryStrategy::Retry {
                    max_attempts: 2,
                    base_delay: retry_after.unwrap_or(Duration::from_secs(1)),
                }
            }
            OvermindError::TensorZero { .. } => {
                RecoveryStrategy::Fallback {
                    fallback_service: "default_optimization".to_string(),
                }
            }
            OvermindError::Jito { .. } => {
                RecoveryStrategy::Fallback {
                    fallback_service: "standard_rpc".to_string(),
                }
            }
            OvermindError::Critical { .. } => {
                RecoveryStrategy::EmergencyStop
            }
            OvermindError::InsufficientFunds { .. } => {
                RecoveryStrategy::FailFast
            }
            _ => {
                RecoveryStrategy::Retry {
                    max_attempts: 2,
                    base_delay: Duration::from_millis(1000),
                }
            }
        }
    }

    /// Execute recovery strategy
    async fn execute_recovery_strategy(&mut self, strategy: &RecoveryStrategy, context: &ErrorContext) {
        match strategy {
            RecoveryStrategy::CircuitBreaker { cooldown } => {
                self.trip_circuit_breaker(&context.component, *cooldown);
            }
            RecoveryStrategy::EmergencyStop => {
                error!("🚨 EMERGENCY STOP triggered in {}.{}", 
                       context.component, context.operation);
                // In production, this would trigger system-wide shutdown
            }
            RecoveryStrategy::Fallback { fallback_service } => {
                info!("🔄 Switching to fallback service: {}", fallback_service);
            }
            _ => {
                // Other strategies are handled by the caller
            }
        }
    }
}

impl Default for ErrorHandler {
    fn default() -> Self {
        Self::new()
    }
}

/// Helper macro for creating error context
#[macro_export]
macro_rules! error_context {
    ($component:expr, $operation:expr) => {
        ErrorContext {
            component: $component.to_string(),
            operation: $operation.to_string(),
            timestamp: std::time::Instant::now(),
            additional_data: std::collections::HashMap::new(),
        }
    };
    ($component:expr, $operation:expr, $($key:expr => $value:expr),*) => {
        {
            let mut context = ErrorContext {
                component: $component.to_string(),
                operation: $operation.to_string(),
                timestamp: std::time::Instant::now(),
                additional_data: std::collections::HashMap::new(),
            };
            $(
                context.additional_data.insert($key.to_string(), $value.to_string());
            )*
            context
        }
    };
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_error_handler_creation() {
        let handler = ErrorHandler::new();
        assert_eq!(handler.error_stats.total_errors, 0);
    }

    #[tokio::test]
    async fn test_circuit_breaker() {
        let mut handler = ErrorHandler::new();
        let service = "test_service";
        
        assert!(!handler.is_circuit_breaker_open(service));
        
        handler.trip_circuit_breaker(service, Duration::from_millis(100));
        assert!(handler.is_circuit_breaker_open(service));
        
        // Wait for cooldown
        tokio::time::sleep(Duration::from_millis(150)).await;
        assert!(!handler.is_circuit_breaker_open(service));
    }

    #[test]
    fn test_error_context_macro() {
        let context = error_context!("test_component", "test_operation");
        assert_eq!(context.component, "test_component");
        assert_eq!(context.operation, "test_operation");
        
        let context_with_data = error_context!(
            "test_component", 
            "test_operation",
            "key1" => "value1",
            "key2" => "value2"
        );
        assert_eq!(context_with_data.additional_data.len(), 2);
    }
}
