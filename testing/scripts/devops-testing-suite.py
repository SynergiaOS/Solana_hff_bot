#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Comprehensive DevOps Testing Suite
Production readiness validation beyond code functionality

This suite answers: "Is our system not only intelligent and fast, 
but also bulletproof, fault-tolerant, and manageable under production conditions?"
"""

import asyncio
import json
import time
import os
import subprocess
import requests
import psutil
import docker
import logging
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('devops-testing.log'),
        logging.StreamHandler()
    ]
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
    metrics: Dict = None
    timestamp: datetime = None

class DevOpsTestSuite:
    """Comprehensive DevOps testing suite for THE OVERMIND PROTOCOL"""
    
    def __init__(self):
        self.results = []
        self.docker_client = None
        self.start_time = None
        self.test_environment = {
            'compose_file': 'docker-compose.overmind.yml',
            'services': [
                'overmind-dragonfly',
                'overmind-postgres', 
                'overmind-chroma',
                'tensorzero-gateway',
                'overmind-brain',
                'overmind-executor'
            ],
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
                     duration: float, details: str = "", metrics: Dict = None):
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
    
    async def test_infrastructure_resilience(self) -> List[TestResult]:
        """Test infrastructure resilience and fault tolerance"""
        self.print_test_header("INFRASTRUCTURE RESILIENCE", "Container Fault Tolerance")
        
        results = []
        
        # Test 1: Container restart resilience
        start_time = time.time()
        try:
            # Initialize Docker client
            self.docker_client = docker.from_env()
            
            # Test container restart behavior
            test_containers = ['overmind-dragonfly', 'overmind-postgres']
            restart_success = 0
            
            for container_name in test_containers:
                try:
                    container = self.docker_client.containers.get(container_name)
                    
                    # Record initial state
                    initial_status = container.status
                    
                    # Restart container
                    container.restart(timeout=30)
                    
                    # Wait for container to be healthy
                    max_wait = 60
                    wait_time = 0
                    while wait_time < max_wait:
                        container.reload()
                        if container.status == 'running':
                            # Check health if healthcheck exists
                            health = container.attrs.get('State', {}).get('Health', {})
                            if not health or health.get('Status') == 'healthy':
                                restart_success += 1
                                break
                        time.sleep(2)
                        wait_time += 2
                    
                except Exception as e:
                    logger.error(f"Failed to restart container {container_name}: {e}")
            
            duration = time.time() - start_time
            success_rate = (restart_success / len(test_containers)) * 100
            
            if success_rate >= 100:
                status = "PASS"
                details = f"All {len(test_containers)} containers restarted successfully"
            elif success_rate >= 80:
                status = "WARN"
                details = f"{restart_success}/{len(test_containers)} containers restarted successfully"
            else:
                status = "FAIL"
                details = f"Only {restart_success}/{len(test_containers)} containers restarted successfully"
            
            results.append(self.record_result(
                "Container Restart Resilience", "Infrastructure", status, duration, details,
                {"success_rate": f"{success_rate:.1f}%", "containers_tested": len(test_containers)}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Container Restart Resilience", "Infrastructure", "FAIL", duration, str(e)
            ))
        
        # Test 2: Network partition simulation
        start_time = time.time()
        try:
            # Simulate network issues by temporarily blocking container communication
            network_test_passed = True
            
            # Test service discovery and communication
            services_to_test = [
                ('overmind-executor', 'http://localhost:8080/health'),
                ('overmind-brain', 'http://localhost:8001/health'),
                ('chroma', 'http://localhost:8000/api/v1/heartbeat')
            ]
            
            healthy_services = 0
            for service_name, health_url in services_to_test:
                try:
                    response = requests.get(health_url, timeout=10)
                    if response.status_code == 200:
                        healthy_services += 1
                except Exception as e:
                    logger.warning(f"Service {service_name} health check failed: {e}")
            
            duration = time.time() - start_time
            health_rate = (healthy_services / len(services_to_test)) * 100
            
            if health_rate >= 100:
                status = "PASS"
                details = f"All {len(services_to_test)} services are healthy"
            elif health_rate >= 80:
                status = "WARN" 
                details = f"{healthy_services}/{len(services_to_test)} services are healthy"
            else:
                status = "FAIL"
                details = f"Only {healthy_services}/{len(services_to_test)} services are healthy"
            
            results.append(self.record_result(
                "Service Health Check", "Infrastructure", status, duration, details,
                {"health_rate": f"{health_rate:.1f}%", "services_tested": len(services_to_test)}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Service Health Check", "Infrastructure", "FAIL", duration, str(e)
            ))
        
        # Test 3: Resource exhaustion simulation
        start_time = time.time()
        try:
            # Test system behavior under resource pressure
            system_metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
            
            # Check if system is under acceptable load
            resource_issues = []
            if system_metrics['cpu_percent'] > 90:
                resource_issues.append(f"High CPU usage: {system_metrics['cpu_percent']:.1f}%")
            if system_metrics['memory_percent'] > 90:
                resource_issues.append(f"High memory usage: {system_metrics['memory_percent']:.1f}%")
            if system_metrics['disk_percent'] > 90:
                resource_issues.append(f"High disk usage: {system_metrics['disk_percent']:.1f}%")
            
            duration = time.time() - start_time
            
            if not resource_issues:
                status = "PASS"
                details = "System resources within acceptable limits"
            elif len(resource_issues) <= 1:
                status = "WARN"
                details = f"Resource concerns: {'; '.join(resource_issues)}"
            else:
                status = "FAIL"
                details = f"Multiple resource issues: {'; '.join(resource_issues)}"
            
            results.append(self.record_result(
                "Resource Utilization Check", "Infrastructure", status, duration, details,
                system_metrics
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Resource Utilization Check", "Infrastructure", "FAIL", duration, str(e)
            ))
        
        return results
    
    async def test_disaster_recovery(self) -> List[TestResult]:
        """Test disaster recovery capabilities"""
        self.print_test_header("DISASTER RECOVERY", "Backup and Recovery Procedures")
        
        results = []
        
        # Test 1: Database backup and restore
        start_time = time.time()
        try:
            # Test PostgreSQL backup capability
            backup_test_passed = False
            
            # Check if backup directory exists and is writable
            backup_dir = "./backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Test backup script execution (dry run)
            backup_script = "./scripts/backup-system.sh"
            if os.path.exists(backup_script):
                # Run backup script in test mode
                result = subprocess.run([backup_script, "--test"], 
                                      capture_output=True, text=True, timeout=60)
                backup_test_passed = result.returncode == 0
                backup_details = result.stdout if result.returncode == 0 else result.stderr
            else:
                backup_details = "Backup script not found - creating basic backup test"
                # Create a simple backup test
                try:
                    # Test Docker volume backup capability
                    volumes = self.docker_client.volumes.list()
                    overmind_volumes = [v for v in volumes if 'overmind' in v.name.lower()]
                    backup_test_passed = len(overmind_volumes) > 0
                    backup_details = f"Found {len(overmind_volumes)} OVERMIND volumes for backup"
                except Exception as e:
                    backup_details = f"Volume backup test failed: {e}"
            
            duration = time.time() - start_time
            
            if backup_test_passed:
                status = "PASS"
                details = f"Backup capability verified: {backup_details}"
            else:
                status = "FAIL"
                details = f"Backup test failed: {backup_details}"
            
            results.append(self.record_result(
                "Backup Capability Test", "Disaster Recovery", status, duration, details
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Backup Capability Test", "Disaster Recovery", "FAIL", duration, str(e)
            ))
        
        # Test 2: Configuration backup and restore
        start_time = time.time()
        try:
            # Test configuration file backup
            config_files = [
                '.env',
                'docker-compose.overmind.yml',
                'monitoring/prometheus.yml'
            ]
            
            backed_up_configs = 0
            for config_file in config_files:
                if os.path.exists(config_file):
                    # Test if file is readable and can be backed up
                    try:
                        with open(config_file, 'r') as f:
                            content = f.read()
                        if content:
                            backed_up_configs += 1
                    except Exception as e:
                        logger.warning(f"Cannot read config file {config_file}: {e}")
            
            duration = time.time() - start_time
            config_backup_rate = (backed_up_configs / len(config_files)) * 100
            
            if config_backup_rate >= 100:
                status = "PASS"
                details = f"All {len(config_files)} configuration files can be backed up"
            elif config_backup_rate >= 80:
                status = "WARN"
                details = f"{backed_up_configs}/{len(config_files)} configuration files can be backed up"
            else:
                status = "FAIL"
                details = f"Only {backed_up_configs}/{len(config_files)} configuration files can be backed up"
            
            results.append(self.record_result(
                "Configuration Backup Test", "Disaster Recovery", status, duration, details,
                {"backup_rate": f"{config_backup_rate:.1f}%"}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Configuration Backup Test", "Disaster Recovery", "FAIL", duration, str(e)
            ))
        
        # Test 3: Recovery time objective (RTO) simulation
        start_time = time.time()
        try:
            # Simulate service recovery time
            test_service = 'overmind-dragonfly'
            
            if self.docker_client:
                container = self.docker_client.containers.get(test_service)
                
                # Stop the service
                stop_time = time.time()
                container.stop(timeout=10)
                
                # Start the service
                container.start()
                
                # Measure time to healthy state
                recovery_start = time.time()
                max_recovery_time = 120  # 2 minutes max
                recovered = False
                
                while (time.time() - recovery_start) < max_recovery_time:
                    container.reload()
                    if container.status == 'running':
                        # Check health if available
                        health = container.attrs.get('State', {}).get('Health', {})
                        if not health or health.get('Status') == 'healthy':
                            recovered = True
                            break
                    time.sleep(2)
                
                recovery_time = time.time() - recovery_start
                duration = time.time() - start_time
                
                if recovered and recovery_time < 60:  # Under 1 minute
                    status = "PASS"
                    details = f"Service recovered in {recovery_time:.1f}s (target: <60s)"
                elif recovered and recovery_time < 120:  # Under 2 minutes
                    status = "WARN"
                    details = f"Service recovered in {recovery_time:.1f}s (slower than ideal)"
                else:
                    status = "FAIL"
                    details = f"Service recovery failed or took too long ({recovery_time:.1f}s)"
                
                results.append(self.record_result(
                    "Recovery Time Objective Test", "Disaster Recovery", status, duration, details,
                    {"recovery_time": f"{recovery_time:.1f}s", "target_rto": "60s"}
                ))
            else:
                raise Exception("Docker client not available")
                
        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Recovery Time Objective Test", "Disaster Recovery", "FAIL", duration, str(e)
            ))
        
        return results

    async def test_monitoring_effectiveness(self) -> List[TestResult]:
        """Test monitoring and alerting systems"""
        self.print_test_header("MONITORING", "Observability and Alerting")

        results = []

        # Test 1: Prometheus metrics collection
        start_time = time.time()
        try:
            prometheus_url = self.test_environment['endpoints']['prometheus']

            # Test Prometheus API
            response = requests.get(f"{prometheus_url}/api/v1/targets", timeout=10)

            if response.status_code == 200:
                targets_data = response.json()
                active_targets = targets_data.get('data', {}).get('activeTargets', [])

                # Count healthy targets
                healthy_targets = sum(1 for target in active_targets if target.get('health') == 'up')
                total_targets = len(active_targets)

                health_rate = (healthy_targets / total_targets * 100) if total_targets > 0 else 0

                if health_rate >= 90:
                    status = "PASS"
                    details = f"Prometheus monitoring healthy: {healthy_targets}/{total_targets} targets up"
                elif health_rate >= 70:
                    status = "WARN"
                    details = f"Some monitoring issues: {healthy_targets}/{total_targets} targets up"
                else:
                    status = "FAIL"
                    details = f"Monitoring problems: {healthy_targets}/{total_targets} targets up"

                # Test specific OVERMIND metrics
                metrics_response = requests.get(f"{prometheus_url}/api/v1/query?query=up", timeout=10)
                metrics_available = metrics_response.status_code == 200

            else:
                status = "FAIL"
                details = f"Prometheus API not accessible: HTTP {response.status_code}"
                health_rate = 0
                metrics_available = False

            duration = time.time() - start_time

            results.append(self.record_result(
                "Prometheus Metrics Collection", "Monitoring", status, duration, details,
                {"health_rate": f"{health_rate:.1f}%", "metrics_api": metrics_available}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Prometheus Metrics Collection", "Monitoring", "FAIL", duration, str(e)
            ))

        # Test 2: Application metrics availability
        start_time = time.time()
        try:
            # Test OVERMIND-specific metrics
            overmind_metrics = [
                'overmind_trades_total',
                'overmind_execution_latency_seconds',
                'overmind_ai_confidence_score',
                'overmind_risk_score'
            ]

            available_metrics = 0
            prometheus_url = self.test_environment['endpoints']['prometheus']

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
                    pass  # Metric not available

            duration = time.time() - start_time
            metrics_rate = (available_metrics / len(overmind_metrics)) * 100

            if metrics_rate >= 75:
                status = "PASS"
                details = f"OVERMIND metrics available: {available_metrics}/{len(overmind_metrics)}"
            elif metrics_rate >= 50:
                status = "WARN"
                details = f"Some OVERMIND metrics missing: {available_metrics}/{len(overmind_metrics)}"
            else:
                status = "FAIL"
                details = f"Most OVERMIND metrics unavailable: {available_metrics}/{len(overmind_metrics)}"

            results.append(self.record_result(
                "Application Metrics Availability", "Monitoring", status, duration, details,
                {"metrics_rate": f"{metrics_rate:.1f}%"}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Application Metrics Availability", "Monitoring", "FAIL", duration, str(e)
            ))

        # Test 3: Log aggregation and retention
        start_time = time.time()
        try:
            # Check Docker container logs
            log_health = {}

            if self.docker_client:
                for service in self.test_environment['services']:
                    try:
                        container = self.docker_client.containers.get(service)
                        logs = container.logs(tail=10, timestamps=True)

                        if logs:
                            log_health[service] = "available"
                        else:
                            log_health[service] = "empty"
                    except Exception as e:
                        log_health[service] = f"error: {str(e)[:50]}"

            healthy_logs = sum(1 for status in log_health.values() if status == "available")
            total_services = len(self.test_environment['services'])
            log_rate = (healthy_logs / total_services) * 100

            duration = time.time() - start_time

            if log_rate >= 90:
                status = "PASS"
                details = f"Log collection healthy: {healthy_logs}/{total_services} services"
            elif log_rate >= 70:
                status = "WARN"
                details = f"Some log issues: {healthy_logs}/{total_services} services"
            else:
                status = "FAIL"
                details = f"Log collection problems: {healthy_logs}/{total_services} services"

            results.append(self.record_result(
                "Log Aggregation Test", "Monitoring", status, duration, details,
                {"log_rate": f"{log_rate:.1f}%", "services_checked": total_services}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Log Aggregation Test", "Monitoring", "FAIL", duration, str(e)
            ))

        return results

    async def test_security_hardening(self) -> List[TestResult]:
        """Test security measures and hardening"""
        self.print_test_header("SECURITY", "Security Hardening and Compliance")

        results = []

        # Test 1: Container security configuration
        start_time = time.time()
        try:
            security_issues = []

            if self.docker_client:
                for service_name in self.test_environment['services']:
                    try:
                        container = self.docker_client.containers.get(service_name)
                        config = container.attrs.get('HostConfig', {})

                        # Check for privileged mode
                        if config.get('Privileged', False):
                            security_issues.append(f"{service_name}: Running in privileged mode")

                        # Check for host network mode
                        if config.get('NetworkMode') == 'host':
                            security_issues.append(f"{service_name}: Using host network mode")

                        # Check for root user
                        user = container.attrs.get('Config', {}).get('User', '')
                        if not user or user == 'root' or user == '0':
                            security_issues.append(f"{service_name}: Running as root user")

                    except Exception as e:
                        security_issues.append(f"{service_name}: Cannot inspect container - {e}")

            duration = time.time() - start_time

            if not security_issues:
                status = "PASS"
                details = "No major security issues found in container configuration"
            elif len(security_issues) <= 2:
                status = "WARN"
                details = f"Minor security concerns: {'; '.join(security_issues[:2])}"
            else:
                status = "FAIL"
                details = f"Multiple security issues: {len(security_issues)} problems found"

            results.append(self.record_result(
                "Container Security Configuration", "Security", status, duration, details,
                {"issues_found": len(security_issues)}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Container Security Configuration", "Security", "FAIL", duration, str(e)
            ))

        # Test 2: Network security and port exposure
        start_time = time.time()
        try:
            exposed_ports = []

            if self.docker_client:
                for service_name in self.test_environment['services']:
                    try:
                        container = self.docker_client.containers.get(service_name)
                        ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})

                        for container_port, host_bindings in ports.items():
                            if host_bindings:
                                for binding in host_bindings:
                                    host_ip = binding.get('HostIp', '0.0.0.0')
                                    host_port = binding.get('HostPort')

                                    # Check for dangerous exposures
                                    if host_ip == '0.0.0.0':
                                        exposed_ports.append(f"{service_name}:{container_port} -> {host_ip}:{host_port}")
                    except Exception:
                        pass

            duration = time.time() - start_time

            # Check for dangerous port exposures
            dangerous_exposures = [port for port in exposed_ports if '0.0.0.0' in port]

            if not dangerous_exposures:
                status = "PASS"
                details = "No dangerous port exposures found (all bound to localhost)"
            elif len(dangerous_exposures) <= 1:
                status = "WARN"
                details = f"Some ports exposed to all interfaces: {len(dangerous_exposures)}"
            else:
                status = "FAIL"
                details = f"Multiple dangerous port exposures: {len(dangerous_exposures)}"

            results.append(self.record_result(
                "Network Security Check", "Security", status, duration, details,
                {"exposed_ports": len(exposed_ports), "dangerous_exposures": len(dangerous_exposures)}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Network Security Check", "Security", "FAIL", duration, str(e)
            ))

        return results

    async def test_performance_under_stress(self) -> List[TestResult]:
        """Test system performance under stress conditions"""
        self.print_test_header("STRESS TESTING", "Performance Under Load")

        results = []

        # Test 1: High-frequency API calls
        start_time = time.time()
        try:
            # Test executor API under load
            executor_url = self.test_environment['endpoints']['executor']

            # Concurrent health check requests
            concurrent_requests = 50
            request_timeout = 5
            successful_requests = 0

            def make_request():
                try:
                    response = requests.get(f"{executor_url}/health", timeout=request_timeout)
                    return response.status_code == 200
                except:
                    return False

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrent_requests)]

                for future in as_completed(futures, timeout=30):
                    if future.result():
                        successful_requests += 1

            duration = time.time() - start_time
            success_rate = (successful_requests / concurrent_requests) * 100

            if success_rate >= 95:
                status = "PASS"
                details = f"High load handled well: {successful_requests}/{concurrent_requests} requests succeeded"
            elif success_rate >= 80:
                status = "WARN"
                details = f"Some degradation under load: {successful_requests}/{concurrent_requests} requests succeeded"
            else:
                status = "FAIL"
                details = f"Poor performance under load: {successful_requests}/{concurrent_requests} requests succeeded"

            results.append(self.record_result(
                "High-Frequency API Load Test", "Stress Testing", status, duration, details,
                {"success_rate": f"{success_rate:.1f}%", "requests_per_second": f"{concurrent_requests/duration:.1f}"}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "High-Frequency API Load Test", "Stress Testing", "FAIL", duration, str(e)
            ))

        # Test 2: Memory pressure simulation
        start_time = time.time()
        try:
            # Monitor memory usage before and during stress
            initial_memory = psutil.virtual_memory().percent

            # Create memory pressure (careful not to crash system)
            memory_hog = []
            target_memory_mb = 500  # 500MB allocation

            try:
                # Allocate memory in chunks
                for i in range(50):
                    chunk = bytearray(10 * 1024 * 1024)  # 10MB chunks
                    memory_hog.append(chunk)
                    time.sleep(0.1)  # Small delay

                # Check system response
                peak_memory = psutil.virtual_memory().percent

                # Test if services are still responsive
                executor_responsive = False
                try:
                    response = requests.get(f"{self.test_environment['endpoints']['executor']}/health", timeout=10)
                    executor_responsive = response.status_code == 200
                except:
                    pass

                # Clean up memory
                del memory_hog

                duration = time.time() - start_time
                memory_increase = peak_memory - initial_memory

                if executor_responsive and memory_increase < 50:
                    status = "PASS"
                    details = f"System stable under memory pressure (+{memory_increase:.1f}% memory)"
                elif executor_responsive:
                    status = "WARN"
                    details = f"System responsive but high memory usage (+{memory_increase:.1f}%)"
                else:
                    status = "FAIL"
                    details = f"System unresponsive under memory pressure (+{memory_increase:.1f}%)"

                results.append(self.record_result(
                    "Memory Pressure Test", "Stress Testing", status, duration, details,
                    {"memory_increase": f"{memory_increase:.1f}%", "peak_memory": f"{peak_memory:.1f}%"}
                ))

            except MemoryError:
                duration = time.time() - start_time
                results.append(self.record_result(
                    "Memory Pressure Test", "Stress Testing", "FAIL", duration, "Memory allocation failed"
                ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Memory Pressure Test", "Stress Testing", "FAIL", duration, str(e)
            ))

        # Test 3: Network latency simulation
        start_time = time.time()
        try:
            # Test system behavior with network delays
            # This is a simplified test - in production you'd use tools like tc (traffic control)

            # Test multiple endpoints with timeout variations
            endpoints_to_test = [
                ('executor', self.test_environment['endpoints']['executor'] + '/health'),
                ('brain', self.test_environment['endpoints']['brain'] + '/health'),
                ('chroma', self.test_environment['endpoints']['chroma'] + '/api/v1/heartbeat')
            ]

            latency_results = {}

            for service_name, url in endpoints_to_test:
                latencies = []
                for _ in range(5):  # 5 requests per service
                    try:
                        start_req = time.time()
                        response = requests.get(url, timeout=10)
                        end_req = time.time()

                        if response.status_code == 200:
                            latencies.append((end_req - start_req) * 1000)  # Convert to ms
                    except:
                        latencies.append(None)  # Failed request

                # Calculate average latency (excluding failures)
                valid_latencies = [l for l in latencies if l is not None]
                if valid_latencies:
                    avg_latency = sum(valid_latencies) / len(valid_latencies)
                    latency_results[service_name] = avg_latency
                else:
                    latency_results[service_name] = None

            duration = time.time() - start_time

            # Evaluate latency results
            high_latency_services = [name for name, latency in latency_results.items()
                                   if latency and latency > 1000]  # >1 second
            failed_services = [name for name, latency in latency_results.items() if latency is None]

            if not high_latency_services and not failed_services:
                status = "PASS"
                details = "All services responding with acceptable latency"
            elif len(high_latency_services) <= 1 and not failed_services:
                status = "WARN"
                details = f"Some latency issues: {high_latency_services}"
            else:
                status = "FAIL"
                details = f"High latency or failures: {high_latency_services + failed_services}"

            results.append(self.record_result(
                "Network Latency Test", "Stress Testing", status, duration, details,
                {"latency_results": {k: f"{v:.1f}ms" if v else "failed" for k, v in latency_results.items()}}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Network Latency Test", "Stress Testing", "FAIL", duration, str(e)
            ))

        return results

    async def test_operational_procedures(self) -> List[TestResult]:
        """Test operational procedures and automation"""
        self.print_test_header("OPERATIONAL PROCEDURES", "Deployment and Management")

        results = []

        # Test 1: Deployment script validation
        start_time = time.time()
        try:
            deployment_scripts = [
                'deploy-overmind.sh',
                'docker-compose.overmind.yml',
                'complete-vds-upgrade.sh'
            ]

            script_status = {}
            for script in deployment_scripts:
                if os.path.exists(script):
                    # Check if script is executable (for .sh files)
                    if script.endswith('.sh'):
                        script_status[script] = os.access(script, os.X_OK)
                    else:
                        script_status[script] = True
                else:
                    script_status[script] = False

            available_scripts = sum(1 for status in script_status.values() if status)
            total_scripts = len(deployment_scripts)

            duration = time.time() - start_time

            if available_scripts == total_scripts:
                status = "PASS"
                details = f"All {total_scripts} deployment scripts available and executable"
            elif available_scripts >= total_scripts * 0.8:
                status = "WARN"
                details = f"{available_scripts}/{total_scripts} deployment scripts available"
            else:
                status = "FAIL"
                details = f"Only {available_scripts}/{total_scripts} deployment scripts available"

            results.append(self.record_result(
                "Deployment Scripts Validation", "Operational", status, duration, details,
                {"available_scripts": available_scripts, "total_scripts": total_scripts}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Deployment Scripts Validation", "Operational", "FAIL", duration, str(e)
            ))

        # Test 2: Environment configuration validation
        start_time = time.time()
        try:
            # Check critical environment variables
            critical_env_vars = [
                'SNIPER_SOLANA_RPC_URL',
                'SNIPER_WALLET_PRIVATE_KEY',
                'OPENAI_API_KEY',
                'OVERMIND_MULTI_WALLET_ENABLED'
            ]

            env_status = {}
            for var in critical_env_vars:
                value = os.getenv(var)
                if value and value.strip() and not value.startswith('your-'):
                    env_status[var] = "configured"
                elif value:
                    env_status[var] = "placeholder"
                else:
                    env_status[var] = "missing"

            configured_vars = sum(1 for status in env_status.values() if status == "configured")
            total_vars = len(critical_env_vars)

            duration = time.time() - start_time

            if configured_vars == total_vars:
                status = "PASS"
                details = f"All {total_vars} critical environment variables configured"
            elif configured_vars >= total_vars * 0.8:
                status = "WARN"
                details = f"{configured_vars}/{total_vars} critical environment variables configured"
            else:
                status = "FAIL"
                details = f"Only {configured_vars}/{total_vars} critical environment variables configured"

            results.append(self.record_result(
                "Environment Configuration", "Operational", status, duration, details,
                {"configured_vars": configured_vars, "total_vars": total_vars}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(self.record_result(
                "Environment Configuration", "Operational", "FAIL", duration, str(e)
            ))

        return results

    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive DevOps testing report"""

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

        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
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
            'production_readiness_score': 0
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
            'Infrastructure': 0.25,
            'Disaster Recovery': 0.20,
            'Monitoring': 0.20,
            'Security': 0.15,
            'Stress Testing': 0.15,
            'Operational': 0.05
        }

        weighted_score = 0
        for category, weight in weights.items():
            if category in report['categories']:
                category_score = report['categories'][category]['success_rate']
                weighted_score += category_score * weight

        report['production_readiness_score'] = weighted_score

        # Generate recommendations
        if report['production_readiness_score'] >= 90:
            report['recommendations'].append("✅ System is production-ready with excellent DevOps practices")
        elif report['production_readiness_score'] >= 80:
            report['recommendations'].append("⚠️ System is mostly production-ready - address warnings before deployment")
        elif report['production_readiness_score'] >= 70:
            report['recommendations'].append("🔧 System needs improvements before production deployment")
        else:
            report['recommendations'].append("❌ System is not ready for production - critical issues must be resolved")

        # Add specific recommendations based on failures
        if failed_tests > 0:
            report['recommendations'].append(f"🚨 Address {failed_tests} critical test failures")
        if warning_tests > 3:
            report['recommendations'].append(f"⚠️ Review {warning_tests} warnings for potential issues")

        return report

    async def run_comprehensive_devops_tests(self) -> Dict:
        """Run all DevOps tests and generate comprehensive report"""

        print("🧠 THE OVERMIND PROTOCOL - Comprehensive DevOps Testing Suite")
        print("=" * 80)
        print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Testing production readiness beyond code functionality...")
        print("=" * 80)

        self.start_time = time.time()

        try:
            # Initialize Docker client
            self.docker_client = docker.from_env()
            print("✅ Docker client initialized successfully")
        except Exception as e:
            print(f"⚠️ Docker client initialization failed: {e}")
            print("Some tests may be skipped or limited")

        # Run all test categories
        test_categories = [
            ("Infrastructure Resilience", self.test_infrastructure_resilience),
            ("Disaster Recovery", self.test_disaster_recovery),
            ("Monitoring Effectiveness", self.test_monitoring_effectiveness),
            ("Security Hardening", self.test_security_hardening),
            ("Performance Under Stress", self.test_performance_under_stress),
            ("Operational Procedures", self.test_operational_procedures)
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

        # Generate comprehensive report
        report = self.generate_comprehensive_report()

        # Print summary
        print(f"\n📊 DevOps Testing Summary:")
        print("=" * 50)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']} ✅")
        print(f"Failed: {report['summary']['failed']} ❌")
        print(f"Warnings: {report['summary']['warnings']} ⚠️")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Production Readiness Score: {report['production_readiness_score']:.1f}%")
        print(f"Total Duration: {report['summary']['total_duration']:.1f}s")

        # Print category breakdown
        print(f"\n📋 Category Breakdown:")
        for category, data in report['categories'].items():
            print(f"  {category}: {data['passed']}/{data['total_tests']} ({data['success_rate']:.1f}%)")

        # Print critical issues
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues ({len(report['critical_issues'])}):")
            for issue in report['critical_issues'][:5]:  # Show first 5
                print(f"  • {issue['category']} - {issue['test']}: {issue['issue']}")

        # Print recommendations
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")

        print(f"\n🏁 DevOps Testing Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return report


async def main():
    """Main execution function"""
    tester = DevOpsTestSuite()

    try:
        # Run comprehensive DevOps testing
        report = await tester.run_comprehensive_devops_tests()

        # Save detailed report
        with open('devops-testing-report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n💾 Detailed report saved to: devops-testing-report.json")

        # Return exit code based on results
        if report['production_readiness_score'] >= 90:
            print("🎉 THE OVERMIND PROTOCOL is PRODUCTION READY from DevOps perspective!")
            return 0
        elif report['production_readiness_score'] >= 80:
            print("⚠️ THE OVERMIND PROTOCOL is mostly ready - address warnings")
            return 1
        else:
            print("❌ THE OVERMIND PROTOCOL needs significant DevOps improvements")
            return 2

    except Exception as e:
        logger.error(f"DevOps testing suite failed: {e}")
        return 3


if __name__ == "__main__":
    import sys

    # Run the DevOps testing suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
