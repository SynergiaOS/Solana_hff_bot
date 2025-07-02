#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Market Regime Detector Tests
Comprehensive testing for market regime detection system
"""

import pytest
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add brain directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'brain', 'src', 'overmind_brain'))

from market_regime_detector import MarketRegimeDetector, MarketRegime, RegimeIndicators
from strategy_profiles import StrategyRegimeMapper

class TestMarketRegimeDetector:
    """Test suite for Market Regime Detector"""
    
    @pytest.fixture
    def detector(self):
        """Create a fresh Market Regime Detector for each test"""
        return MarketRegimeDetector()
    
    @pytest.fixture
    def strategy_mapper(self):
        """Create a fresh Strategy Regime Mapper for each test"""
        return StrategyRegimeMapper()
    
    def create_mock_price_data(self, trend_type: str, periods: int = 100) -> pd.DataFrame:
        """
        Create mock price data for different market conditions
        
        Args:
            trend_type: "bullish", "bearish", "sideways"
            periods: Number of data points
        """
        
        timestamps = pd.date_range(start=datetime.now() - timedelta(hours=24), periods=periods, freq='15min')
        base_price = 150.0
        
        prices = []
        for i in range(periods):
            if trend_type == "bullish":
                # Strong uptrend with increasing prices
                trend = 0.002 * i  # 0.2% per period
                noise = np.random.normal(0, 0.01)
            elif trend_type == "bearish":
                # Strong downtrend with decreasing prices
                trend = -0.002 * i  # -0.2% per period
                noise = np.random.normal(0, 0.01)
            else:  # sideways
                # Sideways movement with minimal trend
                trend = 0.0001 * np.sin(i * 0.1)  # Small oscillation
                noise = np.random.normal(0, 0.005)  # Lower volatility
            
            price = base_price * (1 + trend + noise)
            
            # Generate OHLC
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            open_price = price * (1 + np.random.normal(0, 0.003))
            close = price
            volume = 1000000 * (1 + np.random.normal(0, 0.2))
            
            prices.append({
                'timestamp': timestamps[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(prices)
        df.set_index('timestamp', inplace=True)
        return df
    
    def test_initialization(self, detector):
        """Test 1: Proper initialization of Market Regime Detector"""
        assert detector.helius_api_key == "edbcd361-78a0-4998-bd1e-8d4666722f82"
        assert detector.config['lookback_hours'] == 24
        assert detector.config['interval_minutes'] == 15
        assert detector.config['sma_period'] == 200
        assert detector.current_regime == MarketRegime.NEUTRAL
        assert detector.regime_history == []
    
    def test_technical_indicators_calculation(self, detector):
        """Test 2: Calculation of technical indicators"""
        
        # Create bullish test data
        test_data = self.create_mock_price_data("bullish", 250)  # Enough for SMA200
        
        indicators = detector.calculate_technical_indicators(test_data)
        
        # Verify all indicators are calculated
        assert indicators.current_price > 0
        assert indicators.sma_200 > 0
        assert indicators.sma_50 > 0
        assert indicators.ema_20 > 0
        assert 0 <= indicators.rsi <= 100
        assert indicators.adx >= 0
        assert indicators.volatility >= 0
        assert indicators.volume_ratio > 0
        
        # In bullish data, current price should be above SMA200
        assert indicators.current_price > indicators.sma_200
        assert indicators.price_vs_sma200 > 0  # Positive deviation
    
    def test_bullish_regime_detection(self, detector):
        """Test 3: Detection of bullish market regime"""
        
        # Create strong bullish data
        bullish_data = self.create_mock_price_data("bullish", 250)
        
        indicators = detector.calculate_technical_indicators(bullish_data)
        regime, confidence, reasoning = detector.classify_regime(indicators)
        
        assert regime == MarketRegime.BULLISH
        assert confidence > 0.5  # Should have reasonable confidence
        assert "above SMA200" in " ".join(reasoning)
        assert len(reasoning) > 0
    
    def test_bearish_regime_detection(self, detector):
        """Test 4: Detection of bearish market regime"""
        
        # Create strong bearish data
        bearish_data = self.create_mock_price_data("bearish", 250)
        
        indicators = detector.calculate_technical_indicators(bearish_data)
        regime, confidence, reasoning = detector.classify_regime(indicators)
        
        assert regime == MarketRegime.BEARISH
        assert confidence > 0.5  # Should have reasonable confidence
        assert "below SMA200" in " ".join(reasoning)
        assert len(reasoning) > 0
    
    def test_sideways_regime_detection(self, detector):
        """Test 5: Detection of sideways market regime"""
        
        # Create sideways data
        sideways_data = self.create_mock_price_data("sideways", 250)
        
        indicators = detector.calculate_technical_indicators(sideways_data)
        regime, confidence, reasoning = detector.classify_regime(indicators)
        
        assert regime == MarketRegime.SIDEWAYS
        assert confidence > 0.3  # Lower confidence is expected for sideways
        assert "Weak trend" in " ".join(reasoning) or "ADX" in " ".join(reasoning)
    
    @pytest.mark.asyncio
    async def test_detect_regime_integration(self, detector):
        """Test 6: Full regime detection integration"""
        
        # Mock the price data fetching
        with patch.object(detector, 'get_price_data') as mock_get_data:
            mock_get_data.return_value = self.create_mock_price_data("bullish", 250)
            
            regime_str = await detector.detect_regime()
            
            assert regime_str in ["BULLISH", "BEARISH", "SIDEWAYS", "NEUTRAL"]
            assert detector.current_regime != MarketRegime.NEUTRAL  # Should detect something
            assert detector.last_analysis is not None
            assert len(detector.regime_history) == 1
    
    def test_regime_history_tracking(self, detector):
        """Test 7: Regime history tracking"""
        
        # Simulate multiple regime detections
        test_data = self.create_mock_price_data("bullish", 250)
        
        for i in range(5):
            indicators = detector.calculate_technical_indicators(test_data)
            regime, confidence, reasoning = detector.classify_regime(indicators)
            
            # Manually add to history (simulating detect_regime calls)
            from market_regime_detector import RegimeAnalysis
            import time
            
            analysis = RegimeAnalysis(
                regime=regime,
                confidence=confidence,
                indicators=indicators,
                reasoning=reasoning,
                timestamp=time.time() + i
            )
            
            detector.regime_history.append(analysis)
        
        assert len(detector.regime_history) == 5
        
        # Test history retrieval
        recent_history = detector.get_regime_history(hours=24)
        assert len(recent_history) == 5
    
    def test_regime_summary(self, detector):
        """Test 8: Regime summary generation"""
        
        # Create test analysis
        test_data = self.create_mock_price_data("bullish", 250)
        indicators = detector.calculate_technical_indicators(test_data)
        regime, confidence, reasoning = detector.classify_regime(indicators)
        
        from market_regime_detector import RegimeAnalysis
        import time
        
        detector.last_analysis = RegimeAnalysis(
            regime=regime,
            confidence=confidence,
            indicators=indicators,
            reasoning=reasoning,
            timestamp=time.time()
        )
        
        summary = detector.get_regime_summary()
        
        assert "regime" in summary
        assert "confidence" in summary
        assert "indicators" in summary
        assert "reasoning" in summary
        assert summary["regime"] in ["BULLISH", "BEARISH", "SIDEWAYS", "NEUTRAL"]
        assert 0 <= summary["confidence"] <= 1

class TestStrategyRegimeMapper:
    """Test suite for Strategy Regime Mapper"""
    
    @pytest.fixture
    def mapper(self):
        """Create a fresh Strategy Regime Mapper for each test"""
        return StrategyRegimeMapper()
    
    def test_strategy_mapping_initialization(self, mapper):
        """Test 9: Strategy mapping initialization"""
        
        # Check that all regimes have strategies
        for regime in MarketRegime:
            strategies = mapper.get_allowed_strategies(regime)
            assert isinstance(strategies, list)
            
            if regime != MarketRegime.NEUTRAL:
                assert len(strategies) > 0  # Non-neutral regimes should have strategies
    
    def test_bullish_strategy_validation(self, mapper):
        """Test 10: Bullish regime strategy validation"""
        
        # Test memecoin_hunter in bullish regime
        result = mapper.validate_strategy_signal(
            strategy="memecoin_hunter",
            confidence=0.7,
            current_regime=MarketRegime.BULLISH
        )
        
        assert result["allowed"] == True
        assert result["regime_match"] == True
        assert result["confidence_pass"] == True
        assert "validated" in result["reason"]
    
    def test_bearish_strategy_rejection(self, mapper):
        """Test 11: Bearish regime strategy rejection"""
        
        # Test memecoin_hunter in bearish regime (should be rejected)
        result = mapper.validate_strategy_signal(
            strategy="memecoin_hunter",
            confidence=0.8,
            current_regime=MarketRegime.BEARISH
        )
        
        assert result["allowed"] == False
        assert result["regime_match"] == False
        assert "not allowed" in result["reason"]
    
    def test_confidence_threshold_filtering(self, mapper):
        """Test 12: Confidence threshold filtering"""
        
        # Test low confidence signal in bearish regime (high threshold)
        result = mapper.validate_strategy_signal(
            strategy="low_risk_arbitrage",
            confidence=0.5,  # Low confidence
            current_regime=MarketRegime.BEARISH  # High threshold (0.75)
        )
        
        assert result["allowed"] == False
        assert result["regime_match"] == True
        assert result["confidence_pass"] == False
        assert "below threshold" in result["reason"]
    
    def test_regime_parameters(self, mapper):
        """Test 13: Regime parameters retrieval"""
        
        # Test bullish parameters
        bullish_params = mapper.get_regime_parameters(MarketRegime.BULLISH)
        assert bullish_params["risk_multiplier"] > 1.0  # More aggressive
        assert bullish_params["confidence_threshold"] < 0.7  # Lower threshold
        
        # Test bearish parameters
        bearish_params = mapper.get_regime_parameters(MarketRegime.BEARISH)
        assert bearish_params["risk_multiplier"] < 1.0  # More conservative
        assert bearish_params["confidence_threshold"] > 0.7  # Higher threshold
    
    def test_strategy_summary(self, mapper):
        """Test 14: Strategy summary generation"""
        
        summary = mapper.get_strategy_summary()
        
        assert isinstance(summary, dict)
        assert len(summary) == 4  # Four regimes
        
        for regime_name, regime_data in summary.items():
            assert "strategies" in regime_data
            assert "strategy_count" in regime_data
            assert "risk_multiplier" in regime_data
            assert "confidence_threshold" in regime_data

class TestMarketRegimeIntegration:
    """Integration tests for Market Regime Detection system"""
    
    @pytest.mark.asyncio
    async def test_full_regime_detection_pipeline(self):
        """Test 15: Full regime detection and strategy validation pipeline"""
        
        detector = MarketRegimeDetector()
        mapper = StrategyRegimeMapper()
        
        # Mock price data
        with patch.object(detector, 'get_price_data') as mock_get_data:
            mock_get_data.return_value = detector._generate_sample_data(
                datetime.now() - timedelta(hours=24),
                datetime.now()
            )
            
            # Detect regime
            regime_str = await detector.detect_regime()
            regime = MarketRegime(regime_str)
            
            # Test strategy validation for detected regime
            test_strategies = ["memecoin_hunter", "low_risk_arbitrage", "market_making"]
            
            for strategy in test_strategies:
                result = mapper.validate_strategy_signal(
                    strategy=strategy,
                    confidence=0.7,
                    current_regime=regime
                )
                
                # Result should be consistent with regime
                if strategy in mapper.get_allowed_strategies(regime):
                    assert result["regime_match"] == True
                else:
                    assert result["regime_match"] == False
    
    def test_performance_under_load(self):
        """Test 16: Performance under load"""
        
        detector = MarketRegimeDetector()
        mapper = StrategyRegimeMapper()
        
        import time
        start_time = time.time()
        
        # Generate large dataset
        test_data = detector._generate_sample_data(
            datetime.now() - timedelta(hours=48),  # 48 hours of data
            datetime.now()
        )
        
        # Calculate indicators multiple times
        for _ in range(10):
            indicators = detector.calculate_technical_indicators(test_data)
            regime, confidence, reasoning = detector.classify_regime(indicators)
            
            # Validate multiple strategies
            for strategy in ["memecoin_hunter", "low_risk_arbitrage", "governance_alpha_hunter"]:
                mapper.validate_strategy_signal(strategy, 0.7, regime)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        assert execution_time < 5.0, f"Performance test took too long: {execution_time:.3f}s"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
