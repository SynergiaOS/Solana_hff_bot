# THE OVERMIND PROTOCOL - Vault Agent Configuration
# Auto-authentication and secret caching for trading bot

# Vault server configuration
vault {
  address = "https://vault:8200"
  tls_skip_verify = true
}

# Auto-authentication using AppRole
auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path = "/vault/cache/role-id"
      secret_id_file_path = "/vault/cache/secret-id"
      remove_secret_id_file_after_reading = false
    }
  }

  sink "file" {
    config = {
      path = "/vault/cache/token"
      mode = 0600
    }
  }
}

# Cache configuration
cache {
  use_auto_auth_token = true
  
  # Cache wallet secrets for performance
  persist = {
    type = "kubernetes"
    path = "/vault/cache/persistent"
    keep_after_import = true
    exit_on_err = true
  }
}

# API proxy for applications
api_proxy {
  use_auto_auth_token = true
}

# Listener for applications to connect to
listener "tcp" {
  address = "127.0.0.1:8100"
  tls_disable = true
}

# Template for wallet configuration
template {
  source = "/vault/templates/wallet-config.tpl"
  destination = "/vault/cache/wallet-config.json"
  perms = 0600
  
  # Restart trading bot when wallet config changes
  command = "pkill -HUP overmind-core || true"
  command_timeout = "30s"
}

# Template for main trading wallet
template {
  source = "/vault/templates/main-wallet.tpl"
  destination = "/vault/cache/main-wallet.json"
  perms = 0600
  
  # Backup configuration
  backup = true
  
  # Wait for dependencies
  wait {
    min = "2s"
    max = "10s"
  }
}

# Logging configuration
log_level = "INFO"
log_format = "json"
log_file = "/vault/logs/agent.log"

# Process ID file
pid_file = "/vault/cache/agent.pid"
