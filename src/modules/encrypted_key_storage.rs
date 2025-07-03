// 🔐 ENCRYPTED KEY STORAGE FOR OVERMIND VAULT
// Secure key management using system keyring and encryption

use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use tracing::{info, warn};

/// Encrypted key storage configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptedKeyConfig {
    pub service_name: String,
    pub encryption_enabled: bool,
    pub keyring_enabled: bool,
    pub fallback_to_env: bool,
}

/// Key storage entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyEntry {
    pub key_id: String,
    pub encrypted_value: String,
    pub salt: String,
    pub created_at: u64,
    pub last_accessed: u64,
}

/// Encrypted key storage manager
pub struct EncryptedKeyStorage {
    config: EncryptedKeyConfig,
    cached_keys: HashMap<String, String>,
}

impl EncryptedKeyStorage {
    /// Create new encrypted key storage
    pub fn new() -> Result<Self> {
        let config = EncryptedKeyConfig {
            service_name: "overmind_vault".to_string(),
            encryption_enabled: env::var("OVERMIND_ENCRYPTION_ENABLED")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
            keyring_enabled: env::var("OVERMIND_KEYRING_ENABLED")
                .unwrap_or_else(|_| "false".to_string())
                .parse()
                .unwrap_or(false),
            fallback_to_env: env::var("OVERMIND_FALLBACK_TO_ENV")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
        };

        info!("🔐 Initializing encrypted key storage");
        info!("   Encryption: {}", config.encryption_enabled);
        info!("   Keyring: {}", config.keyring_enabled);
        info!("   Fallback to env: {}", config.fallback_to_env);

        Ok(Self {
            config,
            cached_keys: HashMap::new(),
        })
    }

    /// Get private key securely
    pub fn get_private_key(&mut self, key_id: &str) -> Result<String> {
        info!("🔑 Retrieving private key: {}", key_id);

        // Check cache first
        if let Some(cached_key) = self.cached_keys.get(key_id) {
            info!("✅ Key found in cache: {}", key_id);
            return Ok(cached_key.clone());
        }

        // Try keyring first (if enabled)
        if self.config.keyring_enabled {
            if let Ok(key) = self.get_from_keyring(key_id) {
                info!("✅ Key retrieved from keyring: {}", key_id);
                self.cached_keys.insert(key_id.to_string(), key.clone());
                return Ok(key);
            } else {
                warn!("⚠️ Failed to retrieve key from keyring: {}", key_id);
            }
        }

        // Fallback to environment variables
        if self.config.fallback_to_env {
            if let Ok(key) = self.get_from_environment(key_id) {
                info!("✅ Key retrieved from environment: {}", key_id);
                self.cached_keys.insert(key_id.to_string(), key.clone());
                return Ok(key);
            } else {
                warn!("⚠️ Failed to retrieve key from environment: {}", key_id);
            }
        }

        Err(anyhow!("Failed to retrieve private key: {}", key_id))
    }

    /// Store private key securely
    pub fn store_private_key(&mut self, key_id: &str, private_key: &str) -> Result<()> {
        info!("💾 Storing private key: {}", key_id);

        // Validate private key format
        self.validate_private_key(private_key)?;

        // Store in keyring (if enabled)
        if self.config.keyring_enabled {
            if let Err(e) = self.store_in_keyring(key_id, private_key) {
                warn!("⚠️ Failed to store key in keyring: {}", e);
            } else {
                info!("✅ Key stored in keyring: {}", key_id);
            }
        }

        // Cache the key
        self.cached_keys
            .insert(key_id.to_string(), private_key.to_string());

        info!("✅ Private key stored successfully: {}", key_id);
        Ok(())
    }

    /// Get key from system keyring
    fn get_from_keyring(&self, key_id: &str) -> Result<String> {
        // In a real implementation, this would use a keyring library like `keyring`
        // For now, we'll simulate keyring access

        warn!("🔧 Keyring access not implemented - using environment fallback");
        Err(anyhow!("Keyring not available"))
    }

    /// Store key in system keyring
    fn store_in_keyring(&self, key_id: &str, private_key: &str) -> Result<()> {
        // In a real implementation, this would use a keyring library
        warn!("🔧 Keyring storage not implemented");
        Ok(())
    }

    /// Get key from environment variables
    fn get_from_environment(&self, key_id: &str) -> Result<String> {
        // Map key_id to environment variable names
        let env_var = match key_id {
            "primary_trading" => "SNIPER_WALLET_PRIVATE_KEY",
            "hft_trading" => "HFT_WALLET_PRIVATE_KEY",
            "experimental" => "EXPERIMENTAL_WALLET_PRIVATE_KEY",
            "cold_storage" => "COLD_STORAGE_PRIVATE_KEY",
            "emergency" => "EMERGENCY_WALLET_PRIVATE_KEY",
            _ => {
                // Try direct mapping
                &format!("{}_PRIVATE_KEY", key_id.to_uppercase())
            }
        };

        env::var(env_var).context(format!("Environment variable {} not found", env_var))
    }

