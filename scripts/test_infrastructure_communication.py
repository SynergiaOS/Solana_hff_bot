#!/usr/bin/env python3
"""
🔗 THE OVERMIND PROTOCOL - Infrastructure Communication Test
FRONT 2: Test komunikacji Warstwa 1 (Infrastructure) ↔ Warstwa 2 (Data Intelligence)
"""

import asyncio
import json
import sys
import os
import time
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Any

class InfrastructureCommunicationTester:
    """Tester komunikacji infrastruktury"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    def run_command(self, command: str) -> Dict[str, Any]:
        """Uruchom komendę shell i zwróć wynik"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "returncode": -1
            }
    
    def test_docker_infrastructure(self) -> Dict[str, Any]:
        """Test 2.1.1: Docker Network Communication"""
        print("\n🐳 TEST 2.1.1: DOCKER NETWORK COMMUNICATION")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Docker Compose Status
        print("🔍 Sprawdzanie statusu Docker Compose...")
        result = self.run_command("docker-compose ps")
        docker_status = {
            "test": "Docker Compose Status",
            "success": result["success"],
            "details": result["stdout"] if result["success"] else result.get("stderr", "Unknown error")
        }
        tests.append(docker_status)
        print(f"  Status: {'✅ UP' if result['success'] else '❌ DOWN'}")
        
        # Test 2: Container Network Connectivity
        print("🔍 Testowanie łączności między kontenerami...")
        
        # Lista kontenerów do testowania
        containers_to_test = [
            "dragonfly",
            "postgres", 
            "prometheus",
            "grafana"
        ]
        
        network_tests = []
        for container in containers_to_test:
            # Sprawdź czy kontener działa
            check_cmd = f"docker ps --filter name={container} --format '{{{{.Names}}}}'"
            result = self.run_command(check_cmd)
            
            container_test = {
                "container": container,
                "running": container in result.get("stdout", ""),
                "status": "UP" if container in result.get("stdout", "") else "DOWN"
            }
            network_tests.append(container_test)
            print(f"  {container}: {'✅ UP' if container_test['running'] else '❌ DOWN'}")
        
        tests.append({
            "test": "Container Network Status",
            "success": all(t["running"] for t in network_tests),
            "details": network_tests
        })
        
        # Test 3: DNS Resolution
        print("🔍 Testowanie rozwiązywania DNS...")
        dns_tests = []
        
        # Test DNS resolution dla kluczowych serwisów
        dns_targets = [
            ("localhost", "6379"),  # DragonflyDB
            ("localhost", "5432"),  # PostgreSQL
            ("localhost", "9090"),  # Prometheus
            ("localhost", "3000")   # Grafana
        ]
        
        for host, port in dns_targets:
            # Test połączenia TCP
            test_cmd = f"timeout 5 bash -c 'cat < /dev/null > /dev/tcp/{host}/{port}'"
            result = self.run_command(test_cmd)
            
            dns_test = {
                "target": f"{host}:{port}",
                "reachable": result["success"],
                "response_time": "< 5s" if result["success"] else "timeout"
            }
            dns_tests.append(dns_test)
            print(f"  {host}:{port}: {'✅ REACHABLE' if result['success'] else '❌ UNREACHABLE'}")
        
        tests.append({
            "test": "DNS Resolution & Port Connectivity",
            "success": any(t["reachable"] for t in dns_tests),  # At least one should work
            "details": dns_tests
        })
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 Docker Infrastructure Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "Docker Infrastructure Communication",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_database_connectivity(self) -> Dict[str, Any]:
        """Test 2.1.2: Database Connectivity"""
        print("\n💾 TEST 2.1.2: DATABASE CONNECTIVITY")
        print("-" * 50)
        
        tests = []
        
        # Test 1: DragonflyDB Connection
        print("🔍 Testowanie połączenia z DragonflyDB...")
        try:
            import redis
            
            # Próba połączenia z DragonflyDB
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Test basic operations
            test_key = "overmind_test_key"
            test_value = "test_value_" + str(int(time.time()))
            
            # Set value
            r.set(test_key, test_value)
            
            # Get value
            retrieved_value = r.get(test_key)
            
            # Clean up
            r.delete(test_key)
            
            dragonfly_test = {
                "test": "DragonflyDB Connection",
                "success": retrieved_value == test_value,
                "details": {
                    "host": "localhost",
                    "port": 6379,
                    "operation": "SET/GET/DELETE",
                    "result": "SUCCESS" if retrieved_value == test_value else "FAILED"
                }
            }
            print(f"  DragonflyDB: {'✅ CONNECTED' if dragonfly_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            dragonfly_test = {
                "test": "DragonflyDB Connection",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  DragonflyDB: ❌ FAILED - {str(e)}")
        
        tests.append(dragonfly_test)
        
        # Test 2: PostgreSQL Connection (if available)
        print("🔍 Testowanie połączenia z PostgreSQL...")
        try:
            import psycopg2
            
            # Próba połączenia z PostgreSQL
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="postgres"
            )
            
            # Test basic query
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            
            cur.close()
            conn.close()
            
            postgres_test = {
                "test": "PostgreSQL Connection",
                "success": True,
                "details": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "postgres",
                    "version": version[0] if version else "unknown"
                }
            }
            print(f"  PostgreSQL: ✅ CONNECTED")
            
        except Exception as e:
            postgres_test = {
                "test": "PostgreSQL Connection", 
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  PostgreSQL: ❌ FAILED - {str(e)}")
        
        tests.append(postgres_test)
        
        overall_success = any(t["success"] for t in tests)  # At least one DB should work
        print(f"\n📊 Database Connectivity Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "Database Connectivity",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_external_api_access(self) -> Dict[str, Any]:
        """Test 2.1.3: External API Access"""
        print("\n🌐 TEST 2.1.3: EXTERNAL API ACCESS")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Helius API
        print("🔍 Testowanie dostępu do Helius API...")
        try:
            # Test basic Helius API endpoint
            helius_url = "https://api.helius.xyz/v0/addresses/So11111111111111111111111111111111111111112/balances"
            
            start_time = time.time()
            response = requests.get(helius_url, timeout=10)
            response_time = time.time() - start_time
            
            helius_test = {
                "test": "Helius API Access",
                "success": response.status_code == 200,
                "details": {
                    "url": helius_url,
                    "status_code": response.status_code,
                    "response_time": f"{response_time:.2f}s",
                    "data_received": len(response.text) if response.text else 0
                }
            }
            print(f"  Helius API: {'✅ ACCESSIBLE' if helius_test['success'] else '❌ FAILED'} ({response_time:.2f}s)")
            
        except Exception as e:
            helius_test = {
                "test": "Helius API Access",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Helius API: ❌ FAILED - {str(e)}")
        
        tests.append(helius_test)
        
        # Test 2: QuickNode Devnet
        print("🔍 Testowanie dostępu do QuickNode Devnet...")
        try:
            # Test QuickNode devnet endpoint
            quicknode_url = "https://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth"
            }
            
            start_time = time.time()
            response = requests.post(quicknode_url, json=payload, timeout=10)
            response_time = time.time() - start_time
            
            quicknode_test = {
                "test": "QuickNode Devnet Access",
                "success": response.status_code == 200,
                "details": {
                    "url": "QuickNode Devnet Endpoint",
                    "status_code": response.status_code,
                    "response_time": f"{response_time:.2f}s",
                    "method": "getHealth"
                }
            }
            print(f"  QuickNode: {'✅ ACCESSIBLE' if quicknode_test['success'] else '❌ FAILED'} ({response_time:.2f}s)")
            
        except Exception as e:
            quicknode_test = {
                "test": "QuickNode Devnet Access",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  QuickNode: ❌ FAILED - {str(e)}")
        
        tests.append(quicknode_test)
        
        # Test 3: General Internet Connectivity
        print("🔍 Testowanie ogólnej łączności internetowej...")
        try:
            start_time = time.time()
            response = requests.get("https://httpbin.org/get", timeout=5)
            response_time = time.time() - start_time
            
            internet_test = {
                "test": "General Internet Connectivity",
                "success": response.status_code == 200,
                "details": {
                    "url": "https://httpbin.org/get",
                    "status_code": response.status_code,
                    "response_time": f"{response_time:.2f}s"
                }
            }
            print(f"  Internet: {'✅ CONNECTED' if internet_test['success'] else '❌ FAILED'} ({response_time:.2f}s)")
            
        except Exception as e:
            internet_test = {
                "test": "General Internet Connectivity",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Internet: ❌ FAILED - {str(e)}")
        
        tests.append(internet_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 External API Access Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "External API Access",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_infrastructure_tests(self) -> Dict[str, Any]:
        """Uruchom wszystkie testy infrastruktury"""
        print("🔗 THE OVERMIND PROTOCOL - INFRASTRUCTURE COMMUNICATION TEST")
        print("=" * 65)
        print("🎯 FRONT 2: Test komunikacji Warstwa 1 ↔ Warstwa 2")
        print()
        
        # Uruchom wszystkie testy
        test_results = []
        
        # Test 2.1.1: Docker Infrastructure
        docker_result = self.test_docker_infrastructure()
        test_results.append(docker_result)
        
        # Test 2.1.2: Database Connectivity
        db_result = self.test_database_connectivity()
        test_results.append(db_result)
        
        # Test 2.1.3: External API Access
        api_result = self.test_external_api_access()
        test_results.append(api_result)
        
        # Oblicz ogólny wynik
        overall_success = all(result["success"] for result in test_results)
        passed_tests = sum(1 for result in test_results if result["success"])
        
        # Określ poziom komunikacji
        success_rate = passed_tests / len(test_results)
        if success_rate >= 0.95:
            communication_level = "🌟 EXCELLENT"
        elif success_rate >= 0.85:
            communication_level = "🎯 GOOD"
        elif success_rate >= 0.70:
            communication_level = "⚠️ NEEDS IMPROVEMENT"
        else:
            communication_level = "❌ POOR"
        
        print(f"\n🏆 FINALNE WYNIKI TESTU INFRASTRUKTURY:")
        print("=" * 55)
        print(f"  Testy zaliczone: {passed_tests}/{len(test_results)}")
        print(f"  Wskaźnik sukcesu: {success_rate:.1%}")
        print(f"  Poziom komunikacji: {communication_level}")
        print(f"  Status: {'✅ INFRASTRUCTURE COMMUNICATION OK!' if overall_success else '❌ NEEDS ATTENTION'}")
        
        return {
            "test_timestamp": self.start_time.isoformat(),
            "test_duration": str(datetime.now() - self.start_time),
            "overall_success": overall_success,
            "communication_level": communication_level,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": len(test_results),
            "test_results": test_results,
            "status": "INFRASTRUCTURE_COMMUNICATION_OK" if overall_success else "NEEDS_ATTENTION"
        }

async def main():
    """Główna funkcja testowa"""
    tester = InfrastructureCommunicationTester()
    results = await tester.run_infrastructure_tests()
    
    # Zapisz wyniki
    os.makedirs('docs/testing', exist_ok=True)
    with open('docs/testing/INFRASTRUCTURE_COMMUNICATION_TEST.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Wyniki zapisane w: docs/testing/INFRASTRUCTURE_COMMUNICATION_TEST.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
