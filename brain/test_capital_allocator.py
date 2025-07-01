#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Capital Allocator Unit Tests
Comprehensive testing of dynamic capital allocation system
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add brain directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from capital_allocator import CapitalAllocator, AllocationParams, SignalQuality

class TestCapitalAllocator(unittest.TestCase):
    """Unit tests for CapitalAllocator"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock Redis client
        self.mock_redis = Mock()
        self.allocator = CapitalAllocator(redis_client=self.mock_redis)
    
    def test_initialization(self):
        """Test CapitalAllocator initialization"""
        self.assertIsInstance(self.allocator.params, AllocationParams)
        self.assertEqual(self.allocator.params.max_allocation, 0.25)
        self.assertEqual(self.allocator.params.confidence_threshold, 0.5)
        self.assertIn('memecoin_hunter', self.allocator.strategy_performance)
    
    def test_below_threshold_signal(self):
        """Test signals below confidence threshold"""
        allocation, details = self.allocator.calculate_position_size(
            signal_confidence=0.3,
            strategy="memecoin_hunter"
        )
        
        self.assertEqual(allocation, 0.0)
        self.assertEqual(details["reason"], "below_threshold")
        self.assertLess(details["composite_score"], 0.5)
    
    def test_minimum_threshold_signal(self):
        """Test signals at minimum threshold"""
        allocation, details = self.allocator.calculate_position_size(
            signal_confidence=0.6,
            strategy="memecoin_hunter"
        )
        
        self.assertGreater(allocation, 0.0)
        self.assertLessEqual(allocation, self.allocator.params.max_allocation)
        self.assertIn("allocation_reasoning", details)
    
    def test_high_confidence_signal(self):
        """Test high confidence signals"""
        allocation, details = self.allocator.calculate_position_size(
            signal_confidence=0.9,
            strategy="governance_alpha_hunter"
        )
        
        self.assertGreater(allocation, 0.05)  # Should get significant allocation
        self.assertLessEqual(allocation, self.allocator.params.max_allocation)
        self.assertEqual(details["strategy"], "governance_alpha_hunter")
    
    def test_maximum_confidence_signal(self):
        """Test maximum confidence signals"""
        allocation, details = self.allocator.calculate_position_size(
            signal_confidence=0.98,
            strategy="governance_alpha_hunter"
        )
        
        self.assertGreater(allocation, 0.1)  # Should get large allocation
        self.assertLessEqual(allocation, self.allocator.params.max_allocation)
    
    def test_strategy_performance_impact(self):
        """Test strategy performance impact on allocation"""
        # Test high-performing strategy
        allocation_high, _ = self.allocator.calculate_position_size(
            signal_confidence=0.8,
            strategy="governance_alpha_hunter"  # Higher performance
        )
        
        # Test lower-performing strategy
        allocation_low, _ = self.allocator.calculate_position_size(
            signal_confidence=0.8,
            strategy="high_vol_sniper"  # Lower performance
        )
        
        self.assertGreater(allocation_high, allocation_low)
    
    def test_market_regime_detection(self):
        """Test market regime detection"""
        # Bull market
        regime = self.allocator.detect_market_regime({
            "price_change_24h": 15.0,
            "volatility": 0.3
        })
        self.assertEqual(regime, "bull_market")
        
        # Bear market
        regime = self.allocator.detect_market_regime({
            "price_change_24h": -15.0,
            "volatility": 0.3
        })
        self.assertEqual(regime, "bear_market")
        
        # High volatility
        regime = self.allocator.detect_market_regime({
            "price_change_24h": 5.0,
            "volatility": 0.9
        })
        self.assertEqual(regime, "high_volatility")
        
        # Sideways
        regime = self.allocator.detect_market_regime({
            "price_change_24h": 2.0,
            "volatility": 0.3
        })
        self.assertEqual(regime, "sideways")
    
    def test_market_regime_impact_on_allocation(self):
        """Test market regime impact on position sizing"""
        base_confidence = 0.8
        strategy = "memecoin_hunter"
        
        # Bull market should increase allocation
        allocation_bull, _ = self.allocator.calculate_position_size(
            signal_confidence=base_confidence,
            strategy=strategy,
            market_data={"price_change_24h": 15.0, "volatility": 0.3}
        )
        
        # Bear market should decrease allocation
        allocation_bear, _ = self.allocator.calculate_position_size(
            signal_confidence=base_confidence,
            strategy=strategy,
            market_data={"price_change_24h": -15.0, "volatility": 0.3}
        )
        
        self.assertGreater(allocation_bull, allocation_bear)
    
    def test_portfolio_heat_limit(self):
        """Test portfolio heat limit functionality"""
        # Set high portfolio exposure
        self.allocator.current_exposure = 0.55  # 55% exposure
        
        allocation, details = self.allocator.calculate_position_size(
            signal_confidence=0.9,
            strategy="governance_alpha_hunter"
        )
        
        # Should be limited by remaining capacity (5%)
        self.assertLessEqual(allocation, 0.05)
        
        # Test complete heat limit
        self.allocator.current_exposure = 0.6  # 60% exposure (at limit)
        
        allocation, details = self.allocator.calculate_position_size(
            signal_confidence=0.95,
            strategy="governance_alpha_hunter"
        )
        
        self.assertEqual(allocation, 0.0)
    
    def test_base_allocation_curve(self):
        """Test base allocation calculation curve"""
        # Test allocation curve progression
        test_scores = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
        allocations = [self.allocator.calculate_base_allocation(score) for score in test_scores]
        
        # Should be monotonically increasing
        for i in range(1, len(allocations)):
            self.assertGreaterEqual(allocations[i], allocations[i-1])
        
        # Specific thresholds
        self.assertEqual(self.allocator.calculate_base_allocation(0.4), 0.0)
        self.assertGreater(self.allocator.calculate_base_allocation(0.6), 0.0)
        self.assertGreater(self.allocator.calculate_base_allocation(0.9), 0.1)
    
    def test_signal_quality_assessment(self):
        """Test signal quality assessment"""
        signal_quality = self.allocator.assess_signal_quality(
            confidence=0.8,
            strategy="governance_alpha_hunter",
            market_data={"price_change_24h": 5.0, "volatility": 0.3}
        )
        
        self.assertIsInstance(signal_quality, SignalQuality)
        self.assertEqual(signal_quality.confidence_score, 0.8)
        self.assertGreater(signal_quality.composite_score, 0.0)
        self.assertLessEqual(signal_quality.composite_score, 1.0)
    
    def test_portfolio_exposure_update(self):
        """Test portfolio exposure tracking"""
        initial_exposure = self.allocator.current_exposure
        
        self.allocator.update_portfolio_exposure(0.1)
        self.assertEqual(self.allocator.current_exposure, initial_exposure + 0.1)
        
        # Test bounds
        self.allocator.update_portfolio_exposure(1.0)
        self.assertLessEqual(self.allocator.current_exposure, 1.0)
    
    def test_strategy_performance_update(self):
        """Test strategy performance tracking"""
        initial_performance = self.allocator.strategy_performance["memecoin_hunter"]
        
        # Test successful trade
        self.allocator.update_strategy_performance("memecoin_hunter", True, 0.05)
        self.assertGreater(
            self.allocator.strategy_performance["memecoin_hunter"], 
            initial_performance
        )
        
        # Test failed trade
        self.allocator.update_strategy_performance("memecoin_hunter", False, -0.02)
        self.assertLess(
            self.allocator.strategy_performance["memecoin_hunter"], 
            initial_performance + 0.05
        )
    
    def test_allocation_stats(self):
        """Test allocation statistics"""
        stats = self.allocator.get_allocation_stats()
        
        self.assertIn("current_exposure", stats)
        self.assertIn("max_portfolio_heat", stats)
        self.assertIn("remaining_capacity", stats)
        self.assertIn("strategy_performance", stats)
        self.assertIn("allocation_params", stats)
        
        # Test remaining capacity calculation
        expected_remaining = self.allocator.max_portfolio_heat - self.allocator.current_exposure
        self.assertEqual(stats["remaining_capacity"], expected_remaining)
    
    def test_error_handling(self):
        """Test error handling in position size calculation"""
        # Test with invalid strategy
        allocation, details = self.allocator.calculate_position_size(
            signal_confidence=0.8,
            strategy="invalid_strategy"
        )
        
        # Should still work with default performance
        self.assertGreaterEqual(allocation, 0.0)
        
        # Test with None market data
        allocation, details = self.allocator.calculate_position_size(
            signal_confidence=0.8,
            strategy="memecoin_hunter",
            market_data=None
        )
        
        self.assertGreaterEqual(allocation, 0.0)
    
    def test_allocation_reasoning(self):
        """Test allocation reasoning generation"""
        signal_quality = SignalQuality(
            confidence_score=0.8,
            strategy_performance=0.75,
            market_regime_score=0.8,
            volatility_adjustment=0.9,
            time_decay_factor=1.0,
            composite_score=0.78
        )
        
        reasoning = self.allocator.get_allocation_reasoning(signal_quality, 0.1)
        
        self.assertIsInstance(reasoning, str)
        self.assertIn("allocation", reasoning.lower())
        self.assertIn("confidence", reasoning.lower())

class TestAllocationParams(unittest.TestCase):
    """Test AllocationParams dataclass"""
    
    def test_default_params(self):
        """Test default allocation parameters"""
        params = AllocationParams()
        
        self.assertEqual(params.base_allocation, 0.02)
        self.assertEqual(params.max_allocation, 0.25)
        self.assertEqual(params.min_allocation, 0.005)
        self.assertEqual(params.confidence_threshold, 0.5)
        self.assertEqual(params.risk_multiplier, 1.0)
        self.assertEqual(params.portfolio_heat, 0.0)
    
    def test_custom_params(self):
        """Test custom allocation parameters"""
        params = AllocationParams(
            max_allocation=0.3,
            confidence_threshold=0.7
        )
        
        self.assertEqual(params.max_allocation, 0.3)
        self.assertEqual(params.confidence_threshold, 0.7)
        self.assertEqual(params.base_allocation, 0.02)  # Should keep default

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
