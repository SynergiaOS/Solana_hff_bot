#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Environment Configuration Loader
Dynamic configuration loading based on APP_ENV
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"  # Devnet + Paper Trading
    PRODUCTION = "production"    # Mainnet + Paper Trading  
    LIVE = "live"               # Mainnet + Live Trading

@dataclass
class NetworkConfig:
    """Network configuration for a specific environment"""
    rpc_url: str
    ws_url: str
    helius_rpc_url: str
    helius_ws_url: str
    quicknode_rpc_url: str
    quicknode_ws_url: str
    network_name: str
    is_mainnet: bool

class EnvironmentLoader:
    """
    Dynamic environment configuration loader
    Loads appropriate endpoints based on APP_ENV
    """
    
    def __init__(self):
        self.current_env = self._get_environment()
        self.config = self._load_configuration()
        
    def _get_environment(self) -> Environment:
        """Get current environment from APP_ENV"""
        env_str = os.getenv('APP_ENV', 'development').lower()
        
        try:
            return Environment(env_str)
        except ValueError:
            logger.warning(f"Invalid APP_ENV: {env_str}, defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_configuration(self) -> NetworkConfig:
        """Load configuration for current environment"""
        
        if self.current_env == Environment.DEVELOPMENT:
            return self._load_devnet_config()
        elif self.current_env == Environment.PRODUCTION:
            return self._load_mainnet_config(paper_trading=True)
        elif self.current_env == Environment.LIVE:
            return self._load_mainnet_config(paper_trading=False)
        else:
            logger.error(f"Unknown environment: {self.current_env}")
            return self._load_devnet_config()
    
    def _load_devnet_config(self) -> NetworkConfig:
        """Load Devnet configuration"""
        logger.info("🧪 Loading DEVNET configuration")
        
        return NetworkConfig(
            rpc_url=os.getenv('QUICKNODE_DEVNET_RPC_URL', os.getenv('SOLANA_DEVNET_RPC_URL')),
            ws_url=os.getenv('QUICKNODE_DEVNET_WS_URL', os.getenv('SOLANA_DEVNET_WS_URL')),
            helius_rpc_url=os.getenv('HELIUS_DEVNET_RPC_URL'),
            helius_ws_url=os.getenv('HELIUS_DEVNET_WS_URL'),
            quicknode_rpc_url=os.getenv('QUICKNODE_DEVNET_RPC_URL'),
            quicknode_ws_url=os.getenv('QUICKNODE_DEVNET_WS_URL'),
            network_name="devnet",
            is_mainnet=False
        )
    
    def _load_mainnet_config(self, paper_trading: bool = True) -> NetworkConfig:
        """Load Mainnet configuration"""
        mode = "PAPER TRADING" if paper_trading else "LIVE TRADING"
        logger.info(f"🚀 Loading MAINNET configuration ({mode})")
        
        # Check if Mainnet endpoints are configured
        quicknode_mainnet = os.getenv('QUICKNODE_MAINNET_RPC_URL')
        if not quicknode_mainnet or 'your-mainnet-endpoint' in quicknode_mainnet:
            logger.error("❌ MAINNET QuickNode endpoint not configured!")
            logger.error("Please create Mainnet endpoint in QuickNode panel")
            raise ValueError("Mainnet QuickNode endpoint not configured")
        
        return NetworkConfig(
            rpc_url=quicknode_mainnet,
            ws_url=os.getenv('QUICKNODE_MAINNET_WS_URL'),
            helius_rpc_url=os.getenv('HELIUS_MAINNET_RPC_URL'),
            helius_ws_url=os.getenv('HELIUS_MAINNET_WS_URL'),
            quicknode_rpc_url=quicknode_mainnet,
            quicknode_ws_url=os.getenv('QUICKNODE_MAINNET_WS_URL'),
            network_name="mainnet",
            is_mainnet=True
        )
    
    def get_config(self) -> NetworkConfig:
        """Get current network configuration"""
        return self.config
    
    def get_environment(self) -> Environment:
        """Get current environment"""
        return self.current_env
    
    def is_paper_trading(self) -> bool:
        """Check if paper trading mode is enabled"""
        if self.current_env == Environment.LIVE:
            return False
        return True
    
    def get_trading_mode(self) -> str:
        """Get trading mode string"""
        if self.current_env == Environment.LIVE:
            return "live"
        return "paper"
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate current configuration"""
        validation = {
            'environment_set': self.current_env is not None,
            'rpc_url_configured': bool(self.config.rpc_url),
            'ws_url_configured': bool(self.config.ws_url),
            'helius_configured': bool(self.config.helius_rpc_url),
            'quicknode_configured': bool(self.config.quicknode_rpc_url),
            'api_keys_present': bool(os.getenv('HELIUS_API_KEY') and (os.getenv('QUICKNODE_API_KEY') or os.getenv('SNIPER_QUICKNODE_API_KEY')))
        }
        
        # Additional validation for Mainnet
        if self.config.is_mainnet:
            validation['mainnet_endpoints_configured'] = (
                'your-mainnet-endpoint' not in self.config.quicknode_rpc_url
            )
        
        return validation
    
    def get_status_report(self) -> Dict[str, any]:
        """Get comprehensive status report"""
        validation = self.validate_configuration()
        
        return {
            'environment': self.current_env.value,
            'network': self.config.network_name,
            'is_mainnet': self.config.is_mainnet,
            'trading_mode': self.get_trading_mode(),
            'paper_trading': self.is_paper_trading(),
            'endpoints': {
                'rpc_url': self.config.rpc_url[:50] + '...' if self.config.rpc_url else None,
                'ws_url': self.config.ws_url[:50] + '...' if self.config.ws_url else None,
                'helius_rpc': self.config.helius_rpc_url[:50] + '...' if self.config.helius_rpc_url else None,
                'quicknode_rpc': self.config.quicknode_rpc_url[:50] + '...' if self.config.quicknode_rpc_url else None
            },
            'validation': validation,
            'all_valid': all(validation.values()),
            'warnings': self._get_warnings(validation),
            'next_steps': self._get_next_steps(validation)
        }
    
    def _get_warnings(self, validation: Dict[str, bool]) -> list:
        """Get configuration warnings"""
        warnings = []
        
        if not validation.get('api_keys_present'):
            warnings.append("API keys missing - check HELIUS_API_KEY and QUICKNODE_API_KEY/SNIPER_QUICKNODE_API_KEY")
        
        if self.config.is_mainnet and not validation.get('mainnet_endpoints_configured', True):
            warnings.append("Mainnet QuickNode endpoint not configured - create in QuickNode panel")
        
        if not validation.get('quicknode_configured'):
            warnings.append("QuickNode endpoints not configured")
        
        return warnings
    
    def _get_next_steps(self, validation: Dict[str, bool]) -> list:
        """Get next steps based on validation"""
        steps = []
        
        if self.config.is_mainnet and not validation.get('mainnet_endpoints_configured', True):
            steps.append("1. Log into QuickNode panel")
            steps.append("2. Create new Mainnet endpoint")
            steps.append("3. Update QUICKNODE_MAINNET_RPC_URL in .env")
            steps.append("4. Update QUICKNODE_MAINNET_WS_URL in .env")
        
        if not validation.get('api_keys_present'):
            steps.append("Configure missing API keys in .env file")
        
        if all(validation.values()):
            steps.append("✅ Configuration complete - ready for testing")
        
        return steps
    
    def set_environment_variables(self):
        """Set dynamic environment variables based on current config"""
        logger.info(f"Setting environment variables for {self.current_env.value}")
        
        # Set dynamic variables
        os.environ['SOLANA_RPC_URL'] = self.config.rpc_url or ''
        os.environ['SOLANA_WS_URL'] = self.config.ws_url or ''
        os.environ['QUICKNODE_RPC_URL'] = self.config.quicknode_rpc_url or ''
        os.environ['QUICKNODE_WS_URL'] = self.config.quicknode_ws_url or ''
        os.environ['HELIUS_RPC_URL'] = self.config.helius_rpc_url or ''
        os.environ['HELIUS_WS_URL'] = self.config.helius_ws_url or ''
        
        # Set trading mode
        os.environ['SNIPER_TRADING_MODE'] = self.get_trading_mode()
        os.environ['PAPER_TRADING_MODE'] = str(self.is_paper_trading()).lower()
        
        # Set network info
        os.environ['NETWORK_NAME'] = self.config.network_name
        os.environ['IS_MAINNET'] = str(self.config.is_mainnet).lower()
        
        logger.info(f"✅ Environment variables set for {self.config.network_name}")

# Global instance
environment_loader = EnvironmentLoader()

def get_environment_loader() -> EnvironmentLoader:
    """Get global environment loader instance"""
    return environment_loader

def initialize_environment():
    """Initialize environment and set variables"""
    loader = get_environment_loader()
    loader.set_environment_variables()
    
    status = loader.get_status_report()
    logger.info(f"Environment initialized: {status['environment']} ({status['network']})")
    
    if not status['all_valid']:
        logger.warning("Configuration issues detected:")
        for warning in status['warnings']:
            logger.warning(f"  ⚠️ {warning}")
    
    return loader
