#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Deployment Configuration Validator
Validates all configuration before deployment to prevent issues
"""

import os
import subprocess
import json
from typing import Dict, List, Any

class DeploymentConfigValidator:
    """
    Validates deployment configuration to prevent common issues
    
    Checks:
    1. Environment variables
    2. Docker configuration
    3. API keys format
    4. File paths
    5. Compilation status
    """
    
    def __init__(self):
        """Initialize validator"""
        self.issues = []
        self.warnings = []
        self.successes = []
        
        print("🔍 THE OVERMIND PROTOCOL - Configuration Validator")
        print("=" * 60)
    
    def validate_environment_variables(self) -> bool:
        """Validate environment variables configuration"""
        
        print("\n🔧 VALIDATING ENVIRONMENT VARIABLES...")
        
        # Required variables for production
        required_vars = {
            'DEEPSEEK_API_KEY': 'DeepSeek V2 API key (primary AI model)',
            'SOLANA_WALLET_PRIVATE_KEY': 'Solana wallet private key (64 bytes)',
            'HELIUS_API_KEY': 'Helius API key for Solana data',
            'SOLANA_RPC_URL': 'Solana RPC endpoint URL'
        }
        
        # Optional but recommended variables
        optional_vars = {
            'OPENAI_API_KEY': 'OpenAI API key (backup AI model)',
            'PERPLEXITY_API_KEY': 'Perplexity API key',
            'MISTRAL_API_KEY': 'Mistral API key',
            'GOOGLE_API_KEY': 'Google API key',
            'JINA_API_KEY': 'Jina AI API key'
        }
        
        # Variables that should NOT be set (deprecated)
        deprecated_vars = {
            'GROQ_API_KEY': 'GROQ API (replaced by DeepSeek V2)',
            'FINANCIAL_DATASETS_API_KEY': 'Financial datasets (optional)'
        }
        
        all_valid = True
        
        # Check required variables
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value or value == f'your_{var.lower()}_here':
                self.issues.append(f"❌ Missing required: {var} ({description})")
                all_valid = False
            else:
                self.successes.append(f"✅ Found: {var}")
        
        # Check optional variables
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if not value or value == f'your_{var.lower()}_here':
                self.warnings.append(f"⚠️ Optional missing: {var} ({description})")
            else:
                self.successes.append(f"✅ Found: {var}")
        
        # Check deprecated variables
        for var, description in deprecated_vars.items():
            value = os.getenv(var)
            if value and value != '':
                self.warnings.append(f"⚠️ Deprecated: {var} ({description})")
        
        return all_valid
    
    def validate_docker_configuration(self) -> bool:
        """Validate Docker configuration"""
        
        print("\n🐳 VALIDATING DOCKER CONFIGURATION...")
        
        all_valid = True
        
        # Check Docker Compose file exists
        compose_file = 'infrastructure/compose/docker-compose.production.yml'
        if not os.path.exists(compose_file):
            self.issues.append(f"❌ Missing Docker Compose file: {compose_file}")
            all_valid = False
        else:
            self.successes.append(f"✅ Found Docker Compose file")
        
        # Check brain directory exists
        brain_dir = 'brain'
        if not os.path.exists(brain_dir):
            self.issues.append(f"❌ Missing brain directory: {brain_dir}")
            all_valid = False
        else:
            self.successes.append(f"✅ Found brain directory")
        
        # Check brain Dockerfile exists
        brain_dockerfile = 'brain/Dockerfile'
        if not os.path.exists(brain_dockerfile):
            self.issues.append(f"❌ Missing brain Dockerfile: {brain_dockerfile}")
            all_valid = False
        else:
            self.successes.append(f"✅ Found brain Dockerfile")
        
        return all_valid
    
    def validate_api_keys_format(self) -> bool:
        """Validate API keys format"""
        
        print("\n🔑 VALIDATING API KEYS FORMAT...")
        
        all_valid = True
        
        # Check DeepSeek API key format
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        if deepseek_key and deepseek_key != 'your_deepseek_api_key_here':
            if not deepseek_key.startswith('sk-'):
                self.warnings.append("⚠️ DeepSeek API key should start with 'sk-'")
            else:
                self.successes.append("✅ DeepSeek API key format looks correct")
        
        # Check Solana wallet private key format
        wallet_key = os.getenv('SOLANA_WALLET_PRIVATE_KEY')
        if wallet_key and wallet_key != 'your_64_byte_private_key_here':
            try:
                # Should be 64 bytes when decoded from base58 or hex
                if len(wallet_key) not in [64, 88, 128]:  # Different encoding lengths
                    self.warnings.append("⚠️ Solana wallet private key length seems incorrect")
                else:
                    self.successes.append("✅ Solana wallet private key length looks correct")
            except:
                self.warnings.append("⚠️ Could not validate Solana wallet private key format")
        
        # Check Helius API key format
        helius_key = os.getenv('HELIUS_API_KEY')
        if helius_key and helius_key != 'your_helius_api_key_here':
            if len(helius_key) != 36:  # UUID format
                self.warnings.append("⚠️ Helius API key should be 36 characters (UUID format)")
            else:
                self.successes.append("✅ Helius API key format looks correct")
        
        return all_valid
    
    def validate_compilation(self) -> bool:
        """Validate Rust compilation"""
        
        print("\n🦀 VALIDATING RUST COMPILATION...")
        
        try:
            result = subprocess.run(['cargo', 'check', '--quiet'], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                self.successes.append("✅ Rust code compiles successfully")
                return True
            else:
                self.issues.append(f"❌ Rust compilation failed: {result.stderr}")
                return False
        except Exception as e:
            self.issues.append(f"❌ Could not check Rust compilation: {e}")
            return False
    
    def validate_git_status(self) -> bool:
        """Validate git status"""
        
        print("\n📝 VALIDATING GIT STATUS...")
        
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd='.')
            
            if result.returncode != 0:
                self.warnings.append("⚠️ Not in a git repository or git not available")
                return True
            
            # Check for uncommitted changes
            if result.stdout.strip():
                self.warnings.append("⚠️ Uncommitted changes detected - will be committed during deployment")
            else:
                self.successes.append("✅ No uncommitted changes")
            
            return True
            
        except Exception as e:
            self.warnings.append(f"⚠️ Could not check git status: {e}")
            return True
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation"""
        
        print("🔍 Running comprehensive deployment validation...")
        
        # Run all validations
        env_valid = self.validate_environment_variables()
        docker_valid = self.validate_docker_configuration()
        api_valid = self.validate_api_keys_format()
        compile_valid = self.validate_compilation()
        git_valid = self.validate_git_status()
        
        # Calculate overall status
        critical_valid = env_valid and docker_valid and compile_valid
        overall_valid = critical_valid and api_valid and git_valid
        
        # Display results
        print("\n" + "=" * 60)
        print("🎯 VALIDATION RESULTS")
        print("=" * 60)
        
        # Display successes
        if self.successes:
            print(f"\n✅ SUCCESSES ({len(self.successes)}):")
            for success in self.successes:
                print(f"   {success}")
        
        # Display warnings
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Display issues
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   {issue}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if critical_valid:
            if overall_valid:
                print("   ✅ READY FOR DEPLOYMENT")
                print("   🚀 All critical requirements met")
            else:
                print("   ⚠️ READY WITH WARNINGS")
                print("   🔧 Address warnings for optimal deployment")
        else:
            print("   ❌ NOT READY FOR DEPLOYMENT")
            print("   🛠️ Fix critical issues before deploying")
        
        # Recommendations
        print(f"\n📋 RECOMMENDATIONS:")
        if not critical_valid:
            print("   1. Fix all critical issues listed above")
            print("   2. Re-run validation: python3 validate_deployment_config.py")
            print("   3. Then proceed with deployment")
        else:
            print("   1. Review and address any warnings")
            print("   2. Proceed with deployment: ./deploy_to_server.sh")
            print("   3. Monitor deployment logs for any issues")
        
        print("=" * 60)
        
        return {
            'overall_valid': overall_valid,
            'critical_valid': critical_valid,
            'successes': len(self.successes),
            'warnings': len(self.warnings),
            'issues': len(self.issues),
            'ready_for_deployment': critical_valid
        }

def main():
    """Main validation function"""
    
    # Load environment from .env.production if it exists
    env_file = '.env.production'
    if os.path.exists(env_file):
        print(f"📁 Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if not os.getenv(key):  # Don't override existing env vars
                        os.environ[key] = value
    
    validator = DeploymentConfigValidator()
    results = validator.run_full_validation()
    
    return results

if __name__ == "__main__":
    main()
