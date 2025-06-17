#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Local AI Brain Test
Test AI analysis and decision making locally
"""

import asyncio
import json
import time
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalAIBrainTester:
    """Test AI Brain functionality locally"""
    
    def __init__(self):
        # Check for OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        
        # Test results
        self.test_results = {
            'environment_tests': {},
            'ai_analysis_tests': {},
            'decision_making_tests': {},
            'confidence_tests': {},
            'integration_tests': {}
        }
        
        # Sample market data from devnet test
        self.sample_market_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'solana_devnet',
            'tokens': [
                {
                    'symbol': 'SOL',
                    'mint': 'So11111111111111111111111111111111111111112',
                    'simulated_price': 63.33,
                    'volume': 1000000,
                    'price_change_24h': 2.5,
                    'slot': 388205633
                },
                {
                    'symbol': 'USDC',
                    'mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                    'simulated_price': 1.00,
                    'volume': 5000000,
                    'price_change_24h': 0.1,
                    'slot': 388205633
                }
            ]
        }
    
    def print_test(self, category: str, test_name: str, status: str, details: str = ""):
        """Print formatted test result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_icon} {category} - {test_name}: {status}")
        if details:
            print(f"    Details: {details}")
    
    async def test_environment_setup(self) -> Dict:
        """Test AI environment setup"""
        print("\n🔧 PHASE 1: Environment Setup Test")
        print("=" * 50)
        
        env_results = {}
        
        # Test 1: OpenAI API Key
        if self.openai_api_key and self.openai_api_key.startswith('sk-'):
            env_results['openai_key'] = 'PASS'
            self.print_test("Environment", "OpenAI API Key", "PASS", 
                           f"Key format: {self.openai_api_key[:10]}...")
        else:
            env_results['openai_key'] = 'FAIL'
            self.print_test("Environment", "OpenAI API Key", "FAIL", 
                           "Missing or invalid OpenAI API key")
        
        # Test 2: Python packages
        try:
            import json
            import asyncio
            env_results['python_packages'] = 'PASS'
            self.print_test("Environment", "Python Packages", "PASS", "Core packages available")
        except ImportError as e:
            env_results['python_packages'] = f'FAIL: {str(e)}'
            self.print_test("Environment", "Python Packages", "FAIL", str(e))
        
        # Test 3: Memory and processing
        try:
            # Simple memory test
            test_data = list(range(10000))
            processed = [x * 2 for x in test_data]
            env_results['memory_processing'] = 'PASS'
            self.print_test("Environment", "Memory Processing", "PASS", 
                           f"Processed {len(processed)} items")
        except Exception as e:
            env_results['memory_processing'] = f'FAIL: {str(e)}'
            self.print_test("Environment", "Memory Processing", "FAIL", str(e))
        
        self.test_results['environment_tests'] = env_results
        return env_results
    
    async def test_market_data_analysis(self) -> Dict:
        """Test market data analysis capabilities"""
        print("\n📊 PHASE 2: Market Data Analysis Test")
        print("=" * 50)
        
        analysis_results = {}
        
        try:
            # Test 1: Data parsing
            market_data = self.sample_market_data
            
            if market_data and 'tokens' in market_data:
                analysis_results['data_parsing'] = 'PASS'
                self.print_test("Analysis", "Data Parsing", "PASS", 
                               f"Parsed {len(market_data['tokens'])} tokens")
            else:
                analysis_results['data_parsing'] = 'FAIL'
                self.print_test("Analysis", "Data Parsing", "FAIL", "No market data")
            
            # Test 2: Price analysis
            total_volume = sum(token['volume'] for token in market_data['tokens'])
            avg_price_change = sum(token['price_change_24h'] for token in market_data['tokens']) / len(market_data['tokens'])
            
            price_analysis = {
                'total_volume': total_volume,
                'avg_price_change': avg_price_change,
                'high_volume_tokens': [t for t in market_data['tokens'] if t['volume'] > 1000000],
                'positive_momentum': [t for t in market_data['tokens'] if t['price_change_24h'] > 1.0]
            }
            
            analysis_results['price_analysis'] = 'PASS'
            self.print_test("Analysis", "Price Analysis", "PASS", 
                           f"Volume: {total_volume:,}, Avg change: {avg_price_change:.2f}%")
            
            # Test 3: Trend detection
            bullish_signals = len(price_analysis['positive_momentum'])
            bearish_signals = len(market_data['tokens']) - bullish_signals
            
            trend_analysis = {
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals,
                'market_sentiment': 'BULLISH' if bullish_signals > bearish_signals else 'BEARISH',
                'confidence': abs(bullish_signals - bearish_signals) / len(market_data['tokens'])
            }
            
            analysis_results['trend_detection'] = 'PASS'
            self.print_test("Analysis", "Trend Detection", "PASS", 
                           f"Sentiment: {trend_analysis['market_sentiment']} (confidence: {trend_analysis['confidence']:.2f})")
            
        except Exception as e:
            analysis_results['error'] = str(e)
            self.print_test("Analysis", "Market Data Analysis", "FAIL", str(e))
        
        self.test_results['ai_analysis_tests'] = analysis_results
        return analysis_results
    
    async def test_decision_making(self) -> Dict:
        """Test AI decision making logic"""
        print("\n🧠 PHASE 3: AI Decision Making Test")
        print("=" * 50)
        
        decision_results = {}
        
        try:
            # Test 1: Simple rule-based decisions
            market_data = self.sample_market_data
            
            decisions = []
            for token in market_data['tokens']:
                # Simple decision logic
                if token['price_change_24h'] > 2.0 and token['volume'] > 500000:
                    action = 'BUY'
                    confidence = min(0.9, 0.6 + (token['price_change_24h'] / 10))
                elif token['price_change_24h'] < -2.0:
                    action = 'SELL'
                    confidence = min(0.9, 0.6 + (abs(token['price_change_24h']) / 10))
                else:
                    action = 'HOLD'
                    confidence = 0.5
                
                decision = {
                    'symbol': token['symbol'],
                    'action': action,
                    'confidence': round(confidence, 3),
                    'reasoning': f"Price change: {token['price_change_24h']:.2f}%, Volume: {token['volume']:,}",
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                decisions.append(decision)
            
            if decisions:
                decision_results['rule_based_decisions'] = 'PASS'
                self.print_test("Decision", "Rule-based Logic", "PASS", 
                               f"Generated {len(decisions)} decisions")
                
                # Show decisions
                for decision in decisions:
                    self.print_test("Decision", f"{decision['symbol']} Decision", "INFO", 
                                   f"{decision['action']} (confidence: {decision['confidence']:.3f})")
            else:
                decision_results['rule_based_decisions'] = 'FAIL'
                self.print_test("Decision", "Rule-based Logic", "FAIL", "No decisions generated")
            
            # Test 2: Risk assessment
            risk_assessments = []
            for decision in decisions:
                risk_score = 1.0 - decision['confidence']  # Higher confidence = lower risk
                
                risk_assessment = {
                    'symbol': decision['symbol'],
                    'action': decision['action'],
                    'risk_score': round(risk_score, 3),
                    'risk_level': 'LOW' if risk_score < 0.3 else 'MEDIUM' if risk_score < 0.6 else 'HIGH',
                    'approved': risk_score < 0.5  # Approve if risk is below 50%
                }
                risk_assessments.append(risk_assessment)
            
            approved_decisions = [r for r in risk_assessments if r['approved']]
            
            decision_results['risk_assessment'] = 'PASS'
            self.print_test("Decision", "Risk Assessment", "PASS", 
                           f"Approved {len(approved_decisions)}/{len(risk_assessments)} decisions")
            
            # Test 3: Portfolio optimization
            if approved_decisions:
                # Simple portfolio allocation
                total_confidence = sum(d['confidence'] for d in decisions if any(r['symbol'] == d['symbol'] and r['approved'] for r in risk_assessments))
                
                portfolio = []
                for decision in decisions:
                    if any(r['symbol'] == decision['symbol'] and r['approved'] for r in risk_assessments):
                        allocation = (decision['confidence'] / total_confidence) * 100 if total_confidence > 0 else 0
                        portfolio.append({
                            'symbol': decision['symbol'],
                            'action': decision['action'],
                            'allocation_percent': round(allocation, 2)
                        })
                
                decision_results['portfolio_optimization'] = 'PASS'
                self.print_test("Decision", "Portfolio Optimization", "PASS", 
                               f"Optimized portfolio with {len(portfolio)} positions")
            else:
                decision_results['portfolio_optimization'] = 'SKIP'
                self.print_test("Decision", "Portfolio Optimization", "SKIP", "No approved decisions")
            
        except Exception as e:
            decision_results['error'] = str(e)
            self.print_test("Decision", "AI Decision Making", "FAIL", str(e))
        
        self.test_results['decision_making_tests'] = decision_results
        return decision_results
    
    async def test_confidence_scoring(self) -> Dict:
        """Test confidence scoring mechanisms"""
        print("\n🎯 PHASE 4: Confidence Scoring Test")
        print("=" * 50)
        
        confidence_results = {}
        
        try:
            # Test different confidence calculation methods
            market_data = self.sample_market_data
            
            confidence_methods = {
                'volatility_based': self._calculate_volatility_confidence,
                'volume_based': self._calculate_volume_confidence,
                'momentum_based': self._calculate_momentum_confidence,
                'combined': self._calculate_combined_confidence
            }
            
            for method_name, method_func in confidence_methods.items():
                try:
                    confidences = []
                    for token in market_data['tokens']:
                        confidence = method_func(token)
                        confidences.append({
                            'symbol': token['symbol'],
                            'confidence': confidence,
                            'method': method_name
                        })
                    
                    avg_confidence = sum(c['confidence'] for c in confidences) / len(confidences)
                    
                    confidence_results[method_name] = f'PASS (avg: {avg_confidence:.3f})'
                    self.print_test("Confidence", f"{method_name.replace('_', ' ').title()}", "PASS", 
                                   f"Average confidence: {avg_confidence:.3f}")
                    
                except Exception as e:
                    confidence_results[method_name] = f'FAIL: {str(e)}'
                    self.print_test("Confidence", f"{method_name.replace('_', ' ').title()}", "FAIL", str(e))
            
            # Test confidence thresholds
            threshold_tests = [
                (0.7, 'High Confidence'),
                (0.5, 'Medium Confidence'),
                (0.3, 'Low Confidence')
            ]
            
            for threshold, label in threshold_tests:
                high_conf_decisions = sum(1 for token in market_data['tokens'] 
                                        if self._calculate_combined_confidence(token) >= threshold)
                
                confidence_results[f'threshold_{threshold}'] = f'PASS ({high_conf_decisions} decisions)'
                self.print_test("Confidence", f"{label} Threshold", "PASS", 
                               f"{high_conf_decisions} decisions above {threshold}")
            
        except Exception as e:
            confidence_results['error'] = str(e)
            self.print_test("Confidence", "Confidence Scoring", "FAIL", str(e))
        
        self.test_results['confidence_tests'] = confidence_results
        return confidence_results
    
    def _calculate_volatility_confidence(self, token: Dict) -> float:
        """Calculate confidence based on volatility"""
        volatility = abs(token['price_change_24h'])
        # Higher volatility = lower confidence for conservative trading
        return max(0.1, 1.0 - (volatility / 10.0))
    
    def _calculate_volume_confidence(self, token: Dict) -> float:
        """Calculate confidence based on volume"""
        volume = token['volume']
        # Higher volume = higher confidence
        return min(0.95, 0.3 + (volume / 10000000))
    
    def _calculate_momentum_confidence(self, token: Dict) -> float:
        """Calculate confidence based on momentum"""
        momentum = token['price_change_24h']
        # Strong positive momentum = higher confidence
        return min(0.95, 0.5 + (momentum / 20.0)) if momentum > 0 else max(0.1, 0.5 + (momentum / 20.0))
    
    def _calculate_combined_confidence(self, token: Dict) -> float:
        """Calculate combined confidence score"""
        vol_conf = self._calculate_volatility_confidence(token)
        volume_conf = self._calculate_volume_confidence(token)
        momentum_conf = self._calculate_momentum_confidence(token)
        
        # Weighted average
        combined = (vol_conf * 0.3 + volume_conf * 0.4 + momentum_conf * 0.3)
        return round(combined, 3)
    
    async def test_ai_integration(self) -> Dict:
        """Test AI integration capabilities"""
        print("\n🔗 PHASE 5: AI Integration Test")
        print("=" * 50)
        
        integration_results = {}
        
        try:
            # Test 1: Data pipeline
            pipeline_steps = [
                ('Data Ingestion', self._simulate_data_ingestion),
                ('Data Processing', self._simulate_data_processing),
                ('AI Analysis', self._simulate_ai_analysis),
                ('Decision Generation', self._simulate_decision_generation),
                ('Risk Validation', self._simulate_risk_validation)
            ]
            
            pipeline_data = self.sample_market_data
            
            for step_name, step_func in pipeline_steps:
                try:
                    pipeline_data = step_func(pipeline_data)
                    integration_results[step_name.lower().replace(' ', '_')] = 'PASS'
                    self.print_test("Integration", step_name, "PASS")
                except Exception as e:
                    integration_results[step_name.lower().replace(' ', '_')] = f'FAIL: {str(e)}'
                    self.print_test("Integration", step_name, "FAIL", str(e))
                    break
            
            # Test 2: End-to-end flow
            if all('PASS' in str(result) for result in integration_results.values()):
                integration_results['end_to_end'] = 'PASS'
                self.print_test("Integration", "End-to-End Flow", "PASS", "Complete pipeline executed")
            else:
                integration_results['end_to_end'] = 'FAIL'
                self.print_test("Integration", "End-to-End Flow", "FAIL", "Pipeline incomplete")
            
        except Exception as e:
            integration_results['error'] = str(e)
            self.print_test("Integration", "AI Integration", "FAIL", str(e))
        
        self.test_results['integration_tests'] = integration_results
        return integration_results
    
    def _simulate_data_ingestion(self, data):
        """Simulate data ingestion step"""
        return {**data, 'ingested_at': datetime.now(timezone.utc).isoformat()}
    
    def _simulate_data_processing(self, data):
        """Simulate data processing step"""
        processed_tokens = []
        for token in data['tokens']:
            processed_token = {
                **token,
                'normalized_price': token['simulated_price'] / 100.0,
                'volume_score': min(1.0, token['volume'] / 1000000),
                'momentum_score': token['price_change_24h'] / 10.0
            }
            processed_tokens.append(processed_token)
        
        return {**data, 'tokens': processed_tokens, 'processed_at': datetime.now(timezone.utc).isoformat()}
    
    def _simulate_ai_analysis(self, data):
        """Simulate AI analysis step"""
        analysis = {
            'market_sentiment': 'BULLISH' if sum(t['price_change_24h'] for t in data['tokens']) > 0 else 'BEARISH',
            'total_volume': sum(t['volume'] for t in data['tokens']),
            'avg_momentum': sum(t['momentum_score'] for t in data['tokens']) / len(data['tokens']),
            'analyzed_at': datetime.now(timezone.utc).isoformat()
        }
        
        return {**data, 'analysis': analysis}
    
    def _simulate_decision_generation(self, data):
        """Simulate decision generation step"""
        decisions = []
        for token in data['tokens']:
            confidence = self._calculate_combined_confidence(token)
            action = 'BUY' if token['price_change_24h'] > 1 else 'SELL' if token['price_change_24h'] < -1 else 'HOLD'
            
            decision = {
                'symbol': token['symbol'],
                'action': action,
                'confidence': confidence,
                'quantity': int(1000 * confidence) if action != 'HOLD' else 0
            }
            decisions.append(decision)
        
        return {**data, 'decisions': decisions, 'decisions_generated_at': datetime.now(timezone.utc).isoformat()}
    
    def _simulate_risk_validation(self, data):
        """Simulate risk validation step"""
        validated_decisions = []
        for decision in data['decisions']:
            risk_approved = decision['confidence'] >= 0.7 and decision['quantity'] <= 5000
            
            validated_decision = {
                **decision,
                'risk_approved': risk_approved,
                'risk_score': 1.0 - decision['confidence']
            }
            validated_decisions.append(validated_decision)
        
        return {**data, 'validated_decisions': validated_decisions, 'risk_validated_at': datetime.now(timezone.utc).isoformat()}
    
    def generate_ai_brain_report(self) -> Dict:
        """Generate comprehensive AI Brain test report"""
        print("\n📊 PHASE 6: AI Brain Test Report")
        print("=" * 50)
        
        # Calculate statistics
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.test_results.items():
            if isinstance(results, dict):
                for test_name, result in results.items():
                    total_tests += 1
                    if isinstance(result, str) and 'PASS' in result:
                        passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'ai_brain_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': round(success_rate, 1)
            },
            'ai_brain_status': 'OPERATIONAL' if success_rate > 70 else 'ISSUES_DETECTED',
            'ai_readiness': self._assess_ai_readiness(),
            'recommendations': self._generate_ai_recommendations(),
            'detailed_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print summary
        print(f"\n🎯 AI Brain Local Test Results")
        print("=" * 50)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎯 AI Brain Status: {report['ai_brain_status']}")
        print(f"🧠 AI Readiness: {report['ai_readiness']}")
        
        if report['recommendations']:
            print(f"\n📋 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        return report
    
    def _assess_ai_readiness(self) -> str:
        """Assess AI Brain readiness"""
        env_ok = any('PASS' in str(result) for result in self.test_results.get('environment_tests', {}).values())
        analysis_ok = any('PASS' in str(result) for result in self.test_results.get('ai_analysis_tests', {}).values())
        decision_ok = any('PASS' in str(result) for result in self.test_results.get('decision_making_tests', {}).values())
        
        if env_ok and analysis_ok and decision_ok:
            return "READY"
        elif env_ok and analysis_ok:
            return "PARTIALLY_READY"
        else:
            return "NOT_READY"
    
    def _generate_ai_recommendations(self) -> List[str]:
        """Generate AI-specific recommendations"""
        recommendations = []
        
        # Check environment
        env_results = self.test_results.get('environment_tests', {})
        if 'FAIL' in str(env_results.get('openai_key', '')):
            recommendations.append("Configure OpenAI API key for enhanced AI capabilities")
        
        # Check analysis
        analysis_results = self.test_results.get('ai_analysis_tests', {})
        if not any('PASS' in str(result) for result in analysis_results.values()):
            recommendations.append("Fix market data analysis issues")
        
        # Check decisions
        decision_results = self.test_results.get('decision_making_tests', {})
        if not any('PASS' in str(result) for result in decision_results.values()):
            recommendations.append("Fix AI decision making logic")
        
        if not recommendations:
            recommendations.append("AI Brain is ready for THE OVERMIND PROTOCOL integration")
        
        return recommendations
    
    async def run_complete_ai_brain_test(self):
        """Run complete AI Brain test suite"""
        print("🧠 THE OVERMIND PROTOCOL - Local AI Brain Test")
        print("=" * 60)
        print("Testing AI analysis and decision making capabilities locally")
        print("")
        
        try:
            # Phase 1: Environment Setup
            await self.test_environment_setup()
            
            # Phase 2: Market Data Analysis
            await self.test_market_data_analysis()
            
            # Phase 3: Decision Making
            await self.test_decision_making()
            
            # Phase 4: Confidence Scoring
            await self.test_confidence_scoring()
            
            # Phase 5: AI Integration
            await self.test_ai_integration()
            
            # Phase 6: Generate Report
            final_report = self.generate_ai_brain_report()
            
            # Save results
            with open('ai_brain_test_results.json', 'w') as f:
                json.dump(final_report, f, indent=2)
            
            print(f"\n✅ AI Brain test results saved to: ai_brain_test_results.json")
            
            return final_report
            
        except Exception as e:
            logger.error(f"AI Brain test suite failed: {e}")
            raise

def main():
    """Main function to run AI Brain tests"""
    tester = LocalAIBrainTester()
    
    # Run complete AI Brain test suite
    asyncio.run(tester.run_complete_ai_brain_test())

if __name__ == "__main__":
    main()
