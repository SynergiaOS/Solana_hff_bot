# THE OVERMIND PROTOCOL - Vault Configuration
# Production-ready Vault setup for multi-wallet security

# Storage backend - Integrated Storage (Raft)
storage "raft" {
  path    = "/vault/data"
  node_id = "overmind-vault-1"
  
  retry_join {
    leader_api_addr = "https://vault.overmind.local:8200"
  }
}

# Listener configuration
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/vault/tls/vault.crt"
  tls_key_file  = "/vault/tls/vault.key"
  
  # Security headers
  tls_min_version = "tls12"
  tls_cipher_suites = "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384"
}

# API address
api_addr = "https://vault.overmind.local:8200"

# Cluster address
cluster_addr = "https://vault.overmind.local:8201"

# UI configuration
ui = true

# Logging
log_level = "INFO"
log_format = "json"

# Disable mlock for containers
disable_mlock = true

# Telemetry
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}

# Seal configuration (Auto-unseal with cloud KMS recommended for production)
# seal "awskms" {
#   region     = "us-east-1"
#   kms_key_id = "alias/vault-unseal-key"
# }

# Plugin directory
plugin_directory = "/vault/plugins"

# Maximum lease TTL
max_lease_ttl = "768h"
default_lease_ttl = "168h"

# Entropy Augmentation (Enterprise feature)
# entropy "seal" {
#   mode = "augmentation"
# }
