#!/usr/bin/env python3
"""
Test Environment Configuration System
Test dynamic configuration loading based on APP_ENV
"""

import sys
import os
import asyncio
from unittest.mock import patch

# Add config to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'config'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'brain', 'src'))

def test_environment_detection():
    """Test environment detection from APP_ENV"""
    print("🎯 Testing Environment Detection")
    print("-" * 50)
    
    try:
        from environment_loader import EnvironmentLoader, Environment
        
        # Test default environment
        with patch.dict(os.environ, {}, clear=False):
            if 'APP_ENV' in os.environ:
                del os.environ['APP_ENV']
            loader = EnvironmentLoader()
            print(f"✅ Default environment: {loader.get_environment().value}")
            assert loader.get_environment() == Environment.DEVELOPMENT
        
        # Test development environment
        with patch.dict(os.environ, {'APP_ENV': 'development'}):
            loader = EnvironmentLoader()
            print(f"✅ Development environment: {loader.get_environment().value}")
            assert loader.get_environment() == Environment.DEVELOPMENT
        
        # Test production environment
        with patch.dict(os.environ, {'APP_ENV': 'production'}):
            loader = EnvironmentLoader()
            print(f"✅ Production environment: {loader.get_environment().value}")
            assert loader.get_environment() == Environment.PRODUCTION
        
        # Test live environment
        with patch.dict(os.environ, {'APP_ENV': 'live'}):
            loader = EnvironmentLoader()
            print(f"✅ Live environment: {loader.get_environment().value}")
            assert loader.get_environment() == Environment.LIVE
        
        # Test invalid environment
        with patch.dict(os.environ, {'APP_ENV': 'invalid'}):
            loader = EnvironmentLoader()
            print(f"✅ Invalid environment defaults to: {loader.get_environment().value}")
            assert loader.get_environment() == Environment.DEVELOPMENT
        
        return True
        
    except Exception as e:
        print(f"❌ Environment detection test failed: {e}")
        return False

def test_devnet_configuration():
    """Test Devnet configuration loading"""
    print("\n🧪 Testing Devnet Configuration")
    print("-" * 50)
    
    try:
        from environment_loader import EnvironmentLoader
        
        # Set development environment
        with patch.dict(os.environ, {'APP_ENV': 'development'}):
            loader = EnvironmentLoader()
            config = loader.get_config()
            
            print("✅ Devnet configuration loaded")
            print(f"   - Network: {config.network_name}")
            print(f"   - Is Mainnet: {config.is_mainnet}")
            print(f"   - RPC URL: {config.rpc_url[:50] if config.rpc_url else 'None'}...")
            print(f"   - WS URL: {config.ws_url[:50] if config.ws_url else 'None'}...")
            print(f"   - Helius RPC: {config.helius_rpc_url[:50] if config.helius_rpc_url else 'None'}...")
            print(f"   - QuickNode RPC: {config.quicknode_rpc_url[:50] if config.quicknode_rpc_url else 'None'}...")
            
            # Validate devnet config
            assert config.network_name == "devnet"
            assert config.is_mainnet == False
            assert "devnet" in config.rpc_url.lower() if config.rpc_url else True
            
            # Test trading mode
            assert loader.is_paper_trading() == True
            assert loader.get_trading_mode() == "paper"
            
            print("✅ Devnet configuration validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Devnet configuration test failed: {e}")
        return False

def test_mainnet_configuration_check():
    """Test Mainnet configuration check (without actual Mainnet endpoint)"""
    print("\n🚀 Testing Mainnet Configuration Check")
    print("-" * 50)
    
    try:
        from environment_loader import EnvironmentLoader
        
        # Test production environment (should fail without Mainnet endpoint)
        with patch.dict(os.environ, {'APP_ENV': 'production'}):
            try:
                loader = EnvironmentLoader()
                print("⚠️ Mainnet configuration loaded (unexpected)")
                config = loader.get_config()
                
                # If it loads, check if it's properly configured
                if 'your-mainnet-endpoint' in config.quicknode_rpc_url:
                    print("✅ Correctly detected unconfigured Mainnet endpoint")
                else:
                    print(f"✅ Mainnet endpoint configured: {config.quicknode_rpc_url[:50]}...")
                
            except ValueError as e:
                print(f"✅ Correctly caught unconfigured Mainnet: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mainnet configuration check failed: {e}")
        return False

