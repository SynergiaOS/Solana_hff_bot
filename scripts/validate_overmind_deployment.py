#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Deployment Validation Script
Comprehensive validation of complete system deployment
"""

import asyncio
import aiohttp
import redis
import time
import json
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add brain module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'brain', 'src'))

try:
    from overmind_brain.brain import OVERMINDBrain
    from overmind_brain.vector_memory import VectorMemory
except ImportError as e:
    print(f"❌ Failed to import OVERMIND modules: {e}")
    sys.exit(1)


class OVERMINDDeploymentValidator:
    """Comprehensive deployment validation for THE OVERMIND PROTOCOL"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def log_result(self, component: str, status: str, message: str, details: Dict[str, Any] = None):
        """Log validation result"""
        self.results[component] = {
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "error":
            self.errors.append(f"{component}: {message}")
        elif status == "warning":
            self.warnings.append(f"{component}: {message}")
        
        status_icon = "✅" if status == "success" else "⚠️" if status == "warning" else "❌"
        print(f"{status_icon} {component}: {message}")
    
    async def validate_redis_connection(self) -> bool:
        """Validate Redis/DragonflyDB connection"""
        try:
            redis_url = os.getenv("DRAGONFLY_URL", "redis://127.0.0.1:6379")
            r = redis.from_url(redis_url)
            
            # Test basic operations
            r.ping()
            r.set("overmind:test", "validation")
            value = r.get("overmind:test")
            r.delete("overmind:test")
            
            if value == b"validation":
                self.log_result("redis_connection", "success", "Redis/DragonflyDB connection successful")
                return True
            else:
                self.log_result("redis_connection", "error", "Redis data integrity test failed")
                return False
                
        except Exception as e:
            self.log_result("redis_connection", "error", f"Redis connection failed: {str(e)}")
            return False
    
    async def validate_vector_database(self) -> bool:
        """Validate vector database (Qdrant/ChromaDB) connection"""
        try:
            # Test Qdrant connection
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{qdrant_url}/collections") as response:
                    if response.status == 200:
                        collections = await response.json()
                        self.log_result("vector_database", "success", 
                                      f"Qdrant connection successful, {len(collections.get('result', {}).get('collections', []))} collections found")
                        return True
                    else:
                        self.log_result("vector_database", "error", f"Qdrant returned status {response.status}")
                        return False
                        
        except Exception as e:
            # Try ChromaDB as fallback
            try:
                chroma_url = os.getenv("VECTOR_DB_URL", "http://localhost:8000")
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{chroma_url}/api/v1/heartbeat") as response:
                        if response.status == 200:
                            self.log_result("vector_database", "success", "ChromaDB connection successful")
                            return True
                        else:
                            self.log_result("vector_database", "error", f"ChromaDB returned status {response.status}")
                            return False
            except Exception as chroma_error:
                self.log_result("vector_database", "error", 
                              f"Both Qdrant and ChromaDB failed: {str(e)}, {str(chroma_error)}")
                return False
    
    async def validate_tensorzero_gateway(self) -> bool:
        """Validate TensorZero gateway connection"""
        try:
            tensorzero_url = os.getenv("TENSORZERO_URL", "http://localhost:3000")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{tensorzero_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        self.log_result("tensorzero_gateway", "success", 
                                      f"TensorZero gateway healthy: {health_data.get('status', 'unknown')}")
                        return True
                    else:
                        self.log_result("tensorzero_gateway", "error", f"TensorZero returned status {response.status}")
                        return False
                        
        except Exception as e:
            self.log_result("tensorzero_gateway", "error", f"TensorZero connection failed: {str(e)}")
            return False
    
    async def validate_rust_executor(self) -> bool:
        """Validate Rust HFT executor connection"""
        try:
            executor_url = os.getenv("EXECUTOR_URL", "http://localhost:8080")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{executor_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        self.log_result("rust_executor", "success", 
                                      f"Rust executor healthy: {health_data.get('status', 'operational')}")
                        return True
                    else:
                        self.log_result("rust_executor", "error", f"Rust executor returned status {response.status}")
                        return False
                        
        except Exception as e:
            self.log_result("rust_executor", "warning", f"Rust executor connection failed: {str(e)} (may not be running)")
            return False
    
    async def validate_python_brain(self) -> bool:
        """Validate Python AI Brain functionality"""
        try:
            # Test brain initialization
            brain = OVERMINDBrain()
            
            # Test health check
            health_status = await brain.health_check()
            
            if health_status.get("brain_status") == "operational":
                components = health_status.get("components", {})
                healthy_components = sum(1 for comp in components.values() 
                                       if comp.get("status") in ["operational", "connected"])
                
                self.log_result("python_brain", "success", 
                              f"Python brain operational, {healthy_components}/{len(components)} components healthy",
                              {"health_status": health_status})
                return True
            else:
                self.log_result("python_brain", "error", 
                              f"Python brain not operational: {health_status.get('brain_status')}")
                return False
                
        except Exception as e:
            self.log_result("python_brain", "error", f"Python brain validation failed: {str(e)}")
            return False
    
    async def validate_end_to_end_flow(self) -> bool:
        """Validate complete end-to-end trading flow"""
        try:
            # Test market data processing
            test_market_data = {
                "symbol": "SOL",
                "price": 138.50,
                "volume": 1000000,
                "timestamp": datetime.now().isoformat()
            }
            
            brain = OVERMINDBrain()
            decision = await brain.process_market_data(test_market_data)
            
            if decision and "action" in decision and "confidence" in decision:
                self.log_result("end_to_end_flow", "success", 
                              f"E2E flow successful: {decision['action']} with {decision['confidence']:.2f} confidence",
                              {"decision": decision})
                return True
            else:
                self.log_result("end_to_end_flow", "error", "E2E flow failed: invalid decision format")
                return False
                
        except Exception as e:
            self.log_result("end_to_end_flow", "error", f"E2E flow validation failed: {str(e)}")
            return False
    
    async def validate_monitoring_systems(self) -> bool:
        """Validate monitoring and alerting systems"""
        try:
            # Test Prometheus
            prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{prometheus_url}/-/healthy") as response:
                    prometheus_healthy = response.status == 200
                
                # Test Grafana
                grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3001")
                async with session.get(f"{grafana_url}/api/health") as response:
                    grafana_healthy = response.status == 200
            
            if prometheus_healthy and grafana_healthy:
                self.log_result("monitoring_systems", "success", "Prometheus and Grafana both healthy")
                return True
            elif prometheus_healthy or grafana_healthy:
                self.log_result("monitoring_systems", "warning", 
                              f"Partial monitoring: Prometheus={prometheus_healthy}, Grafana={grafana_healthy}")
                return True
            else:
                self.log_result("monitoring_systems", "error", "Both Prometheus and Grafana unavailable")
                return False
                
        except Exception as e:
            self.log_result("monitoring_systems", "warning", f"Monitoring validation failed: {str(e)}")
            return False
    
    async def validate_api_keys(self) -> bool:
        """Validate required API keys are present"""
        required_keys = [
            "OPENAI_API_KEY",
            "HELIUS_API_KEY",
            "QUICKNODE_API_KEY"
        ]
        
        optional_keys = [
            "MISTRAL_API_KEY",
            "GROQ_API_KEY",
            "DEEPSEEK_API_KEY"
        ]
        
        missing_required = []
        missing_optional = []
        
        for key in required_keys:
            if not os.getenv(key):
                missing_required.append(key)
        
        for key in optional_keys:
            if not os.getenv(key):
                missing_optional.append(key)
        
        if missing_required:
            self.log_result("api_keys", "error", 
                          f"Missing required API keys: {', '.join(missing_required)}")
            return False
        elif missing_optional:
            self.log_result("api_keys", "warning", 
                          f"Missing optional API keys: {', '.join(missing_optional)}")
            return True
        else:
            self.log_result("api_keys", "success", "All API keys present")
            return True
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete deployment validation"""
        print("🚀 Starting THE OVERMIND PROTOCOL Deployment Validation")
        print("=" * 70)
        
        start_time = time.time()
        
        # Run all validations
        validations = [
            ("API Keys", self.validate_api_keys()),
            ("Redis Connection", self.validate_redis_connection()),
            ("Vector Database", self.validate_vector_database()),
            ("TensorZero Gateway", self.validate_tensorzero_gateway()),
            ("Rust Executor", self.validate_rust_executor()),
            ("Python Brain", self.validate_python_brain()),
            ("End-to-End Flow", self.validate_end_to_end_flow()),
            ("Monitoring Systems", self.validate_monitoring_systems())
        ]
        
        results = {}
        for name, validation in validations:
            print(f"\n🔍 Validating {name}...")
            results[name] = await validation
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate summary
        successful = sum(1 for result in results.values() if result)
        total = len(results)
        
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        overall_status = "READY" if successful == total and not self.errors else \
                        "PARTIAL" if successful > total // 2 else "FAILED"
        
        print(f"\n🎯 OVERALL STATUS: {overall_status}")
        
        return {
            "status": overall_status,
            "duration": duration,
            "successful": successful,
            "total": total,
            "errors": self.errors,
            "warnings": self.warnings,
            "results": self.results
        }


async def main():
    """Main validation function"""
    validator = OVERMINDDeploymentValidator()
    summary = await validator.run_full_validation()
    
    # Exit with appropriate code
    if summary["status"] == "READY":
        print("\n🎉 THE OVERMIND PROTOCOL is ready for deployment!")
        sys.exit(0)
    elif summary["status"] == "PARTIAL":
        print("\n⚠️  THE OVERMIND PROTOCOL has some issues but may be operational")
        sys.exit(1)
    else:
        print("\n❌ THE OVERMIND PROTOCOL is not ready for deployment")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
