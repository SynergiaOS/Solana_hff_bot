#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Regime Backtester
Historical regime analysis and accuracy validation
"""

import numpy as np
import pandas as pd
import asyncio
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from market_regime_detector import create_market_regime_detector, MarketRegime, MarketData
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('RegimeBacktester')

class RegimeBacktester:
    """
    Historical Regime Analysis and Backtesting
    
    Validates regime detection accuracy using historical data
    Optimizes parameters for maximum prediction accuracy
    """
    
    def __init__(self):
        """Initialize Regime Backtester"""
        self.regime_detector = create_market_regime_detector()
        
        # Backtesting configuration
        self.lookback_days = 30
        self.validation_window = 7  # Days to validate regime accuracy
        
        # Performance metrics
        self.accuracy_metrics = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'regime_accuracy': {},
            'allocation_performance': {},
            'false_positives': 0,
            'false_negatives': 0
        }
        
        logger.info("📊 Regime Backtester initialized")
        logger.info(f"🔍 Lookback period: {self.lookback_days} days")
        logger.info(f"⏰ Validation window: {self.validation_window} days")
    
    async def run_historical_analysis(self, symbol: str = "SOL") -> Dict[str, Any]:
        """Run comprehensive historical regime analysis"""
        try:
            logger.info(f"🔍 Starting historical analysis for {symbol}...")
            
            # Generate historical market data (simulated for now)
            historical_data = await self.generate_historical_data(symbol)
            
            # Run regime detection on historical data
            regime_predictions = await self.analyze_historical_regimes(historical_data)
            
            # Validate predictions against actual market outcomes
            validation_results = await self.validate_regime_predictions(regime_predictions, historical_data)
            
            # Calculate performance metrics
            performance_metrics = self.calculate_performance_metrics(validation_results)
            
            # Generate optimization recommendations
            optimization_recommendations = self.generate_optimization_recommendations(performance_metrics)
            
            # Create comprehensive report
            analysis_report = {
                'symbol': symbol,
                'analysis_period': f"{self.lookback_days} days",
                'total_data_points': len(historical_data),
                'regime_predictions': len(regime_predictions),
                'performance_metrics': performance_metrics,
                'optimization_recommendations': optimization_recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Historical analysis complete for {symbol}")
            logger.info(f"   Overall Accuracy: {performance_metrics.get('overall_accuracy', 0.0):.1%}")
            logger.info(f"   Best Regime: {performance_metrics.get('best_regime', 'unknown')}")
            
            return analysis_report
            
        except Exception as e:
            logger.error(f"❌ Error in historical analysis: {e}")
            return {'error': str(e)}
    
    async def generate_historical_data(self, symbol: str) -> List[MarketData]:
        """Generate historical market data for backtesting"""
        try:
            logger.info(f"📊 Generating historical data for {symbol}...")
            
            # For now, generate simulated historical data
            # In production, this would fetch real historical data from APIs
            
            historical_data = []
            base_price = 100.0
            base_volume = 1000000.0
            
            for i in range(self.lookback_days * 24):  # Hourly data
                # Simulate different market conditions
                if i < self.lookback_days * 8:  # First third - bull market
                    price_change = np.random.normal(0.5, 2.0)  # Positive bias
                    volume_multiplier = np.random.uniform(0.8, 2.0)
                elif i < self.lookback_days * 16:  # Second third - sideways
                    price_change = np.random.normal(0.0, 1.0)  # No bias
                    volume_multiplier = np.random.uniform(0.7, 1.3)
                else:  # Last third - bear market
                    price_change = np.random.normal(-0.3, 1.5)  # Negative bias
                    volume_multiplier = np.random.uniform(0.9, 2.5)
                
                # Calculate cumulative price
                base_price *= (1 + price_change / 100)
                current_volume = base_volume * volume_multiplier
                
                # Create market data point
                market_data = MarketData(
                    timestamp=datetime.now().timestamp() - (self.lookback_days * 24 - i) * 3600,
                    price=base_price,
                    volume_24h=current_volume,
                    price_change_1h=price_change,
                    price_change_24h=price_change * 24 + np.random.normal(0, 5),
                    price_change_7d=price_change * 168 + np.random.normal(0, 15),
                    market_cap=base_price * 1000000,
                    volatility=abs(price_change) / 100
                )
                
                historical_data.append(market_data)
            
            logger.info(f"📊 Generated {len(historical_data)} historical data points")
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ Error generating historical data: {e}")
            return []
    
    async def analyze_historical_regimes(self, historical_data: List[MarketData]) -> List[Dict[str, Any]]:
        """Analyze regimes for historical data"""
        try:
            logger.info("🔍 Analyzing historical regimes...")
            
            regime_predictions = []
            
            for i, market_data in enumerate(historical_data):
                # Update detector's historical data
                self.regime_detector.price_history.append(market_data.price)
                self.regime_detector.volume_history.append(market_data.volume_24h)
                
                # Keep only recent history
                if len(self.regime_detector.price_history) > 100:
                    self.regime_detector.price_history = self.regime_detector.price_history[-100:]
                if len(self.regime_detector.volume_history) > 100:
                    self.regime_detector.volume_history = self.regime_detector.volume_history[-100:]
                
                # Calculate indicators
                indicators = await self.regime_detector.calculate_indicators(market_data)
                
                # Analyze regime
                regime_analysis = self.regime_detector.analyze_regime(market_data, indicators)
                
                # Store prediction
                prediction = {
                    'timestamp': market_data.timestamp,
                    'regime': regime_analysis.regime,
                    'confidence': regime_analysis.confidence,
                    'allocation_multiplier': regime_analysis.allocation_multiplier,
                    'market_data': market_data,
                    'indicators': indicators
                }
                
                regime_predictions.append(prediction)
                
                # Log progress
                if i % 100 == 0:
                    logger.info(f"   Processed {i}/{len(historical_data)} data points...")
            
            logger.info(f"✅ Analyzed {len(regime_predictions)} regime predictions")
            return regime_predictions
            
        except Exception as e:
            logger.error(f"❌ Error analyzing historical regimes: {e}")
            return []
    
    async def validate_regime_predictions(self, predictions: List[Dict[str, Any]], historical_data: List[MarketData]) -> List[Dict[str, Any]]:
        """Validate regime predictions against actual market outcomes"""
        try:
            logger.info("✅ Validating regime predictions...")
            
            validation_results = []
            
            for i, prediction in enumerate(predictions[:-self.validation_window * 24]):  # Exclude last week for validation
                # Get future market data for validation
                future_data = historical_data[i + 1:i + self.validation_window * 24 + 1]
                
                if not future_data:
                    continue
                
                # Calculate actual market performance
                actual_performance = self.calculate_actual_performance(future_data)
                
                # Determine if regime prediction was accurate
                prediction_accuracy = self.evaluate_prediction_accuracy(prediction, actual_performance)
                
                # Store validation result
                validation_result = {
                    'prediction': prediction,
                    'actual_performance': actual_performance,
                    'accuracy': prediction_accuracy,
                    'regime_correct': prediction_accuracy['regime_correct'],
                    'allocation_effective': prediction_accuracy['allocation_effective']
                }
                
                validation_results.append(validation_result)
            
            logger.info(f"✅ Validated {len(validation_results)} predictions")
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Error validating predictions: {e}")
            return []
    
    def calculate_actual_performance(self, future_data: List[MarketData]) -> Dict[str, Any]:
        """Calculate actual market performance over validation window"""
        try:
            if not future_data:
                return {}
            
            start_price = future_data[0].price
            end_price = future_data[-1].price
            
            # Calculate performance metrics
            total_return = (end_price - start_price) / start_price
            max_price = max(data.price for data in future_data)
            min_price = min(data.price for data in future_data)
            max_drawdown = (max_price - min_price) / max_price
            
            # Calculate volatility
            price_changes = [(future_data[i].price - future_data[i-1].price) / future_data[i-1].price 
                           for i in range(1, len(future_data))]
            volatility = np.std(price_changes) if price_changes else 0.0
            
            # Determine actual regime based on performance
            if total_return > 0.05:  # >5% gain
                actual_regime = MarketRegime.BULL_STRONG if volatility < 0.02 else MarketRegime.BULL_WEAK
            elif total_return < -0.05:  # >5% loss
                actual_regime = MarketRegime.BEAR_STRONG if volatility < 0.02 else MarketRegime.BEAR_WEAK
            elif volatility > 0.03:  # High volatility
                actual_regime = MarketRegime.HIGH_VOLATILITY
            else:
                actual_regime = MarketRegime.SIDEWAYS
            
            return {
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'actual_regime': actual_regime,
                'price_trend': 'up' if total_return > 0 else 'down' if total_return < 0 else 'flat'
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating actual performance: {e}")
            return {}
    
    def evaluate_prediction_accuracy(self, prediction: Dict[str, Any], actual_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate accuracy of regime prediction"""
        try:
            predicted_regime = prediction['regime']
            actual_regime = actual_performance.get('actual_regime')
            
            # Check regime accuracy
            regime_correct = predicted_regime == actual_regime
            
            # Check allocation effectiveness
            predicted_multiplier = prediction['allocation_multiplier']
            actual_return = actual_performance.get('total_return', 0.0)
            
            # Allocation is effective if:
            # - High multiplier during positive returns
            # - Low multiplier during negative returns
            if actual_return > 0:
                allocation_effective = predicted_multiplier > 1.0
            elif actual_return < -0.02:  # Significant loss
                allocation_effective = predicted_multiplier < 0.8
            else:
                allocation_effective = True  # Neutral case
            
            return {
                'regime_correct': regime_correct,
                'allocation_effective': allocation_effective,
                'predicted_regime': predicted_regime.value,
                'actual_regime': actual_regime.value if actual_regime else 'unknown',
                'predicted_multiplier': predicted_multiplier,
                'actual_return': actual_return
            }
            
        except Exception as e:
            logger.error(f"❌ Error evaluating prediction accuracy: {e}")
            return {'regime_correct': False, 'allocation_effective': False}
    
    def calculate_performance_metrics(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            if not validation_results:
                return {}
            
            # Overall accuracy
            total_predictions = len(validation_results)
            correct_regime_predictions = sum(1 for result in validation_results if result['accuracy']['regime_correct'])
            effective_allocations = sum(1 for result in validation_results if result['accuracy']['allocation_effective'])
            
            overall_accuracy = correct_regime_predictions / total_predictions
            allocation_effectiveness = effective_allocations / total_predictions
            
            # Regime-specific accuracy
            regime_accuracy = {}
            for regime in MarketRegime:
                regime_predictions = [r for r in validation_results if r['prediction']['regime'] == regime]
                if regime_predictions:
                    correct = sum(1 for r in regime_predictions if r['accuracy']['regime_correct'])
                    regime_accuracy[regime.value] = correct / len(regime_predictions)
            
            # Best and worst performing regimes
            best_regime = max(regime_accuracy.items(), key=lambda x: x[1]) if regime_accuracy else ('unknown', 0.0)
            worst_regime = min(regime_accuracy.items(), key=lambda x: x[1]) if regime_accuracy else ('unknown', 0.0)
            
            return {
                'overall_accuracy': overall_accuracy,
                'allocation_effectiveness': allocation_effectiveness,
                'total_predictions': total_predictions,
                'correct_predictions': correct_regime_predictions,
                'regime_accuracy': regime_accuracy,
                'best_regime': best_regime[0],
                'best_regime_accuracy': best_regime[1],
                'worst_regime': worst_regime[0],
                'worst_regime_accuracy': worst_regime[1],
                'confidence_correlation': self.calculate_confidence_correlation(validation_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating performance metrics: {e}")
            return {}
    
    def calculate_confidence_correlation(self, validation_results: List[Dict[str, Any]]) -> float:
        """Calculate correlation between confidence and accuracy"""
        try:
            confidences = [r['prediction']['confidence'] for r in validation_results]
            accuracies = [1.0 if r['accuracy']['regime_correct'] else 0.0 for r in validation_results]
            
            if len(confidences) > 1:
                correlation = np.corrcoef(confidences, accuracies)[0, 1]
                return correlation if not np.isnan(correlation) else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating confidence correlation: {e}")
            return 0.0
    
    def generate_optimization_recommendations(self, performance_metrics: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on performance"""
        recommendations = []
        
        try:
            overall_accuracy = performance_metrics.get('overall_accuracy', 0.0)
            allocation_effectiveness = performance_metrics.get('allocation_effectiveness', 0.0)
            confidence_correlation = performance_metrics.get('confidence_correlation', 0.0)
            
            # Accuracy recommendations
            if overall_accuracy < 0.7:
                recommendations.append("Consider adjusting regime classification thresholds - accuracy below 70%")
            
            if allocation_effectiveness < 0.6:
                recommendations.append("Review allocation multipliers - effectiveness below 60%")
            
            if confidence_correlation < 0.3:
                recommendations.append("Improve confidence scoring - low correlation with accuracy")
            
            # Regime-specific recommendations
            regime_accuracy = performance_metrics.get('regime_accuracy', {})
            for regime, accuracy in regime_accuracy.items():
                if accuracy < 0.5:
                    recommendations.append(f"Improve {regime} detection - accuracy only {accuracy:.1%}")
            
            # General recommendations
            if not recommendations:
                recommendations.append("System performing well - consider fine-tuning for marginal improvements")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    async def optimize_parameters(self, symbol: str = "SOL") -> Dict[str, Any]:
        """Optimize regime detection parameters"""
        try:
            logger.info(f"⚙️ Optimizing parameters for {symbol}...")
            
            # Run analysis with current parameters
            baseline_analysis = await self.run_historical_analysis(symbol)
            baseline_accuracy = baseline_analysis.get('performance_metrics', {}).get('overall_accuracy', 0.0)
            
            logger.info(f"📊 Baseline accuracy: {baseline_accuracy:.1%}")
            
            # Test different parameter combinations
            # This is a simplified optimization - in production, use more sophisticated methods
            
            optimization_results = {
                'baseline_accuracy': baseline_accuracy,
                'optimized_parameters': {},
                'improvement': 0.0,
                'recommendations': baseline_analysis.get('optimization_recommendations', [])
            }
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"❌ Error optimizing parameters: {e}")
            return {'error': str(e)}

# Factory function
def create_regime_backtester() -> RegimeBacktester:
    """Create regime backtester instance"""
    return RegimeBacktester()

# Example usage
if __name__ == "__main__":
    async def test_backtesting():
        """Test regime backtesting"""
        backtester = create_regime_backtester()
        
        # Run historical analysis
        analysis = await backtester.run_historical_analysis("SOL")
        
        print("=== REGIME BACKTESTING RESULTS ===")
        print(f"Symbol: {analysis.get('symbol', 'unknown')}")
        print(f"Analysis Period: {analysis.get('analysis_period', 'unknown')}")
        print(f"Total Data Points: {analysis.get('total_data_points', 0)}")
        
        performance = analysis.get('performance_metrics', {})
        print(f"\nPerformance Metrics:")
        print(f"  Overall Accuracy: {performance.get('overall_accuracy', 0.0):.1%}")
        print(f"  Allocation Effectiveness: {performance.get('allocation_effectiveness', 0.0):.1%}")
        print(f"  Best Regime: {performance.get('best_regime', 'unknown')} ({performance.get('best_regime_accuracy', 0.0):.1%})")
        print(f"  Worst Regime: {performance.get('worst_regime', 'unknown')} ({performance.get('worst_regime_accuracy', 0.0):.1%})")
        
        recommendations = analysis.get('optimization_recommendations', [])
        print(f"\nOptimization Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    asyncio.run(test_backtesting())