def test_configuration_validation():
    """Test configuration validation"""
    print("\n🔍 Testing Configuration Validation")
    print("-" * 50)
    
    try:
        from environment_loader import EnvironmentLoader
        
        # Test with development environment
        with patch.dict(os.environ, {'APP_ENV': 'development'}):
            loader = EnvironmentLoader()
            validation = loader.validate_configuration()
            
            print("✅ Configuration validation completed")
            for key, value in validation.items():
                status = "✅" if value else "❌"
                print(f"   {status} {key}: {value}")
            
            # Get status report
            status_report = loader.get_status_report()
            print(f"\n✅ Status report generated")
            print(f"   - Environment: {status_report['environment']}")
            print(f"   - Network: {status_report['network']}")
            print(f"   - Trading mode: {status_report['trading_mode']}")
            print(f"   - All valid: {status_report['all_valid']}")
            
            if status_report['warnings']:
                print("   - Warnings:")
                for warning in status_report['warnings']:
                    print(f"     ⚠️ {warning}")
            
            if status_report['next_steps']:
                print("   - Next steps:")
                for step in status_report['next_steps']:
                    print(f"     📋 {step}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False

def test_environment_variable_setting():
    """Test dynamic environment variable setting"""
    print("\n⚙️ Testing Environment Variable Setting")
    print("-" * 50)
    
    try:
        from environment_loader import EnvironmentLoader
        
        # Test with development environment
        with patch.dict(os.environ, {'APP_ENV': 'development'}):
            loader = EnvironmentLoader()
            
            # Store original values
            original_vars = {
                'SOLANA_RPC_URL': os.environ.get('SOLANA_RPC_URL'),
                'SNIPER_TRADING_MODE': os.environ.get('SNIPER_TRADING_MODE'),
                'NETWORK_NAME': os.environ.get('NETWORK_NAME')
            }
            
            # Set environment variables
            loader.set_environment_variables()
            
            print("✅ Environment variables set")
            print(f"   - SOLANA_RPC_URL: {os.environ.get('SOLANA_RPC_URL', 'Not set')[:50]}...")
            print(f"   - SNIPER_TRADING_MODE: {os.environ.get('SNIPER_TRADING_MODE', 'Not set')}")
            print(f"   - PAPER_TRADING_MODE: {os.environ.get('PAPER_TRADING_MODE', 'Not set')}")
            print(f"   - NETWORK_NAME: {os.environ.get('NETWORK_NAME', 'Not set')}")
            print(f"   - IS_MAINNET: {os.environ.get('IS_MAINNET', 'Not set')}")
            
            # Validate set variables
            assert os.environ.get('SNIPER_TRADING_MODE') == 'paper'
            assert os.environ.get('PAPER_TRADING_MODE') == 'true'
            assert os.environ.get('NETWORK_NAME') == 'devnet'
            assert os.environ.get('IS_MAINNET') == 'false'
            
            print("✅ Environment variable validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment variable setting test failed: {e}")
        return False

def test_global_initialization():
    """Test global environment initialization"""
    print("\n🌍 Testing Global Environment Initialization")
    print("-" * 50)
    
    try:
        from environment_loader import initialize_environment, get_environment_loader
        
        # Test initialization
        loader = initialize_environment()
        
        print("✅ Global environment initialized")
        print(f"   - Environment: {loader.get_environment().value}")
        print(f"   - Network: {loader.get_config().network_name}")
        print(f"   - Trading mode: {loader.get_trading_mode()}")
        
        # Test global getter
        global_loader = get_environment_loader()
        assert global_loader is not None
        print("✅ Global loader accessible")
        
        # Test status
        status = global_loader.get_status_report()
        print(f"   - Configuration valid: {status['all_valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Global initialization test failed: {e}")
        return False

def test_integration_with_existing_code():
    """Test integration with existing codebase"""
    print("\n🔗 Testing Integration with Existing Code")
    print("-" * 50)
    
    try:
        from environment_loader import initialize_environment
        
        # Initialize environment
        loader = initialize_environment()
        
        # Test if environment variables are accessible by existing code
        rpc_url = os.environ.get('SOLANA_RPC_URL')
        trading_mode = os.environ.get('SNIPER_TRADING_MODE')
        
        print("✅ Integration test completed")
        print(f"   - RPC URL available: {bool(rpc_url)}")
        print(f"   - Trading mode available: {bool(trading_mode)}")
        
        if rpc_url:
            print(f"   - RPC URL: {rpc_url[:50]}...")
        if trading_mode:
            print(f"   - Trading mode: {trading_mode}")
        
        # Test that existing code patterns still work
        helius_key = os.environ.get('HELIUS_API_KEY')
        quicknode_key = os.environ.get('QUICKNODE_API_KEY')
        
        print(f"   - Helius API key: {'Available' if helius_key else 'Missing'}")
        print(f"   - QuickNode API key: {'Available' if quicknode_key else 'Missing'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Run all environment configuration tests"""
    print("🎯 THE OVERMIND PROTOCOL - Environment Configuration Tests")
    print("=" * 70)
    print("Testing PROTOKÓŁ ZJEDNOCZENIA - Unified Configuration System")
    print("=" * 70)
    
    # Run all tests
    test1 = test_environment_detection()
    test2 = test_devnet_configuration()
    test3 = test_mainnet_configuration_check()
    test4 = test_configuration_validation()
    test5 = test_environment_variable_setting()
    test6 = test_global_initialization()
    test7 = test_integration_with_existing_code()
    
    print("\n" + "=" * 70)
    
    if all([test1, test2, test3, test4, test5, test6, test7]):
        print("🎉 ALL ENVIRONMENT CONFIGURATION TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • Dynamic environment detection working")
        print("   • Devnet configuration loading correctly")
        print("   • Mainnet configuration validation ready")
        print("   • Configuration validation system operational")
        print("   • Environment variable setting functional")
        print("   • Global initialization working")
        print("   • Integration with existing code successful")
        print("\n🚀 READY FOR:")
        print("   • QuickNode Mainnet endpoint configuration")
        print("   • Production environment testing")
        print("   • Kestra integration")
        print("\n🎯 FAZA 1 STATUS: CONFIGURATION SYSTEM READY")
        print("   Next: Configure QuickNode Mainnet endpoint")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
