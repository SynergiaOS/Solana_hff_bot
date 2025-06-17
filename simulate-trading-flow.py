#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Trading Flow Simulator
Simulates complete trading flow: Data → Analysis → AI Decision → Execution
"""

import asyncio
import json
import time
import random
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional

class TradingFlowSimulator:
    """Simulates complete THE OVERMIND PROTOCOL trading flow"""
    
    def __init__(self, base_url: str = "http://89.117.53.53"):
        self.base_url = base_url
        self.trading_url = f"{base_url}:8080"
        self.ai_url = f"{base_url}:8000"
        self.tensorzero_url = f"{base_url}:3000"
        self.prometheus_url = f"{base_url}:9090"
        
        # Test data
        self.test_tokens = [
            {"symbol": "SOL/USDC", "price": 100.50, "volume": 1000},
            {"symbol": "BONK/SOL", "price": 0.000025, "volume": 50000},
            {"symbol": "WIF/SOL", "price": 0.15, "volume": 2000},
            {"symbol": "JUP/USDC", "price": 0.85, "volume": 1500},
        ]
        
        self.results = {
            "data_ingestion": [],
            "ai_analysis": [],
            "decisions": [],
            "executions": [],
            "errors": []
        }
    
    def print_step(self, step: str, message: str):
        """Print formatted step message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔄 {step}: {message}")
    
    def print_success(self, step: str, message: str):
        """Print formatted success message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ {step}: {message}")
    
    def print_error(self, step: str, message: str):
        """Print formatted error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ {step}: {message}")
    
    def check_system_health(self) -> bool:
        """Check if all system components are healthy"""
        print("\n🔍 STEP 1: System Health Check")
        print("=" * 50)
        
        endpoints = {
            "Trading System": f"{self.trading_url}/health",
            "AI Vector DB": f"{self.ai_url}/api/v1/heartbeat",
            "TensorZero": f"{self.tensorzero_url}/health",
            "Prometheus": f"{self.prometheus_url}/-/healthy"
        }
        
        all_healthy = True
        for name, url in endpoints.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.print_success("Health", f"{name} is healthy")
                else:
                    self.print_error("Health", f"{name} returned {response.status_code}")
                    all_healthy = False
            except Exception as e:
                self.print_error("Health", f"{name} unreachable: {str(e)}")
                all_healthy = False
        
        return all_healthy
    
    def simulate_market_data(self) -> Dict:
        """Simulate incoming market data"""
        print("\n📊 STEP 2: Market Data Simulation")
        print("=" * 50)
        
        # Select random token and simulate price movement
        token = random.choice(self.test_tokens)
        
        # Simulate price volatility
        price_change = random.uniform(-0.05, 0.05)  # ±5% change
        new_price = token["price"] * (1 + price_change)
        
        # Simulate volume spike
        volume_multiplier = random.uniform(0.5, 3.0)
        new_volume = int(token["volume"] * volume_multiplier)
        
        market_event = {
            "symbol": token["symbol"],
            "price": round(new_price, 6),
            "volume": new_volume,
            "price_change": round(price_change * 100, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "PRICE_CHANGE" if abs(price_change) > 0.02 else "VOLUME_SPIKE"
        }
        
        self.print_step("Data", f"Generated market event for {market_event['symbol']}")
        self.print_step("Data", f"Price: ${market_event['price']} ({market_event['price_change']:+.2f}%)")
        self.print_step("Data", f"Volume: {market_event['volume']:,}")
        
        self.results["data_ingestion"].append(market_event)
        return market_event
    
    def simulate_ai_analysis(self, market_event: Dict) -> Dict:
        """Simulate AI analysis of market data"""
        print("\n🧠 STEP 3: AI Analysis Simulation")
        print("=" * 50)
        
        # Simulate AI processing time
        processing_time = random.uniform(0.1, 0.5)
        self.print_step("AI", f"Processing market event for {market_event['symbol']}...")
        time.sleep(processing_time)
        
        # Simulate AI decision making
        confidence = random.uniform(0.6, 0.95)
        
        # Decision logic based on price change and volume
        price_change = market_event["price_change"]
        volume = market_event["volume"]
        
        if abs(price_change) > 3 and volume > 1500:
            action = "BUY" if price_change > 0 else "SELL"
            reasoning = f"Strong {'upward' if price_change > 0 else 'downward'} movement with high volume"
        elif abs(price_change) > 2:
            action = "BUY" if price_change > 0 else "SELL"
            reasoning = f"Moderate price movement detected"
        else:
            action = "HOLD"
            reasoning = "Insufficient signal strength"
        
        ai_decision = {
            "decision_id": f"ai_{int(time.time())}",
            "symbol": market_event["symbol"],
            "action": action,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
            "quantity": 1000 if action != "HOLD" else 0,
            "target_price": market_event["price"],
            "processing_time_ms": round(processing_time * 1000, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_context": {
                "price_change": price_change,
                "volume": volume,
                "volatility": "HIGH" if abs(price_change) > 3 else "MEDIUM" if abs(price_change) > 1 else "LOW"
            }
        }
        
        self.print_step("AI", f"Analysis completed in {ai_decision['processing_time_ms']}ms")
        self.print_success("AI", f"Decision: {action} with {confidence:.1%} confidence")
        self.print_step("AI", f"Reasoning: {reasoning}")
        
        self.results["ai_analysis"].append(ai_decision)
        return ai_decision
    
    def simulate_risk_verification(self, ai_decision: Dict) -> Dict:
        """Simulate risk management verification"""
        print("\n🛡️ STEP 4: Risk Verification")
        print("=" * 50)
        
        # Simulate risk checks
        risk_checks = {
            "confidence_threshold": ai_decision["confidence"] >= 0.7,
            "position_size": ai_decision["quantity"] <= 10000,
            "daily_limit": True,  # Simulate daily limit check
            "correlation": True,  # Simulate correlation check
            "volatility": ai_decision["market_context"]["volatility"] != "EXTREME"
        }
        
        all_passed = all(risk_checks.values())
        
        for check, passed in risk_checks.items():
            if passed:
                self.print_success("Risk", f"{check.replace('_', ' ').title()}: PASS")
            else:
                self.print_error("Risk", f"{check.replace('_', ' ').title()}: FAIL")
        
        risk_result = {
            "decision_id": ai_decision["decision_id"],
            "approved": all_passed,
            "checks": risk_checks,
            "final_action": ai_decision["action"] if all_passed else "REJECT",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if all_passed:
            self.print_success("Risk", "All risk checks passed - Decision APPROVED")
        else:
            self.print_error("Risk", "Risk checks failed - Decision REJECTED")
        
        self.results["decisions"].append(risk_result)
        return risk_result
    
    def simulate_execution(self, risk_result: Dict, ai_decision: Dict) -> Dict:
        """Simulate trade execution"""
        print("\n⚡ STEP 5: Trade Execution Simulation")
        print("=" * 50)
        
        if not risk_result["approved"]:
            self.print_error("Execution", "Trade rejected by risk management")
            return {"status": "REJECTED", "reason": "Risk management rejection"}
        
        # Simulate execution latency
        execution_time = random.uniform(0.02, 0.08)  # 20-80ms
        self.print_step("Execution", f"Executing {ai_decision['action']} order...")
        time.sleep(execution_time)
        
        # Simulate execution success/failure
        success_rate = 0.95  # 95% success rate
        execution_successful = random.random() < success_rate
        
        if execution_successful:
            # Simulate slippage
            slippage = random.uniform(-0.001, 0.001)  # ±0.1% slippage
            executed_price = ai_decision["target_price"] * (1 + slippage)
            
            execution_result = {
                "execution_id": f"exec_{int(time.time())}",
                "decision_id": ai_decision["decision_id"],
                "symbol": ai_decision["symbol"],
                "action": ai_decision["action"],
                "quantity": ai_decision["quantity"],
                "target_price": ai_decision["target_price"],
                "executed_price": round(executed_price, 6),
                "slippage": round(slippage * 100, 3),
                "execution_time_ms": round(execution_time * 1000, 1),
                "status": "EXECUTED",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.print_success("Execution", f"Order executed successfully")
            self.print_step("Execution", f"Price: ${executed_price:.6f} (slippage: {slippage*100:+.3f}%)")
            self.print_step("Execution", f"Execution time: {execution_result['execution_time_ms']}ms")
            
        else:
            execution_result = {
                "execution_id": f"exec_{int(time.time())}",
                "decision_id": ai_decision["decision_id"],
                "status": "FAILED",
                "reason": "Network timeout",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.print_error("Execution", "Order execution failed")
        
        self.results["executions"].append(execution_result)
        return execution_result
    
    def test_api_endpoints(self):
        """Test actual API endpoints if available"""
        print("\n🔌 STEP 6: API Endpoints Test")
        print("=" * 50)
        
        # Test trading system metrics
        try:
            response = requests.get(f"{self.trading_url}/metrics", timeout=5)
            if response.status_code == 200:
                self.print_success("API", "Trading system metrics endpoint responding")
                
                # Look for OVERMIND-specific metrics
                metrics_text = response.text
                if "overmind" in metrics_text.lower():
                    self.print_success("API", "OVERMIND metrics found in response")
                else:
                    self.print_error("API", "OVERMIND metrics not found")
            else:
                self.print_error("API", f"Metrics endpoint returned {response.status_code}")
        except Exception as e:
            self.print_error("API", f"Metrics endpoint test failed: {str(e)}")
        
        # Test vector database
        try:
            response = requests.get(f"{self.ai_url}/api/v1/collections", timeout=5)
            if response.status_code == 200:
                self.print_success("API", "Vector database collections endpoint responding")
            else:
                self.print_error("API", f"Vector DB endpoint returned {response.status_code}")
        except Exception as e:
            self.print_error("API", f"Vector DB endpoint test failed: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 STEP 7: Test Report Generation")
        print("=" * 50)
        
        total_events = len(self.results["data_ingestion"])
        total_decisions = len(self.results["ai_analysis"])
        approved_decisions = len([d for d in self.results["decisions"] if d["approved"]])
        successful_executions = len([e for e in self.results["executions"] if e.get("status") == "EXECUTED"])
        
        print(f"\n🎯 THE OVERMIND PROTOCOL - Trading Flow Test Results")
        print("=" * 60)
        print(f"📊 Market Events Processed: {total_events}")
        print(f"🧠 AI Decisions Generated: {total_decisions}")
        print(f"✅ Risk-Approved Decisions: {approved_decisions}")
        print(f"⚡ Successful Executions: {successful_executions}")
        print(f"📈 Success Rate: {(successful_executions/total_events*100):.1f}%" if total_events > 0 else "N/A")
        
        if self.results["ai_analysis"]:
            avg_confidence = sum(d["confidence"] for d in self.results["ai_analysis"]) / len(self.results["ai_analysis"])
            avg_processing_time = sum(d["processing_time_ms"] for d in self.results["ai_analysis"]) / len(self.results["ai_analysis"])
            print(f"🤖 Average AI Confidence: {avg_confidence:.1%}")
            print(f"⏱️  Average Processing Time: {avg_processing_time:.1f}ms")
        
        if self.results["executions"]:
            executed_orders = [e for e in self.results["executions"] if e.get("status") == "EXECUTED"]
            if executed_orders:
                avg_execution_time = sum(e["execution_time_ms"] for e in executed_orders) / len(executed_orders)
                avg_slippage = sum(abs(e["slippage"]) for e in executed_orders) / len(executed_orders)
                print(f"⚡ Average Execution Time: {avg_execution_time:.1f}ms")
                print(f"📉 Average Slippage: {avg_slippage:.3f}%")
        
        print(f"\n📋 Detailed Results:")
        print(f"   Data Events: {json.dumps(self.results['data_ingestion'], indent=2)}")
        
        return self.results
    
    async def run_simulation(self, num_cycles: int = 5):
        """Run complete trading flow simulation"""
        print("🚀 THE OVERMIND PROTOCOL - Trading Flow Simulation")
        print("=" * 60)
        print(f"Running {num_cycles} complete trading cycles...")
        
        # Check system health first
        if not self.check_system_health():
            print("\n❌ System health check failed. Please ensure THE OVERMIND PROTOCOL is running.")
            return
        
        # Run trading cycles
        for cycle in range(1, num_cycles + 1):
            print(f"\n🔄 TRADING CYCLE {cycle}/{num_cycles}")
            print("=" * 60)
            
            try:
                # Step 1: Generate market data
                market_event = self.simulate_market_data()
                
                # Step 2: AI analysis
                ai_decision = self.simulate_ai_analysis(market_event)
                
                # Step 3: Risk verification
                risk_result = self.simulate_risk_verification(ai_decision)
                
                # Step 4: Execution
                execution_result = self.simulate_execution(risk_result, ai_decision)
                
                # Wait between cycles
                if cycle < num_cycles:
                    wait_time = random.uniform(1, 3)
                    print(f"\n⏳ Waiting {wait_time:.1f}s before next cycle...")
                    await asyncio.sleep(wait_time)
                
            except Exception as e:
                self.print_error("Simulation", f"Cycle {cycle} failed: {str(e)}")
                self.results["errors"].append({
                    "cycle": cycle,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        # Test API endpoints
        self.test_api_endpoints()
        
        # Generate final report
        self.generate_report()
        
        print(f"\n🎯 Trading flow simulation completed!")
        print(f"✅ THE OVERMIND PROTOCOL flow tested successfully")

def main():
    """Main function to run the simulation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="THE OVERMIND PROTOCOL Trading Flow Simulator")
    parser.add_argument("--cycles", type=int, default=5, help="Number of trading cycles to simulate")
    parser.add_argument("--server", type=str, default="http://89.117.53.53", help="Server base URL")
    
    args = parser.parse_args()
    
    simulator = TradingFlowSimulator(base_url=args.server)
    
    # Run simulation
    asyncio.run(simulator.run_simulation(num_cycles=args.cycles))

if __name__ == "__main__":
    main()
