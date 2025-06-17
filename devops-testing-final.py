#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Final DevOps Testing Suite
Production readiness validation focusing on what we can test without full deployment

This suite answers: "Is our system not only intelligent and fast, 
but also bulletproof, fault-tolerant, and manageable under production conditions?"
"""

import asyncio
import json
import time
import os
import subprocess
import urllib.request
import urllib.error
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    category: str
    status: str  # PASS, FAIL, WARN, SKIP
    duration: float
    details: str
    metrics: Dict = field(default_factory=dict)
    timestamp: Optional[datetime] = None

class FinalDevOpsTestSuite:
    """Final DevOps testing suite for THE OVERMIND PROTOCOL"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        
    def print_test_header(self, category: str, test_name: str):
        """Print formatted test header"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 🧪 {category} - {test_name}")
        print("=" * 80)
    
    def print_test_result(self, result: TestResult):
        """Print formatted test result"""
        status_icons = {
            'PASS': '✅',
            'FAIL': '❌', 
            'WARN': '⚠️',
            'SKIP': '⏭️'
        }
        icon = status_icons.get(result.status, '❓')
        print(f"{icon} {result.test_name}: {result.status} ({result.duration:.2f}s)")
        if result.details:
            print(f"   Details: {result.details}")
        if result.metrics:
            for key, value in result.metrics.items():
                print(f"   {key}: {value}")
    
    def record_result(self, test_name: str, category: str, status: str, 
                     duration: float, details: str = "", metrics: Optional[Dict] = None):
        """Record test result"""
        result = TestResult(
            test_name=test_name,
            category=category,
            status=status,
            duration=duration,
            details=details,
            metrics=metrics or {},
            timestamp=datetime.now()
        )
        self.results.append(result)
        self.print_test_result(result)
        return result
    
    async def test_infrastructure_readiness(self) -> List[TestResult]:
        """Test infrastructure readiness without requiring running services"""
        self.print_test_header("INFRASTRUCTURE", "Infrastructure Readiness Assessment")
        
        results = []
        
        # Test 1: Docker availability and configuration
        start_time = time.time()
        try:
            # Check Docker
            docker_result = subprocess.run(['docker', '--version'], 
                                         capture_output=True, text=True, timeout=10)
            
            if docker_result.returncode == 0:
                docker_version = docker_result.stdout.strip()
                
                # Check Docker Compose
                compose_result = subprocess.run(['docker-compose', '--version'], 
                                              capture_output=True, text=True, timeout=10)
                
                if compose_result.returncode == 0:
                    compose_version = compose_result.stdout.strip()
                    status = "PASS"
                    details = f"Docker and Compose ready: {docker_version}, {compose_version}"
                else:
                    status = "WARN"
                    details = f"Docker available but Compose missing: {docker_version}"
            else:
                status = "FAIL"
                details = "Docker not available"
            
            duration = time.time() - start_time
            results.append(self.record_result(
                "Docker Infrastructure", "Infrastructure", status, duration, details
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Docker Infrastructure", "Infrastructure", "FAIL", duration, str(e)
            ))
        
        # Test 2: System resources assessment
        start_time = time.time()
        try:
            # Check available memory
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            mem_total = None
            mem_available = None
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) // 1024  # Convert to MB
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) // 1024  # Convert to MB
            
            # Check CPU cores
            cpu_cores = os.cpu_count()
            
            # Check disk space
            disk_usage = shutil.disk_usage('/')
            disk_free_gb = disk_usage.free // (1024**3)
            
            duration = time.time() - start_time
            
            # Assess resource adequacy for THE OVERMIND PROTOCOL
            resource_issues = []
            if mem_total and mem_total < 8000:  # Less than 8GB
                resource_issues.append(f"Low memory: {mem_total}MB (recommend 16GB+)")
            if cpu_cores < 4:
                resource_issues.append(f"Low CPU cores: {cpu_cores} (recommend 8+)")
            if disk_free_gb < 20:
                resource_issues.append(f"Low disk space: {disk_free_gb}GB (recommend 50GB+)")
            
            if not resource_issues:
                status = "PASS"
                details = f"Adequate resources: {mem_total}MB RAM, {cpu_cores} cores, {disk_free_gb}GB free"
            elif len(resource_issues) == 1:
                status = "WARN"
                details = f"Resource concern: {resource_issues[0]}"
            else:
                status = "FAIL"
                details = f"Multiple resource issues: {'; '.join(resource_issues)}"
            
            results.append(self.record_result(
                "System Resources", "Infrastructure", status, duration, details,
                {"memory_mb": mem_total, "cpu_cores": cpu_cores, "disk_free_gb": disk_free_gb}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "System Resources", "Infrastructure", "FAIL", duration, str(e)
            ))
        
        return results
    
    async def test_configuration_completeness(self) -> List[TestResult]:
        """Test configuration completeness and validity"""
        self.print_test_header("CONFIGURATION", "Configuration Completeness Assessment")
        
        results = []
        
        # Test 1: Critical files presence and validity
        start_time = time.time()
        try:
            critical_files = {
                '.env': 'Environment configuration',
                'docker-compose.overmind.yml': 'Main deployment configuration',
                'docker-compose.overmind-simple.yml': 'Simplified deployment configuration',
                'Cargo.toml': 'Rust project configuration',
                'pixi.toml': 'Python environment configuration',
                'brain/Dockerfile': 'AI Brain container configuration',
                'Dockerfile': 'Main executor container configuration'
            }
            
            file_status = {}
            for file_path, description in critical_files.items():
                if os.path.exists(file_path):
                    # Check if file is readable and non-empty
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().strip()
                        if content:
                            file_status[file_path] = "valid"
                        else:
                            file_status[file_path] = "empty"
                    except Exception:
                        file_status[file_path] = "unreadable"
                else:
                    file_status[file_path] = "missing"
            
            valid_files = sum(1 for status in file_status.values() if status == "valid")
            total_files = len(critical_files)
            
            duration = time.time() - start_time
            file_rate = (valid_files / total_files) * 100
            
            if file_rate >= 90:
                status = "PASS"
                details = f"Configuration complete: {valid_files}/{total_files} files valid"
            elif file_rate >= 75:
                status = "WARN"
                details = f"Most configuration ready: {valid_files}/{total_files} files valid"
            else:
                status = "FAIL"
                details = f"Configuration incomplete: {valid_files}/{total_files} files valid"
            
            results.append(self.record_result(
                "Configuration Files", "Configuration", status, duration, details,
                {"file_rate": f"{file_rate:.1f}%", "valid_files": valid_files}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Configuration Files", "Configuration", "FAIL", duration, str(e)
            ))
        
        # Test 2: Environment variables completeness
        start_time = time.time()
        try:
            required_env_vars = {
                'SNIPER_SOLANA_RPC_URL': 'Solana RPC endpoint',
                'SNIPER_WALLET_PRIVATE_KEY': 'Trading wallet private key',
                'OPENAI_API_KEY': 'OpenAI API access',
                'OVERMIND_MULTI_WALLET_ENABLED': 'Multi-wallet feature flag'
            }
            
            optional_env_vars = {
                'GROQ_API_KEY': 'Groq API access',
                'MISTRAL_API_KEY': 'Mistral API access',
                'GOOGLE_API_KEY': 'Google API access',
                'PERPLEXITY_API_KEY': 'Perplexity API access'
            }
            
            configured_required = 0
            configured_optional = 0
            
            for var, description in required_env_vars.items():
                value = os.getenv(var)
                if value and value.strip() and not value.startswith('your-') and value != 'placeholder':
                    configured_required += 1
            
            for var, description in optional_env_vars.items():
                value = os.getenv(var)
                if value and value.strip() and not value.startswith('your-') and value != 'placeholder':
                    configured_optional += 1
            
            duration = time.time() - start_time
            required_rate = (configured_required / len(required_env_vars)) * 100
            
            if required_rate >= 100:
                status = "PASS"
                details = f"Environment complete: {configured_required}/{len(required_env_vars)} required, {configured_optional}/{len(optional_env_vars)} optional"
            elif required_rate >= 75:
                status = "WARN"
                details = f"Most environment ready: {configured_required}/{len(required_env_vars)} required vars configured"
            else:
                status = "FAIL"
                details = f"Environment incomplete: {configured_required}/{len(required_env_vars)} required vars configured"
            
            results.append(self.record_result(
                "Environment Variables", "Configuration", status, duration, details,
                {"required_rate": f"{required_rate:.1f}%", "optional_configured": configured_optional}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Environment Variables", "Configuration", "FAIL", duration, str(e)
            ))
        
        return results
    
    async def test_deployment_readiness(self) -> List[TestResult]:
        """Test deployment scripts and procedures readiness"""
        self.print_test_header("DEPLOYMENT", "Deployment Readiness Assessment")
        
        results = []
        
        # Test 1: Deployment scripts availability and executability
        start_time = time.time()
        try:
            deployment_scripts = {
                'deploy-overmind.sh': 'Main deployment script',
                'complete-vds-upgrade.sh': 'VDS upgrade completion script',
                'verify-32gb-upgrade.sh': 'Upgrade verification script',
                'fix-devops-critical-issues.sh': 'DevOps issues fix script',
                'quick-devops-fix.sh': 'Quick infrastructure fix script'
            }
            
            script_status = {}
            for script, description in deployment_scripts.items():
                if os.path.exists(script):
                    if os.access(script, os.X_OK):
                        script_status[script] = "executable"
                    else:
                        script_status[script] = "not_executable"
                else:
                    script_status[script] = "missing"
            
            executable_scripts = sum(1 for status in script_status.values() if status == "executable")
            total_scripts = len(deployment_scripts)
            
            duration = time.time() - start_time
            script_rate = (executable_scripts / total_scripts) * 100
            
            if script_rate >= 90:
                status = "PASS"
                details = f"Deployment ready: {executable_scripts}/{total_scripts} scripts executable"
            elif script_rate >= 70:
                status = "WARN"
                details = f"Most deployment ready: {executable_scripts}/{total_scripts} scripts executable"
            else:
                status = "FAIL"
                details = f"Deployment not ready: {executable_scripts}/{total_scripts} scripts executable"
            
            results.append(self.record_result(
                "Deployment Scripts", "Deployment", status, duration, details,
                {"script_rate": f"{script_rate:.1f}%"}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Deployment Scripts", "Deployment", "FAIL", duration, str(e)
            ))
        
        return results
    
    async def test_security_configuration(self) -> List[TestResult]:
        """Test security configuration and hardening"""
        self.print_test_header("SECURITY", "Security Configuration Assessment")
        
        results = []
        
        # Test 1: File permissions and security
        start_time = time.time()
        try:
            sensitive_files = ['.env', 'wallets/', 'private_keys/']
            permission_issues = []
            
            for file_path in sensitive_files:
                if os.path.exists(file_path):
                    stat_info = os.stat(file_path)
                    permissions = oct(stat_info.st_mode)[-3:]
                    
                    # Check for world-readable permissions
                    if permissions[-1] in ['4', '5', '6', '7']:
                        permission_issues.append(f"{file_path}: world-readable ({permissions})")
            
            duration = time.time() - start_time
            
            if not permission_issues:
                status = "PASS"
                details = "File permissions properly secured"
            elif len(permission_issues) <= 1:
                status = "WARN"
                details = f"Minor permission issue: {permission_issues[0]}"
            else:
                status = "FAIL"
                details = f"Multiple permission issues: {len(permission_issues)} problems"
            
            results.append(self.record_result(
                "File Permissions", "Security", status, duration, details,
                {"issues_found": len(permission_issues)}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "File Permissions", "Security", "FAIL", duration, str(e)
            ))
        
        return results
    
    def generate_final_report(self) -> Dict:
        """Generate final DevOps assessment report"""
        
        # Categorize results
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == "PASS")
        failed_tests = sum(1 for r in self.results if r.status == "FAIL")
        warning_tests = sum(1 for r in self.results if r.status == "WARN")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warning_tests,
                'success_rate': success_rate,
                'total_duration': sum(r.duration for r in self.results)
            },
            'categories': {},
            'critical_issues': [],
            'recommendations': [],
            'production_readiness_score': 0,
            'devops_assessment': ''
        }
        
        # Analyze by category
        for category, results in categories.items():
            category_passed = sum(1 for r in results if r.status == "PASS")
            category_total = len(results)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            report['categories'][category] = {
                'total_tests': category_total,
                'passed': category_passed,
                'failed': sum(1 for r in results if r.status == "FAIL"),
                'warnings': sum(1 for r in results if r.status == "WARN"),
                'success_rate': category_rate,
                'tests': [
                    {
                        'name': r.test_name,
                        'status': r.status,
                        'duration': r.duration,
                        'details': r.details,
                        'metrics': r.metrics
                    } for r in results
                ]
            }
            
            # Identify critical issues
            for result in results:
                if result.status == "FAIL":
                    report['critical_issues'].append({
                        'category': category,
                        'test': result.test_name,
                        'issue': result.details
                    })
        
        # Calculate production readiness score
        weights = {
            'Infrastructure': 0.30,
            'Configuration': 0.30,
            'Deployment': 0.25,
            'Security': 0.15
        }
        
        weighted_score = 0
        for category, weight in weights.items():
            if category in report['categories']:
                category_score = report['categories'][category]['success_rate']
                weighted_score += category_score * weight
        
        report['production_readiness_score'] = weighted_score
        
        # Generate assessment
        if report['production_readiness_score'] >= 90:
            report['devops_assessment'] = "✅ EXCELLENT - System demonstrates strong DevOps readiness for production"
            report['recommendations'].append("System is well-prepared for production deployment")
        elif report['production_readiness_score'] >= 80:
            report['devops_assessment'] = "⚠️ GOOD - System is mostly ready with minor DevOps improvements needed"
            report['recommendations'].append("Address warnings to improve operational reliability")
        elif report['production_readiness_score'] >= 70:
            report['devops_assessment'] = "🔧 FAIR - System needs significant DevOps improvements before production"
            report['recommendations'].append("Focus on infrastructure and configuration improvements")
        else:
            report['devops_assessment'] = "❌ POOR - System requires major DevOps work before production deployment"
            report['recommendations'].append("Critical DevOps issues must be resolved before production")
        
        # Add specific recommendations
        if failed_tests > 0:
            report['recommendations'].append(f"🚨 Resolve {failed_tests} critical failures")
        if warning_tests > 2:
            report['recommendations'].append(f"⚠️ Address {warning_tests} warnings")
        
        return report
    
    async def run_final_devops_assessment(self) -> Dict:
        """Run final DevOps assessment"""
        
        print("🧠 THE OVERMIND PROTOCOL - Final DevOps Assessment")
        print("=" * 80)
        print(f"Assessment Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Evaluating production readiness from DevOps perspective...")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Run all assessment categories
        test_categories = [
            ("Infrastructure Readiness", self.test_infrastructure_readiness),
            ("Configuration Completeness", self.test_configuration_completeness),
            ("Deployment Readiness", self.test_deployment_readiness),
            ("Security Configuration", self.test_security_configuration)
        ]
        
        for category_name, test_method in test_categories:
            try:
                print(f"\n🔍 Assessing {category_name}...")
                await test_method()
            except Exception as e:
                logger.error(f"Failed to assess {category_name}: {e}")
                self.record_result(
                    f"{category_name} Assessment", category_name, "FAIL", 0, str(e)
                )
        
        # Generate final report
        report = self.generate_final_report()
        
        # Print summary
        print(f"\n📊 Final DevOps Assessment Summary:")
        print("=" * 50)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']} ✅")
        print(f"Failed: {report['summary']['failed']} ❌")
        print(f"Warnings: {report['summary']['warnings']} ⚠️")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Production Readiness Score: {report['production_readiness_score']:.1f}%")
        
        # Print assessment
        print(f"\n🎯 DevOps Assessment:")
        print(f"  {report['devops_assessment']}")
        
        # Print category breakdown
        print(f"\n📋 Category Breakdown:")
        for category, data in report['categories'].items():
            print(f"  {category}: {data['passed']}/{data['total_tests']} ({data['success_rate']:.1f}%)")
        
        # Print critical issues
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues ({len(report['critical_issues'])}):")
            for issue in report['critical_issues']:
                print(f"  • {issue['category']} - {issue['test']}: {issue['issue']}")
        
        # Print recommendations
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print(f"\n🏁 DevOps Assessment Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return report


async def main():
    """Main execution function"""
    tester = FinalDevOpsTestSuite()
    
    try:
        # Run final DevOps assessment
        report = await tester.run_final_devops_assessment()
        
        # Save report
        with open('final-devops-assessment.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Assessment report saved to: final-devops-assessment.json")
        
        # Return exit code based on results
        if report['production_readiness_score'] >= 90:
            print("🎉 THE OVERMIND PROTOCOL demonstrates excellent DevOps readiness!")
            return 0
        elif report['production_readiness_score'] >= 80:
            print("⚠️ THE OVERMIND PROTOCOL shows good DevOps readiness with minor improvements needed")
            return 1
        else:
            print("❌ THE OVERMIND PROTOCOL needs significant DevOps improvements before production")
            return 2
            
    except Exception as e:
        logger.error(f"DevOps assessment failed: {e}")
        return 3


if __name__ == "__main__":
    import sys
    
    # Run the final DevOps assessment
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
