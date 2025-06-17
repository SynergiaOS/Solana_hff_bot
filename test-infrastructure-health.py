#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Infrastructure Health Test
Test infrastructure components with alternative ports
"""

import requests
import time
import subprocess
import sys

def test_endpoint(name, url, timeout=10):
    """Test if endpoint is healthy"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name}: Healthy ({response.status_code})")
            return True
        else:
            print(f"⚠️ {name}: Responding but not healthy ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: Not responding ({str(e)})")
        return False

def test_database(name, container, command):
    """Test database connectivity"""
    try:
        result = subprocess.run(
            ["docker", "exec", container] + command,
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {name}: Healthy")
            return True
        else:
            print(f"❌ {name}: Not healthy ({result.stderr})")
            return False
    except Exception as e:
        print(f"❌ {name}: Error testing ({str(e)})")
        return False

def main():
    print("🧠 THE OVERMIND PROTOCOL - Infrastructure Health Test")
    print("=" * 60)
    
    # Test HTTP endpoints
    endpoints = [
        ("Prometheus", "http://localhost:9091/-/healthy"),
        ("Grafana", "http://localhost:3002/api/health"),
        ("Chroma Vector DB", "http://localhost:8001/api/v1/heartbeat")
    ]
    
    healthy_endpoints = 0
    for name, url in endpoints:
        if test_endpoint(name, url):
            healthy_endpoints += 1
    
    # Test databases
    databases = [
        ("PostgreSQL", "overmind-postgres-test", ["pg_isready", "-U", "sniper"]),
        ("DragonflyDB", "overmind-dragonfly-test", ["redis-cli", "ping"])
    ]
    
    healthy_databases = 0
    for name, container, command in databases:
        if test_database(name, container, command):
            healthy_databases += 1
    
    # Calculate overall health
    total_services = len(endpoints) + len(databases)
    healthy_services = healthy_endpoints + healthy_databases
    health_rate = (healthy_services / total_services) * 100
    
    print("\n📊 Infrastructure Health Summary:")
    print(f"  Healthy Services: {healthy_services}/{total_services}")
    print(f"  Health Rate: {health_rate:.1f}%")
    
    if health_rate >= 80:
        print("🎉 Infrastructure is healthy!")
        return 0
    elif health_rate >= 60:
        print("⚠️ Infrastructure has some issues")
        return 1
    else:
        print("❌ Infrastructure has critical issues")
        return 2

if __name__ == "__main__":
    sys.exit(main())
