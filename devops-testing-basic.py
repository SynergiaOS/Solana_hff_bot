#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Basic DevOps Testing Suite
Production readiness validation using only standard library

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

class BasicDevOpsTestSuite:
    """Basic DevOps testing suite for THE OVERMIND PROTOCOL"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.test_environment = {
            'compose_file': 'docker-compose.overmind.yml',
            'endpoints': {
                'executor': 'http://localhost:8080',
                'brain': 'http://localhost:8001',
                'chroma': 'http://localhost:8000',
                'tensorzero': 'http://localhost:3000',
                'prometheus': 'http://localhost:9090',
                'grafana': 'http://localhost:3001'
            }
        }
        
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
    
    def check_url_health(self, url: str, timeout: int = 10) -> tuple[bool, str]:
        """Check if URL is accessible and healthy"""
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                if status_code == 200:
                    return True, f"HTTP {status_code}"
                else:
                    return False, f"HTTP {status_code}"
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            return False, f"Connection error: {e.reason}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    async def test_infrastructure_basic(self) -> List[TestResult]:
        """Test basic infrastructure components"""
        self.print_test_header("INFRASTRUCTURE", "Basic Infrastructure Tests")
        
        results = []
        
        # Test 1: Docker availability
        start_time = time.time()
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                docker_version = result.stdout.strip()
                status = "PASS"
                details = f"Docker available: {docker_version}"
            else:
                status = "FAIL"
                details = "Docker not available or not working"
            
            duration = time.time() - start_time
            results.append(self.record_result(
                "Docker Availability", "Infrastructure", status, duration, details
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Docker Availability", "Infrastructure", "FAIL", duration, str(e)
            ))
        
        # Test 2: Docker Compose availability
        start_time = time.time()
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                compose_version = result.stdout.strip()
                status = "PASS"
                details = f"Docker Compose available: {compose_version}"
            else:
                status = "FAIL"
                details = "Docker Compose not available"
            
            duration = time.time() - start_time
            results.append(self.record_result(
                "Docker Compose Availability", "Infrastructure", status, duration, details
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Docker Compose Availability", "Infrastructure", "FAIL", duration, str(e)
            ))
        
        # Test 3: Service health checks
        start_time = time.time()
        try:
            healthy_services = 0
            total_services = len(self.test_environment['endpoints'])
            
            for service_name, url in self.test_environment['endpoints'].items():
                health_url = f"{url}/health" if not url.endswith('/health') else url
                is_healthy, health_details = self.check_url_health(health_url, timeout=5)
                
                if is_healthy:
                    healthy_services += 1
                    logger.info(f"Service {service_name}: {health_details}")
                else:
                    logger.warning(f"Service {service_name}: {health_details}")
            
            duration = time.time() - start_time
            health_rate = (healthy_services / total_services) * 100
            
            if health_rate >= 80:
                status = "PASS"
                details = f"Service health good: {healthy_services}/{total_services} services healthy"
            elif health_rate >= 60:
                status = "WARN"
                details = f"Some service issues: {healthy_services}/{total_services} services healthy"
            else:
                status = "FAIL"
                details = f"Poor service health: {healthy_services}/{total_services} services healthy"
            
            results.append(self.record_result(
                "Service Health Checks", "Infrastructure", status, duration, details,
                {"health_rate": f"{health_rate:.1f}%", "healthy_services": healthy_services}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Service Health Checks", "Infrastructure", "FAIL", duration, str(e)
            ))
        
        return results
    
    async def test_configuration_management(self) -> List[TestResult]:
        """Test configuration and deployment readiness"""
        self.print_test_header("CONFIGURATION", "Configuration Management Tests")
        
        results = []
        
        # Test 1: Critical files existence
        start_time = time.time()
        try:
            critical_files = [
                '.env',
                'docker-compose.overmind.yml',
                'deploy-overmind.sh',
                'pixi.toml',
                'Cargo.toml'
            ]
            
            existing_files = 0
            for file_path in critical_files:
                if os.path.exists(file_path):
                    existing_files += 1
                    logger.info(f"Found critical file: {file_path}")
                else:
                    logger.warning(f"Missing critical file: {file_path}")
            
            duration = time.time() - start_time
            file_rate = (existing_files / len(critical_files)) * 100
            
            if file_rate >= 90:
                status = "PASS"
                details = f"All critical files present: {existing_files}/{len(critical_files)}"
            elif file_rate >= 70:
                status = "WARN"
                details = f"Most critical files present: {existing_files}/{len(critical_files)}"
            else:
                status = "FAIL"
                details = f"Missing critical files: {existing_files}/{len(critical_files)}"
            
            results.append(self.record_result(
                "Critical Files Check", "Configuration", status, duration, details,
                {"file_rate": f"{file_rate:.1f}%"}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Critical Files Check", "Configuration", "FAIL", duration, str(e)
            ))
        
        # Test 2: Environment variables validation
        start_time = time.time()
        try:
            required_env_vars = [
                'SNIPER_SOLANA_RPC_URL',
                'SNIPER_WALLET_PRIVATE_KEY',
                'OPENAI_API_KEY'
            ]
            
            configured_vars = 0
            for var in required_env_vars:
                value = os.getenv(var)
                if value and value.strip() and not value.startswith('your-'):
                    configured_vars += 1
                    logger.info(f"Environment variable {var}: configured")
                else:
                    logger.warning(f"Environment variable {var}: not configured or placeholder")
            
            duration = time.time() - start_time
            config_rate = (configured_vars / len(required_env_vars)) * 100
            
            if config_rate >= 100:
                status = "PASS"
                details = f"All environment variables configured: {configured_vars}/{len(required_env_vars)}"
            elif config_rate >= 70:
                status = "WARN"
                details = f"Most environment variables configured: {configured_vars}/{len(required_env_vars)}"
            else:
                status = "FAIL"
                details = f"Missing environment variables: {configured_vars}/{len(required_env_vars)}"
            
            results.append(self.record_result(
                "Environment Variables", "Configuration", status, duration, details,
                {"config_rate": f"{config_rate:.1f}%"}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Environment Variables", "Configuration", "FAIL", duration, str(e)
            ))
        
        return results

    async def test_deployment_readiness(self) -> List[TestResult]:
        """Test deployment scripts and procedures"""
        self.print_test_header("DEPLOYMENT", "Deployment Readiness Tests")

        results = []

        # Test 1: Deployment scripts validation
        start_time = time.time()
        try:
            deployment_scripts = [
                'deploy-overmind.sh',
                'complete-vds-upgrade.sh',
                'verify-32gb-upgrade.sh'
            ]

            executable_scripts = 0
            for script in deployment_scripts:
                if os.path.exists(script):
                    if os.access(script, os.X_OK):
                        executable_scripts += 1
                        logger.info(f"Deployment script ready: {script}")
                    else:
                        logger.warning(f"Deployment script not executable: {script}")
                else:
                    logger.warning(f"Deployment script missing: {script}")

            duration = time.time() - start_time
            script_rate = (executable_scripts / len(deployment_scripts)) * 100

            if script_rate >= 90:
                status = "PASS"
                details = f"Deployment scripts ready: {executable_scripts}/{len(deployment_scripts)}"
            elif script_rate >= 70:
                status = "WARN"
                details = f"Most deployment scripts ready: {executable_scripts}/{len(deployment_scripts)}"
            else:
                status = "FAIL"
                details = f"Deployment scripts not ready: {executable_scripts}/{len(deployment_scripts)}"

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

    async def test_monitoring_basic(self) -> List[TestResult]:
        """Test basic monitoring capabilities"""
        self.print_test_header("MONITORING", "Basic Monitoring Tests")

        results = []

        # Test 1: Prometheus accessibility
        start_time = time.time()
        try:
            prometheus_url = self.test_environment['endpoints']['prometheus']
            is_accessible, details = self.check_url_health(prometheus_url)

            duration = time.time() - start_time

            if is_accessible:
                status = "PASS"
                details = f"Prometheus accessible: {details}"
            else:
                status = "FAIL"
                details = f"Prometheus not accessible: {details}"

            results.append(self.record_result(
                "Prometheus Accessibility", "Monitoring", status, duration, details
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Prometheus Accessibility", "Monitoring", "FAIL", duration, str(e)
            ))

        # Test 2: Grafana accessibility
        start_time = time.time()
        try:
            grafana_url = self.test_environment['endpoints']['grafana']
            is_accessible, details = self.check_url_health(grafana_url)

            duration = time.time() - start_time

            if is_accessible:
                status = "PASS"
                details = f"Grafana accessible: {details}"
            else:
                status = "WARN"  # Grafana might not be critical for basic operation
                details = f"Grafana not accessible: {details}"

            results.append(self.record_result(
                "Grafana Accessibility", "Monitoring", status, duration, details
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Grafana Accessibility", "Monitoring", "FAIL", duration, str(e)
            ))

        return results

    async def test_security_basic(self) -> List[TestResult]:
        """Test basic security measures"""
        self.print_test_header("SECURITY", "Basic Security Tests")

        results = []

        # Test 1: File permissions check
        start_time = time.time()
        try:
            sensitive_files = [
                '.env',
                'wallets/',
                'private_keys/'
            ]

            permission_issues = []
            for file_path in sensitive_files:
                if os.path.exists(file_path):
                    # Check if file/directory is world-readable
                    stat_info = os.stat(file_path)
                    permissions = oct(stat_info.st_mode)[-3:]

                    # Check for world-readable permissions (last digit should not be 4, 5, 6, 7)
                    if permissions[-1] in ['4', '5', '6', '7']:
                        permission_issues.append(f"{file_path}: world-readable ({permissions})")

            duration = time.time() - start_time

            if not permission_issues:
                status = "PASS"
                details = "No obvious file permission issues found"
            elif len(permission_issues) <= 1:
                status = "WARN"
                details = f"Minor permission concerns: {'; '.join(permission_issues)}"
            else:
                status = "FAIL"
                details = f"Multiple permission issues: {len(permission_issues)} problems"

            results.append(self.record_result(
                "File Permissions Check", "Security", status, duration, details,
                {"issues_found": len(permission_issues)}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "File Permissions Check", "Security", "FAIL", duration, str(e)
            ))

        return results

    def generate_basic_report(self) -> Dict:
        """Generate basic DevOps testing report"""

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
            'production_readiness_assessment': ''
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

        # Generate assessment and recommendations
        if success_rate >= 90:
            report['production_readiness_assessment'] = "✅ EXCELLENT - System shows strong DevOps readiness"
            report['recommendations'].append("System demonstrates good DevOps practices and operational readiness")
        elif success_rate >= 80:
            report['production_readiness_assessment'] = "⚠️ GOOD - Minor DevOps improvements needed"
            report['recommendations'].append("Address warnings to improve operational reliability")
        elif success_rate >= 70:
            report['production_readiness_assessment'] = "🔧 FAIR - Significant DevOps improvements needed"
            report['recommendations'].append("Focus on infrastructure and deployment improvements")
        else:
            report['production_readiness_assessment'] = "❌ POOR - Major DevOps issues must be resolved"
            report['recommendations'].append("Critical DevOps issues require immediate attention")

        # Add specific recommendations
        if failed_tests > 0:
            report['recommendations'].append(f"🚨 Resolve {failed_tests} critical failures before production")
        if warning_tests > 2:
            report['recommendations'].append(f"⚠️ Review {warning_tests} warnings for potential issues")

        # Infrastructure-specific recommendations
        infra_category = report['categories'].get('Infrastructure', {})
        if infra_category.get('success_rate', 0) < 80:
            report['recommendations'].append("🏗️ Strengthen infrastructure monitoring and health checks")

        # Configuration-specific recommendations
        config_category = report['categories'].get('Configuration', {})
        if config_category.get('success_rate', 0) < 90:
            report['recommendations'].append("⚙️ Complete configuration management setup")

        return report

    async def run_basic_devops_tests(self) -> Dict:
        """Run basic DevOps tests and generate report"""

        print("🧠 THE OVERMIND PROTOCOL - Basic DevOps Testing Suite")
        print("=" * 80)
        print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Testing production readiness with basic DevOps validation...")
        print("=" * 80)

        self.start_time = time.time()

        # Run all test categories
        test_categories = [
            ("Infrastructure", self.test_infrastructure_basic),
            ("Configuration", self.test_configuration_management),
            ("Deployment", self.test_deployment_readiness),
            ("Monitoring", self.test_monitoring_basic),
            ("Security", self.test_security_basic)
        ]

        for category_name, test_method in test_categories:
            try:
                print(f"\n🔍 Running {category_name} tests...")
                await test_method()
            except Exception as e:
                logger.error(f"Failed to run {category_name} tests: {e}")
                self.record_result(
                    f"{category_name} Test Suite", category_name, "FAIL", 0, str(e)
                )

        # Generate report
        report = self.generate_basic_report()

        # Print summary
        print(f"\n📊 Basic DevOps Testing Summary:")
        print("=" * 50)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']} ✅")
        print(f"Failed: {report['summary']['failed']} ❌")
        print(f"Warnings: {report['summary']['warnings']} ⚠️")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Total Duration: {report['summary']['total_duration']:.1f}s")

        # Print category breakdown
        print(f"\n📋 Category Breakdown:")
        for category, data in report['categories'].items():
            print(f"  {category}: {data['passed']}/{data['total_tests']} ({data['success_rate']:.1f}%)")

        # Print assessment
        print(f"\n🎯 Production Readiness Assessment:")
        print(f"  {report['production_readiness_assessment']}")

        # Print critical issues
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues ({len(report['critical_issues'])}):")
            for issue in report['critical_issues']:
                print(f"  • {issue['category']} - {issue['test']}: {issue['issue']}")

        # Print recommendations
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")

        print(f"\n🏁 Basic DevOps Testing Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return report


async def main():
    """Main execution function"""
    tester = BasicDevOpsTestSuite()

    try:
        # Run basic DevOps testing
        report = await tester.run_basic_devops_tests()

        # Save report
        with open('basic-devops-report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n💾 Report saved to: basic-devops-report.json")

        # Return exit code based on results
        if report['summary']['success_rate'] >= 90:
            print("🎉 THE OVERMIND PROTOCOL shows excellent DevOps readiness!")
            return 0
        elif report['summary']['success_rate'] >= 80:
            print("⚠️ THE OVERMIND PROTOCOL shows good DevOps readiness with minor issues")
            return 1
        else:
            print("❌ THE OVERMIND PROTOCOL needs DevOps improvements before production")
            return 2

    except Exception as e:
        logger.error(f"Basic DevOps testing failed: {e}")
        return 3


if __name__ == "__main__":
    import sys

    # Run the basic DevOps testing suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
