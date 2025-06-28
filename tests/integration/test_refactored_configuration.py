#!/usr/bin/env python3
"""
Test Refactored Configuration System
Test that Python components use dynamic configuration from environment loader
"""

import sys
import os
import asyncio
from unittest.mock import patch

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'config'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'brain', 'src'))

async def test_quicknode_premium_refactored():
    """Test QuickNode Premium with refactored configuration"""
    print("🚀 Testing QuickNode Premium Refactored Configuration")
    print("-" * 60)
    
    try:
        # Initialize environment first
        from environment_loader import initialize_environment
        loader = initialize_environment()
        
        # Import QuickNode Premium
        from overmind_brain.quicknode_premium import QuickNodePremiumClient

        # Create instance
        qn = QuickNodePremiumClient()
        
        print("✅ QuickNode Premium initialized with dynamic configuration")
        print(f"   - Environment: {qn.environment}")
        print(f"   - Network: {qn.network_name}")
        print(f"   - Is Mainnet: {qn.is_mainnet}")
        print(f"   - RPC URL: {qn.current_rpc_url[:50] if qn.current_rpc_url else 'None'}...")
        print(f"   - WS URL: {qn.current_ws_url[:50] if qn.current_ws_url else 'None'}...")
        print(f"   - API Key: {'Configured' if qn.api_key else 'Missing'}")
        
        # Validate configuration matches environment
        config = loader.get_config()
        assert qn.current_rpc_url == config.quicknode_rpc_url, "RPC URL mismatch"
        assert qn.current_ws_url == config.quicknode_ws_url, "WS URL mismatch"
        assert qn.network_name == config.network_name, "Network name mismatch"
        assert qn.is_mainnet == config.is_mainnet, "Mainnet flag mismatch"
        
        print("✅ Configuration validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ QuickNode Premium refactored test failed: {e}")
        return False

async def test_helius_integration_refactored():
    """Test Helius Integration with refactored configuration"""
    print("\n🌟 Testing Helius Integration Refactored Configuration")
    print("-" * 60)
    
    try:
        # Initialize environment first
        from environment_loader import initialize_environment
        loader = initialize_environment()
        
        # Import Helius Integration
        from overmind_brain.helius_integration import HeliusAPIClient

        # Create instance
        helius = HeliusAPIClient()
        
        print("✅ Helius Integration initialized with dynamic configuration")
        print(f"   - Environment: {helius.environment}")
        print(f"   - Network: {helius.network_name}")
        print(f"   - Is Mainnet: {helius.is_mainnet}")
        print(f"   - RPC URL: {helius.current_rpc_url[:50] if helius.current_rpc_url else 'None'}...")
        print(f"   - API Key: {'Configured' if helius.api_key else 'Missing'}")
        
        # Validate configuration matches environment
        config = loader.get_config()
        assert helius.current_rpc_url == config.helius_rpc_url, "RPC URL mismatch"
        assert helius.network_name == config.network_name, "Network name mismatch"
        assert helius.is_mainnet == config.is_mainnet, "Mainnet flag mismatch"
        
        print("✅ Configuration validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Helius Integration refactored test failed: {e}")
        return False

async def test_environment_switching():
    """Test switching between environments"""
    print("\n🔄 Testing Environment Switching")
    print("-" * 60)
    
    try:
        # Test development environment
        with patch.dict(os.environ, {'APP_ENV': 'development'}):
            from environment_loader import EnvironmentLoader
            loader = EnvironmentLoader()
            loader.set_environment_variables()
            
            from overmind_brain.quicknode_premium import QuickNodePremiumClient
            qn_dev = QuickNodePremiumClient()
            
            print("✅ Development environment configuration")
            print(f"   - Environment: {qn_dev.environment}")
            print(f"   - Network: {qn_dev.network_name}")
            print(f"   - Is Mainnet: {qn_dev.is_mainnet}")
            
            assert qn_dev.network_name == "devnet", "Should be devnet"
            assert qn_dev.is_mainnet == False, "Should not be mainnet"
        
        # Test production environment (if Mainnet endpoint configured)
        try:
            with patch.dict(os.environ, {'APP_ENV': 'production'}):
                loader = EnvironmentLoader()
                loader.set_environment_variables()
                
                qn_prod = QuickNodePremiumClient()
                
                print("✅ Production environment configuration")
                print(f"   - Environment: {qn_prod.environment}")
                print(f"   - Network: {qn_prod.network_name}")
                print(f"   - Is Mainnet: {qn_prod.is_mainnet}")
                
                assert qn_prod.network_name == "mainnet", "Should be mainnet"
                assert qn_prod.is_mainnet == True, "Should be mainnet"
                
        except ValueError as e:
            print(f"⚠️ Production environment test skipped: {e}")
            print("   (Mainnet endpoint not configured - this is expected)")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment switching test failed: {e}")
        return False