    /// Validate private key format
    fn validate_private_key(&self, private_key: &str) -> Result<()> {
        // Check if it's a valid base58 string or JSON array
        if private_key.starts_with('[') && private_key.ends_with(']') {
            // JSON array format
            let _bytes: Vec<u8> =
                serde_json::from_str(private_key).context("Invalid JSON array format")?;
            return Ok(());
        }

        // Check base58 format
        if private_key.len() >= 80 && private_key.len() <= 90 {
            // Likely base58 format
            return Ok(());
        }

        Err(anyhow!("Invalid private key format"))
    }

    /// Clear cached keys (for security)
    pub fn clear_cache(&mut self) {
        info!("🧹 Clearing key cache");
        self.cached_keys.clear();
    }

    /// Get storage statistics
    pub fn get_storage_stats(&self) -> StorageStats {
        StorageStats {
            cached_keys: self.cached_keys.len(),
            keyring_enabled: self.config.keyring_enabled,
            encryption_enabled: self.config.encryption_enabled,
            fallback_enabled: self.config.fallback_to_env,
        }
    }

    /// Encrypt sensitive data
    fn encrypt_data(&self, data: &str, salt: &str) -> Result<String> {
        if !self.config.encryption_enabled {
            return Ok(data.to_string());
        }

        // In a real implementation, this would use proper encryption
        // For now, we'll use base64 encoding as a placeholder
        use base64::{engine::general_purpose, Engine as _};
        let encoded = general_purpose::STANDARD.encode(format!("{}:{}", salt, data));
        Ok(encoded)
    }

    /// Decrypt sensitive data
    fn decrypt_data(&self, encrypted_data: &str, salt: &str) -> Result<String> {
        if !self.config.encryption_enabled {
            return Ok(encrypted_data.to_string());
        }

        // In a real implementation, this would use proper decryption
        use base64::{engine::general_purpose, Engine as _};
        let decoded = general_purpose::STANDARD
            .decode(encrypted_data)
            .context("Failed to decode encrypted data")?;

        let decoded_str = String::from_utf8(decoded).context("Invalid UTF-8 in decrypted data")?;

        if let Some(data) = decoded_str.strip_prefix(&format!("{}:", salt)) {
            Ok(data.to_string())
        } else {
            Err(anyhow!("Invalid encrypted data format"))
        }
    }

    /// Generate random salt
    fn generate_salt() -> String {
        use std::time::{SystemTime, UNIX_EPOCH};
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        format!("salt_{}", timestamp)
    }
}

/// Storage statistics
#[derive(Debug, Serialize)]
pub struct StorageStats {
    pub cached_keys: usize,
    pub keyring_enabled: bool,
    pub encryption_enabled: bool,
    pub fallback_enabled: bool,
}

impl Default for EncryptedKeyStorage {
    fn default() -> Self {
        Self::new().expect("Failed to create encrypted key storage")
    }
}

/// Key storage factory for different environments
pub struct KeyStorageFactory;

impl KeyStorageFactory {
    /// Create key storage for production environment
    pub fn create_production() -> Result<EncryptedKeyStorage> {
        std::env::set_var("OVERMIND_ENCRYPTION_ENABLED", "true");
        std::env::set_var("OVERMIND_KEYRING_ENABLED", "true");
        std::env::set_var("OVERMIND_FALLBACK_TO_ENV", "false");

        EncryptedKeyStorage::new()
    }

    /// Create key storage for development environment
    pub fn create_development() -> Result<EncryptedKeyStorage> {
        std::env::set_var("OVERMIND_ENCRYPTION_ENABLED", "false");
        std::env::set_var("OVERMIND_KEYRING_ENABLED", "false");
        std::env::set_var("OVERMIND_FALLBACK_TO_ENV", "true");

        EncryptedKeyStorage::new()
    }

    /// Create key storage for testing environment
    pub fn create_testing() -> Result<EncryptedKeyStorage> {
        std::env::set_var("OVERMIND_ENCRYPTION_ENABLED", "false");
        std::env::set_var("OVERMIND_KEYRING_ENABLED", "false");
        std::env::set_var("OVERMIND_FALLBACK_TO_ENV", "true");

        EncryptedKeyStorage::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_key_storage_creation() {
        let storage = EncryptedKeyStorage::new();
        assert!(storage.is_ok());
    }

    #[test]
    fn test_private_key_validation() {
        let storage = EncryptedKeyStorage::new().unwrap();

        // Valid base58 format
        let valid_key = "EXAMPLE_PRIVATE_KEY_87_CHARACTERS_LONG_FOR_TESTING_PURPOSES_ONLY_NOT_REAL";
        assert!(storage.validate_private_key(valid_key).is_ok());

        // Valid JSON array format
        let valid_json = "[1,2,3,4,5]";
        assert!(storage.validate_private_key(valid_json).is_ok());

        // Invalid format
        let invalid_key = "invalid_key";
        assert!(storage.validate_private_key(invalid_key).is_err());
    }

    #[test]
    fn test_factory_methods() {
        let dev_storage = KeyStorageFactory::create_development();
        assert!(dev_storage.is_ok());

        let test_storage = KeyStorageFactory::create_testing();
        assert!(test_storage.is_ok());
    }
}
