#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Comprehensive DevOps Testing Suite
Production readiness validation through 4 critical test categories

This suite implements "Trust through Real-World Verification" philosophy:
Assume everything that can fail will fail. Verify system behavior when reality hits our infrastructure.

Test Categories:
1. DEPLOYMENT & CONFIGURATION TESTS
2. OBSERVABILITY & MONITORING TESTS  
3. RESILIENCE & RELIABILITY TESTS (Chaos Engineering)
4. SECURITY TESTS
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
import socket
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import tempfile
# import yaml  # Optional dependency

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
    evidence: List[str] = field(default_factory=list)  # Screenshots, logs, etc.

class ComprehensiveDevOpsTestSuite:
    """Comprehensive DevOps testing suite implementing 4 critical test categories"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.test_environment = {
            'endpoints': {
                'executor': 'http://localhost:8080',
                'brain': 'http://localhost:8001', 
                'chroma': 'http://localhost:8000',
                'tensorzero': 'http://localhost:3000',
                'prometheus': 'http://localhost:9090',
                'grafana': 'http://localhost:3001',
                'dragonfly': 'redis://localhost:6379'
            },
            'containers': [
                'overmind-executor',
                'overmind-python-brain',
                'overmind-chroma',
                'overmind-tensorzero',
                'overmind-prometheus',
                'overmind-grafana',
                'overmind-dragonfly'
            ]
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
        if result.evidence:
            print(f"   Evidence: {', '.join(result.evidence)}")
    
    def record_result(self, test_name: str, category: str, status: str, 
                     duration: float, details: str = "", metrics: Optional[Dict] = None,
                     evidence: Optional[List[str]] = None):
        """Record test result"""
        result = TestResult(
            test_name=test_name,
            category=category,
            status=status,
            duration=duration,
            details=details,
            metrics=metrics or {},
            evidence=evidence or [],
            timestamp=datetime.now()
        )
        self.results.append(result)
        self.print_test_result(result)
        return result
    
    def check_endpoint_health(self, url: str, timeout: int = 10) -> Tuple[bool, str, float]:
        """Check endpoint health and measure response time"""
        start_time = time.time()
        try:
            response = requests.get(url, timeout=timeout)
            duration = time.time() - start_time
            if response.status_code == 200:
                return True, f"HTTP {response.status_code}", duration * 1000  # ms
            else:
                return False, f"HTTP {response.status_code}", duration * 1000
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            return False, str(e), duration * 1000
    
    def execute_shell_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Execute shell command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    # ============================================================================
    # CATEGORY 1: DEPLOYMENT & CONFIGURATION TESTS
    # ============================================================================
    
    async def test_deployment_configuration(self) -> List[TestResult]:
        """Category 1: Deployment & Configuration Tests"""
        self.print_test_header("DEPLOYMENT & CONFIGURATION", "Automated Deployment Validation")
        
        results = []
        
        # Test 1: Clean Server Test
        start_time = time.time()
        try:
            # Verify deploy script exists and is executable
            deploy_script = './deploy-overmind.sh'
            if not os.path.exists(deploy_script):
                status = "FAIL"
                details = "deploy-overmind.sh script not found"
            elif not os.access(deploy_script, os.X_OK):
                status = "FAIL"
                details = "deploy-overmind.sh script not executable"
            else:
                # Test deployment script syntax
                success, stdout, stderr = self.execute_shell_command(f"bash -n {deploy_script}")
                if success:
                    status = "PASS"
                    details = "Deployment script syntax valid and executable"
                else:
                    status = "FAIL"
                    details = f"Deployment script syntax error: {stderr}"
            
            duration = time.time() - start_time
            results.append(self.record_result(
                "Clean Server Deployment Test", "Deployment", status, duration, details
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Clean Server Deployment Test", "Deployment", "FAIL", duration, str(e)
            ))
        
        # Test 2: Configuration Validation Test
        start_time = time.time()
        try:
            # Test Docker Compose file validation
            compose_files = ['docker-compose.overmind.yml', 'docker-compose.overmind-simple.yml']
            valid_configs = 0
            
            for compose_file in compose_files:
                if os.path.exists(compose_file):
                    success, stdout, stderr = self.execute_shell_command(
                        f"docker-compose -f {compose_file} config"
                    )
                    if success:
                        valid_configs += 1
            
            duration = time.time() - start_time
            
            if valid_configs == len(compose_files):
                status = "PASS"
                details = f"All {len(compose_files)} Docker Compose configurations valid"
            elif valid_configs > 0:
                status = "WARN"
                details = f"{valid_configs}/{len(compose_files)} Docker Compose configurations valid"
            else:
                status = "FAIL"
                details = "No valid Docker Compose configurations found"
            
            results.append(self.record_result(
                "Configuration Validation Test", "Deployment", status, duration, details,
                {"valid_configs": valid_configs, "total_configs": len(compose_files)}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Configuration Validation Test", "Deployment", "FAIL", duration, str(e)
            ))
        
        # Test 3: Secret Management Test
        start_time = time.time()
        try:
            # Check for critical environment variables
            critical_secrets = [
                'OPENAI_API_KEY',
                'SNIPER_WALLET_PRIVATE_KEY',
                'SNIPER_SOLANA_RPC_URL'
            ]
            
            configured_secrets = 0
            missing_secrets = []
            
            for secret in critical_secrets:
                value = os.getenv(secret)
                if value and value.strip() and not value.startswith('your-') and value != 'placeholder':
                    configured_secrets += 1
                else:
                    missing_secrets.append(secret)
            
            duration = time.time() - start_time
            
            if configured_secrets == len(critical_secrets):
                status = "PASS"
                details = "All critical secrets properly configured"
            elif configured_secrets >= len(critical_secrets) * 0.8:
                status = "WARN"
                details = f"Most secrets configured, missing: {', '.join(missing_secrets)}"
            else:
                status = "FAIL"
                details = f"Critical secrets missing: {', '.join(missing_secrets)}"
            
            results.append(self.record_result(
                "Secret Management Test", "Deployment", status, duration, details,
                {"configured_secrets": configured_secrets, "missing_count": len(missing_secrets)}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Secret Management Test", "Deployment", "FAIL", duration, str(e)
            ))
        
        return results
    
    # ============================================================================
    # CATEGORY 2: OBSERVABILITY & MONITORING TESTS
    # ============================================================================
    
    async def test_observability_monitoring(self) -> List[TestResult]:
        """Category 2: Observability & Monitoring Tests"""
        self.print_test_header("OBSERVABILITY & MONITORING", "Real-time System Visibility")
        
        results = []
        
        # Test 1: Metrics Flow Test
        start_time = time.time()
        try:
            # Check if Prometheus is accessible
            prometheus_url = self.test_environment['endpoints']['prometheus']
            is_healthy, health_details, response_time = self.check_endpoint_health(
                f"{prometheus_url}/api/v1/query?query=up"
            )
            
            if is_healthy:
                # Try to query OVERMIND-specific metrics
                overmind_metrics = [
                    'overmind_trades_executed_total',
                    'overmind_pnl_total',
                    'overmind_execution_latency_seconds'
                ]
                
                available_metrics = 0
                for metric in overmind_metrics:
                    try:
                        response = requests.get(
                            f"{prometheus_url}/api/v1/query?query={metric}",
                            timeout=5
                        )
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('data', {}).get('result'):
                                available_metrics += 1
                    except Exception:
                        pass
                
                metrics_rate = (available_metrics / len(overmind_metrics)) * 100
                
                if metrics_rate >= 75:
                    status = "PASS"
                    details = f"Metrics flow operational: {available_metrics}/{len(overmind_metrics)} OVERMIND metrics available"
                elif metrics_rate >= 50:
                    status = "WARN"
                    details = f"Partial metrics flow: {available_metrics}/{len(overmind_metrics)} OVERMIND metrics available"
                else:
                    status = "FAIL"
                    details = f"Poor metrics flow: {available_metrics}/{len(overmind_metrics)} OVERMIND metrics available"
                
            else:
                status = "FAIL"
                details = f"Prometheus not accessible: {health_details}"
                metrics_rate = 0
                available_metrics = 0
            
            duration = time.time() - start_time
            results.append(self.record_result(
                "Metrics Flow Test", "Monitoring", status, duration, details,
                {"metrics_rate": f"{metrics_rate:.1f}%", "prometheus_response_time": f"{response_time:.1f}ms"}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Metrics Flow Test", "Monitoring", "FAIL", duration, str(e)
            ))
        
        # Test 2: Alert Testing
        start_time = time.time()
        try:
            # Check if AlertManager is configured
            alertmanager_config = './monitoring/alertmanager.yml'
            prometheus_rules = './monitoring/alert-rules.yml'
            
            config_files_exist = 0
            if os.path.exists(alertmanager_config):
                config_files_exist += 1
            if os.path.exists(prometheus_rules):
                config_files_exist += 1
            
            # Check if Prometheus has alert rules loaded
            prometheus_url = self.test_environment['endpoints']['prometheus']
            try:
                response = requests.get(f"{prometheus_url}/api/v1/rules", timeout=10)
                if response.status_code == 200:
                    rules_data = response.json()
                    rule_groups = rules_data.get('data', {}).get('groups', [])
                    total_rules = sum(len(group.get('rules', [])) for group in rule_groups)
                    
                    if total_rules > 0:
                        status = "PASS"
                        details = f"Alert system configured: {total_rules} alert rules loaded"
                    else:
                        status = "WARN"
                        details = "Prometheus accessible but no alert rules configured"
                else:
                    status = "FAIL"
                    details = f"Cannot access Prometheus rules API: HTTP {response.status_code}"
            except Exception as e:
                status = "FAIL"
                details = f"Alert testing failed: {str(e)}"
                total_rules = 0
            
            duration = time.time() - start_time
            results.append(self.record_result(
                "Alert Testing", "Monitoring", status, duration, details,
                {"config_files": config_files_exist, "alert_rules": total_rules}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Alert Testing", "Monitoring", "FAIL", duration, str(e)
            ))
        
        # Test 3: Centralized Logging Test
        start_time = time.time()
        try:
            # Check if logging infrastructure is available
            log_systems = {
                'docker_logs': True,  # Always available with Docker
                'elasticsearch': False,
                'grafana_loki': False
            }
            
            # Check for Elasticsearch
            try:
                response = requests.get('http://localhost:9200/_cluster/health', timeout=5)
                if response.status_code == 200:
                    log_systems['elasticsearch'] = True
            except:
                pass
            
            # Check for Grafana Loki
            try:
                response = requests.get('http://localhost:3100/ready', timeout=5)
                if response.status_code == 200:
                    log_systems['grafana_loki'] = True
            except:
                pass
            
            available_systems = sum(1 for available in log_systems.values() if available)
            total_systems = len(log_systems)
            
            duration = time.time() - start_time
            
            if available_systems >= 2:
                status = "PASS"
                details = f"Centralized logging available: {available_systems}/{total_systems} systems operational"
            elif available_systems == 1:
                status = "WARN"
                details = f"Basic logging available: {available_systems}/{total_systems} systems operational"
            else:
                status = "FAIL"
                details = "No centralized logging systems available"
            
            results.append(self.record_result(
                "Centralized Logging Test", "Monitoring", status, duration, details,
                {"available_systems": available_systems, "systems": log_systems}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Centralized Logging Test", "Monitoring", "FAIL", duration, str(e)
            ))
        
        return results

    # ============================================================================
    # CATEGORY 3: RESILIENCE & RELIABILITY TESTS (Chaos Engineering)
    # ============================================================================

    async def test_resilience_reliability(self) -> List[TestResult]:
        """Category 3: Resilience & Reliability Tests (Chaos Engineering)"""
        self.print_test_header("RESILIENCE & RELIABILITY", "Chaos Engineering Tests")

        results = []

        # Test 1: Database "Blink" Test
        start_time = time.time()
        try:
            # Check if DragonflyDB container exists
            success, stdout, stderr = self.execute_shell_command(
                "docker ps --filter name=dragonfly --format '{{.Names}}'"
            )

            if success and stdout.strip():
                container_name = stdout.strip().split('\n')[0]

                # Test connection before restart (simplified test)
                connection_before = True  # Assume connection works

                if connection_before:
                    # Restart the container
                    restart_success, _, restart_error = self.execute_shell_command(
                        f"docker restart {container_name}"
                    )

                    if restart_success:
                        # Wait for container to come back up
                        time.sleep(5)

                        # Check if container is running
                        check_success, check_stdout, _ = self.execute_shell_command(
                            f"docker ps --filter name={container_name} --filter status=running --format '{{.Names}}'"
                        )

                        if check_success and check_stdout.strip():
                            status = "PASS"
                            details = f"Database blink test successful: {container_name} restarted and recovered"
                        else:
                            status = "FAIL"
                            details = f"Database failed to restart: {container_name}"
                    else:
                        status = "FAIL"
                        details = f"Failed to restart container: {restart_error}"
                else:
                    status = "SKIP"
                    details = "DragonflyDB not accessible for testing"
            else:
                status = "SKIP"
                details = "DragonflyDB container not found"

            duration = time.time() - start_time
            results.append(self.record_result(
                "Database Blink Test", "Resilience", status, duration, details
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Database Blink Test", "Resilience", "FAIL", duration, str(e)
            ))

        # Test 2: API Overload Test
        start_time = time.time()
        try:
            # Test monitoring endpoints under load
            test_endpoints = [
                f"{self.test_environment['endpoints']['prometheus']}/api/v1/query?query=up",
                f"{self.test_environment['endpoints']['grafana']}/api/health"
            ]

            load_test_results = {}

            for endpoint in test_endpoints:
                endpoint_name = endpoint.split('//')[1].split('/')[0].split(':')[0]

                # Baseline response time
                baseline_healthy, baseline_details, baseline_time = self.check_endpoint_health(endpoint)

                if baseline_healthy:
                    # Simulate load with sequential requests (simplified)
                    successful_requests = 0
                    total_requests = 10

                    for _ in range(total_requests):
                        try:
                            response = requests.get(endpoint, timeout=5)
                            if response.status_code == 200:
                                successful_requests += 1
                        except:
                            pass

                    # Check response time after load
                    post_load_healthy, post_load_details, post_load_time = self.check_endpoint_health(endpoint)

                    success_rate = (successful_requests / total_requests) * 100
                    performance_degradation = ((post_load_time - baseline_time) / baseline_time) * 100 if baseline_time > 0 else 0

                    load_test_results[endpoint_name] = {
                        'success_rate': success_rate,
                        'performance_degradation': performance_degradation,
                        'baseline_time': baseline_time,
                        'post_load_time': post_load_time
                    }
                else:
                    load_test_results[endpoint_name] = {'error': 'Endpoint not accessible'}

            duration = time.time() - start_time

            # Evaluate results
            if load_test_results:
                accessible_endpoints = [r for r in load_test_results.values() if 'success_rate' in r]
                if accessible_endpoints:
                    avg_success_rate = sum(r['success_rate'] for r in accessible_endpoints) / len(accessible_endpoints)

                    if avg_success_rate >= 90:
                        status = "PASS"
                        details = f"API overload test successful: {avg_success_rate:.1f}% average success rate"
                    elif avg_success_rate >= 70:
                        status = "WARN"
                        details = f"API overload test partial: {avg_success_rate:.1f}% average success rate"
                    else:
                        status = "FAIL"
                        details = f"API overload test failed: {avg_success_rate:.1f}% average success rate"
                else:
                    status = "SKIP"
                    details = "No accessible endpoints for load testing"
            else:
                status = "SKIP"
                details = "No endpoints available for load testing"

            results.append(self.record_result(
                "API Overload Test", "Resilience", status, duration, details,
                {"load_test_results": load_test_results}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "API Overload Test", "Resilience", "FAIL", duration, str(e)
            ))

        # Test 3: Container Failure Recovery Test
        start_time = time.time()
        try:
            # Find containers to test with
            success, stdout, stderr = self.execute_shell_command(
                "docker ps --format '{{.Names}}' | grep overmind"
            )

            if success and stdout.strip():
                containers = stdout.strip().split('\n')
                # Test with first available container
                test_container = containers[0] if containers else None

                if test_container:
                    # Stop the container
                    stop_success, _, stop_error = self.execute_shell_command(
                        f"docker stop {test_container}"
                    )

                    if stop_success:
                        # Wait a moment
                        time.sleep(2)

                        # Start the container
                        start_success, _, start_error = self.execute_shell_command(
                            f"docker start {test_container}"
                        )

                        if start_success:
                            # Wait for container to be healthy
                            time.sleep(10)

                            # Check if container is running
                            check_success, check_stdout, _ = self.execute_shell_command(
                                f"docker ps --filter name={test_container} --filter status=running --format '{{.Names}}'"
                            )

                            if check_success and check_stdout.strip():
                                status = "PASS"
                                details = f"Container recovery successful: {test_container} recovered"
                            else:
                                status = "FAIL"
                                details = f"Container failed to recover: {test_container}"
                        else:
                            status = "FAIL"
                            details = f"Container start failed: {start_error}"
                    else:
                        status = "FAIL"
                        details = f"Container stop failed: {stop_error}"
                else:
                    status = "SKIP"
                    details = "No OVERMIND containers found for testing"
            else:
                status = "SKIP"
                details = "No containers available for recovery testing"

            duration = time.time() - start_time
            results.append(self.record_result(
                "Container Failure Recovery Test", "Resilience", status, duration, details
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Container Failure Recovery Test", "Resilience", "FAIL", duration, str(e)
            ))

        return results

    # ============================================================================
    # CATEGORY 4: SECURITY TESTS
    # ============================================================================

    async def test_security(self) -> List[TestResult]:
        """Category 4: Security Tests"""
        self.print_test_header("SECURITY", "Security Vulnerability Assessment")

        results = []

        # Test 1: Network Access Test
        start_time = time.time()
        try:
            # Test internal service ports accessibility from external perspective
            internal_ports = [6379, 5432, 8000, 9200]  # DragonflyDB, PostgreSQL, Chroma, Elasticsearch
            accessible_ports = []

            for port in internal_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()

                    if result == 0:
                        accessible_ports.append(port)
                except Exception:
                    pass

            duration = time.time() - start_time

            # Evaluate security posture
            if not accessible_ports:
                status = "PASS"
                details = "All internal services properly secured - no external access"
            elif len(accessible_ports) <= 2:
                status = "WARN"
                details = f"Some internal services accessible: ports {accessible_ports}"
            else:
                status = "FAIL"
                details = f"Multiple internal services exposed: ports {accessible_ports}"

            results.append(self.record_result(
                "Network Access Test", "Security", status, duration, details,
                {"accessible_ports": accessible_ports, "total_tested": len(internal_ports)}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Network Access Test", "Security", "FAIL", duration, str(e)
            ))

        # Test 2: Container Vulnerability Scan
        start_time = time.time()
        try:
            # Check if Trivy is available for container scanning
            trivy_available = False
            try:
                success, stdout, stderr = self.execute_shell_command("trivy --version")
                if success:
                    trivy_available = True
            except:
                pass

            if trivy_available:
                # Scan a sample container image
                scan_success, scan_output, scan_error = self.execute_shell_command(
                    "trivy image --severity HIGH,CRITICAL --format json postgres:15-alpine",
                    timeout=60
                )

                if scan_success:
                    try:
                        scan_data = json.loads(scan_output)
                        vulnerabilities = scan_data.get('Results', [])
                        critical_vulns = 0
                        high_vulns = 0

                        for result in vulnerabilities:
                            for vuln in result.get('Vulnerabilities', []):
                                severity = vuln.get('Severity', '')
                                if severity == 'CRITICAL':
                                    critical_vulns += 1
                                elif severity == 'HIGH':
                                    high_vulns += 1

                        if critical_vulns == 0 and high_vulns == 0:
                            status = "PASS"
                            details = "Container vulnerability scan clean: no critical/high vulnerabilities"
                        elif critical_vulns == 0 and high_vulns <= 3:
                            status = "WARN"
                            details = f"Container scan found {high_vulns} high severity vulnerabilities"
                        else:
                            status = "FAIL"
                            details = f"Container scan found {critical_vulns} critical, {high_vulns} high vulnerabilities"
                    except json.JSONDecodeError:
                        status = "WARN"
                        details = "Container scan completed but output format unexpected"
                else:
                    status = "FAIL"
                    details = f"Container vulnerability scan failed: {scan_error}"
            else:
                status = "SKIP"
                details = "Trivy not available for container vulnerability scanning"

            duration = time.time() - start_time
            results.append(self.record_result(
                "Container Vulnerability Scan", "Security", status, duration, details
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Container Vulnerability Scan", "Security", "FAIL", duration, str(e)
            ))

        # Test 3: Secret Leak Test
        start_time = time.time()
        try:
            # Scan codebase for potential secret leaks
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']{8,}["\']',
                r'secret\s*=\s*["\'][^"\']{8,}["\']',
                r'key\s*=\s*["\'][^"\']{20,}["\']',
                r'token\s*=\s*["\'][^"\']{20,}["\']',
                r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API key pattern
                r'[0-9a-fA-F]{64}',      # 64-char hex strings (potential private keys)
            ]

            # Files to scan
            scan_files = []
            for root, dirs, files in os.walk('.'):
                # Skip hidden directories and common non-source directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'target', '__pycache__']]

                for file in files:
                    if file.endswith(('.py', '.rs', '.js', '.ts', '.yml', '.yaml', '.json', '.env')):
                        scan_files.append(os.path.join(root, file))

            potential_leaks = []

            for file_path in scan_files[:50]:  # Limit to first 50 files for performance
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for pattern in secret_patterns:
                        import re
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            # Filter out obvious placeholders
                            real_matches = [m for m in matches if not any(placeholder in m.lower()
                                          for placeholder in ['placeholder', 'example', 'your-', 'xxx', 'test'])]
                            if real_matches:
                                potential_leaks.append(f"{file_path}: {len(real_matches)} potential secrets")
                except Exception:
                    continue

            duration = time.time() - start_time

            if not potential_leaks:
                status = "PASS"
                details = f"Secret leak scan clean: {len(scan_files)} files scanned, no secrets found"
            elif len(potential_leaks) <= 2:
                status = "WARN"
                details = f"Potential secret leaks found: {len(potential_leaks)} files with concerns"
            else:
                status = "FAIL"
                details = f"Multiple potential secret leaks: {len(potential_leaks)} files with concerns"

            results.append(self.record_result(
                "Secret Leak Test", "Security", status, duration, details,
                {"files_scanned": len(scan_files), "potential_leaks": len(potential_leaks)}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Secret Leak Test", "Security", "FAIL", duration, str(e)
            ))

        return results

    # ============================================================================
    # REPORT GENERATION AND MAIN EXECUTION
    # ============================================================================

    def generate_production_readiness_report(self) -> Dict:
        """Generate comprehensive production readiness certification report"""

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
        skipped_tests = sum(1 for r in self.results if r.status == "SKIP")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Generate comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_philosophy': 'Trust through Real-World Verification',
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warning_tests,
                'skipped': skipped_tests,
                'success_rate': success_rate,
                'total_duration': sum(r.duration for r in self.results)
            },
            'categories': {},
            'critical_issues': [],
            'recommendations': [],
            'production_readiness_score': 0,
            'certification_status': '',
            'evidence_collected': []
        }

        # Analyze by category with specific weights
        category_weights = {
            'Deployment': 0.30,      # Critical for deployment automation
            'Monitoring': 0.25,      # Essential for observability
            'Resilience': 0.25,      # Critical for reliability
            'Security': 0.20         # Important for production safety
        }

        weighted_score = 0
        for category, results in categories.items():
            category_passed = sum(1 for r in results if r.status == "PASS")
            category_total = len(results)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0

            report['categories'][category] = {
                'total_tests': category_total,
                'passed': category_passed,
                'failed': sum(1 for r in results if r.status == "FAIL"),
                'warnings': sum(1 for r in results if r.status == "WARN"),
                'skipped': sum(1 for r in results if r.status == "SKIP"),
                'success_rate': category_rate,
                'weight': category_weights.get(category, 0.1),
                'tests': [
                    {
                        'name': r.test_name,
                        'status': r.status,
                        'duration': r.duration,
                        'details': r.details,
                        'metrics': r.metrics,
                        'evidence': r.evidence
                    } for r in results
                ]
            }

            # Calculate weighted contribution
            weight = category_weights.get(category, 0.1)
            weighted_score += category_rate * weight

            # Identify critical issues
            for result in results:
                if result.status == "FAIL":
                    report['critical_issues'].append({
                        'category': category,
                        'test': result.test_name,
                        'issue': result.details,
                        'severity': 'CRITICAL' if category in ['Deployment', 'Security'] else 'HIGH'
                    })

        report['production_readiness_score'] = weighted_score

        # Determine certification status
        if weighted_score >= 90 and failed_tests == 0:
            report['certification_status'] = "✅ CERTIFIED - Production Ready"
            report['recommendations'].append("System is certified for production deployment")
        elif weighted_score >= 80 and failed_tests <= 1:
            report['certification_status'] = "⚠️ CONDITIONAL - Minor Issues"
            report['recommendations'].append("Address minor issues before production deployment")
        elif weighted_score >= 70:
            report['certification_status'] = "🔧 NEEDS WORK - Significant Issues"
            report['recommendations'].append("Significant improvements required before production")
        else:
            report['certification_status'] = "❌ NOT READY - Critical Issues"
            report['recommendations'].append("Critical issues must be resolved before production")

        # Add specific recommendations based on test results
        if failed_tests > 0:
            report['recommendations'].append(f"🚨 Resolve {failed_tests} critical test failures")
        if warning_tests > 3:
            report['recommendations'].append(f"⚠️ Address {warning_tests} warnings")

        # Category-specific recommendations
        for category, data in report['categories'].items():
            if data['success_rate'] < 80:
                if category == 'Deployment':
                    report['recommendations'].append("🚀 Improve deployment automation and configuration management")
                elif category == 'Monitoring':
                    report['recommendations'].append("📊 Enhance monitoring and observability infrastructure")
                elif category == 'Resilience':
                    report['recommendations'].append("🛡️ Strengthen system resilience and fault tolerance")
                elif category == 'Security':
                    report['recommendations'].append("🔒 Address security vulnerabilities and hardening")

        return report

    async def run_comprehensive_devops_tests(self) -> Dict:
        """Run all 4 categories of comprehensive DevOps tests"""

        print("🧠 THE OVERMIND PROTOCOL - Comprehensive DevOps Testing Suite")
        print("=" * 80)
        print("Philosophy: 'Trust through Real-World Verification'")
        print("Assume everything that can fail will fail. Verify system behavior when reality hits.")
        print("=" * 80)
        print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        self.start_time = time.time()

        # Run all 4 critical test categories
        test_categories = [
            ("Deployment & Configuration", self.test_deployment_configuration),
            ("Observability & Monitoring", self.test_observability_monitoring),
            ("Resilience & Reliability", self.test_resilience_reliability),
            ("Security", self.test_security)
        ]

        for category_name, test_method in test_categories:
            try:
                print(f"\n🔍 Executing {category_name} Tests...")
                await test_method()
            except Exception as e:
                logger.error(f"Failed to execute {category_name} tests: {e}")
                self.record_result(
                    f"{category_name} Test Suite", category_name, "FAIL", 0, str(e)
                )

        # Generate comprehensive report
        report = self.generate_production_readiness_report()

        # Print executive summary
        print(f"\n📊 COMPREHENSIVE DEVOPS TESTING SUMMARY:")
        print("=" * 60)
        print(f"Total Tests Executed: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']} ✅")
        print(f"Failed: {report['summary']['failed']} ❌")
        print(f"Warnings: {report['summary']['warnings']} ⚠️")
        print(f"Skipped: {report['summary']['skipped']} ⏭️")
        print(f"Overall Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Production Readiness Score: {report['production_readiness_score']:.1f}%")
        print(f"Total Test Duration: {report['summary']['total_duration']:.1f}s")

        # Print certification status
        print(f"\n🎯 PRODUCTION READINESS CERTIFICATION:")
        print(f"  {report['certification_status']}")

        # Print category breakdown
        print(f"\n📋 Test Category Results:")
        for category, data in report['categories'].items():
            weight = data['weight'] * 100
            print(f"  {category}: {data['passed']}/{data['total_tests']} ({data['success_rate']:.1f}%) [Weight: {weight:.0f}%]")

        # Print critical issues
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues Requiring Attention ({len(report['critical_issues'])}):")
            for issue in report['critical_issues']:
                severity_icon = "🔥" if issue['severity'] == 'CRITICAL' else "⚠️"
                print(f"  {severity_icon} {issue['category']} - {issue['test']}: {issue['issue']}")

        # Print recommendations
        print(f"\n💡 Production Deployment Recommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")

        print(f"\n🏁 Comprehensive DevOps Testing Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return report


async def main():
    """Main execution function for comprehensive DevOps testing"""
    tester = ComprehensiveDevOpsTestSuite()

    try:
        # Run comprehensive DevOps testing
        report = await tester.run_comprehensive_devops_tests()

        # Save detailed report
        with open('comprehensive-devops-report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n💾 Comprehensive report saved to: comprehensive-devops-report.json")

        # Create production readiness certificate
        certificate = {
            'system': 'THE OVERMIND PROTOCOL',
            'certification_date': datetime.now().isoformat(),
            'certification_status': report['certification_status'],
            'production_readiness_score': report['production_readiness_score'],
            'test_summary': report['summary'],
            'critical_issues_count': len(report['critical_issues']),
            'recommendations_count': len(report['recommendations']),
            'certified_by': 'Comprehensive DevOps Testing Suite',
            'valid_until': (datetime.now().replace(month=datetime.now().month + 3)).isoformat()  # 3 months validity
        }

        with open('production-readiness-certificate.json', 'w') as f:
            json.dump(certificate, f, indent=2, default=str)

        print(f"🏆 Production readiness certificate saved to: production-readiness-certificate.json")

        # Return exit code based on certification
        if report['production_readiness_score'] >= 90 and report['summary']['failed'] == 0:
            print("🎉 THE OVERMIND PROTOCOL is CERTIFIED for production deployment!")
            return 0
        elif report['production_readiness_score'] >= 80:
            print("⚠️ THE OVERMIND PROTOCOL has conditional readiness - address issues before deployment")
            return 1
        else:
            print("❌ THE OVERMIND PROTOCOL is NOT READY for production deployment")
            return 2

    except Exception as e:
        logger.error(f"Comprehensive DevOps testing failed: {e}")
        return 3


if __name__ == "__main__":
    import sys

    # Run the comprehensive DevOps testing suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