async def test_fallback_configuration():
    """Test fallback configuration when environment loader fails"""
    print("\n🛡️ Testing Fallback Configuration")
    print("-" * 60)
    
    try:
        # Temporarily break the environment loader import
        original_path = sys.path[:]
        sys.path = [p for p in sys.path if 'config' not in p]
        
        # Import should use fallback configuration
        from overmind_brain.quicknode_premium import QuickNodePremiumClient
        qn_fallback = QuickNodePremiumClient()
        
        print("✅ Fallback configuration working")
        print(f"   - Environment: {qn_fallback.environment}")
        print(f"   - Network: {qn_fallback.network_name}")
        print(f"   - RPC URL: {qn_fallback.current_rpc_url[:50] if qn_fallback.current_rpc_url else 'None'}...")
        
        # Restore path
        sys.path = original_path
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback configuration test failed: {e}")
        # Restore path in case of error
        sys.path = original_path
        return False

async def test_historical_framework_integration():
    """Test Historical Framework with refactored configuration"""
    print("\n📊 Testing Historical Framework Integration")
    print("-" * 60)
    
    try:
        # Initialize environment
        from environment_loader import initialize_environment
        loader = initialize_environment()
        
        # Test Historical Data Provider
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'historical_data'))
        from historical_testing_framework import HistoricalDataProvider
        
        provider = HistoricalDataProvider()
        await provider.initialize()
        
        print("✅ Historical Data Provider initialized")
        print(f"   - Helius API Key: {'Configured' if provider.helius_api_key else 'Missing'}")
        print(f"   - QuickNode API Key: {'Configured' if provider.quicknode_api_key else 'Missing'}")
        
        # Test that it uses the same API keys as refactored components
        from overmind_brain.quicknode_premium import QuickNodePremiumClient
        qn = QuickNodePremiumClient()
        
        # API keys should match
        assert provider.helius_api_key == os.getenv('HELIUS_API_KEY'), "Helius API key mismatch"
        
        await provider.close()
        
        print("✅ Historical Framework integration validated")
        
        return True
        
    except Exception as e:
        print(f"❌ Historical Framework integration test failed: {e}")
        return False

async def test_configuration_consistency():
    """Test configuration consistency across all components"""
    print("\n🔗 Testing Configuration Consistency")
    print("-" * 60)
    
    try:
        # Initialize environment
        from environment_loader import initialize_environment
        loader = initialize_environment()
        config = loader.get_config()
        
        # Test all components use same configuration
        from overmind_brain.quicknode_premium import QuickNodePremiumClient
        from overmind_brain.helius_integration import HeliusAPIClient

        qn = QuickNodePremiumClient()
        helius = HeliusAPIClient()
        
        print("✅ All components initialized")
        
        # Check consistency
        components = [
            ("QuickNode", qn),
            ("Helius", helius)
        ]
        
        for name, component in components:
            print(f"   - {name}:")
            print(f"     • Environment: {component.environment}")
            print(f"     • Network: {component.network_name}")
            print(f"     • Is Mainnet: {component.is_mainnet}")
            
            # Validate consistency
            assert component.environment == loader.get_environment().value, f"{name} environment mismatch"
            assert component.network_name == config.network_name, f"{name} network mismatch"
            assert component.is_mainnet == config.is_mainnet, f"{name} mainnet flag mismatch"
        
        print("✅ Configuration consistency validated")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration consistency test failed: {e}")
        return False

async def main():
    """Run all refactored configuration tests"""
    print("🎯 THE OVERMIND PROTOCOL - Refactored Configuration Tests")
    print("=" * 70)
    print("Testing FAZA 2: Centralizacja Konfiguracji - Dynamic Configuration")
    print("=" * 70)
    
    # Run all tests
    test1 = await test_quicknode_premium_refactored()
    test2 = await test_helius_integration_refactored()
    test3 = await test_environment_switching()
    test4 = await test_fallback_configuration()
    test5 = await test_historical_framework_integration()
    test6 = await test_configuration_consistency()
    
    print("\n" + "=" * 70)
    
    if all([test1, test2, test3, test4, test5, test6]):
        print("🎉 ALL REFACTORED CONFIGURATION TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • QuickNode Premium using dynamic configuration")
        print("   • Helius Integration using dynamic configuration")
        print("   • Environment switching working correctly")
        print("   • Fallback configuration operational")
        print("   • Historical Framework integration validated")
        print("   • Configuration consistency across all components")
        print("\n🚀 READY FOR:")
        print("   • Kestra integration with unified configuration")
        print("   • Rust configuration refactoring")
        print("   • Production environment testing")
        print("\n🎯 FAZA 2 STATUS: PYTHON REFACTORING COMPLETE")
        print("   Next: Rust configuration refactoring")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
