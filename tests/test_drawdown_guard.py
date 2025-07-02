#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Drawdown Guard Tests
Comprehensive testing for the global portfolio protection system
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add brain directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'brain', 'src', 'overmind_brain'))

from drawdown_guard import DrawdownGuard, DrawdownConfig

class TestDrawdownGuard:
    """Test suite for Drawdown Guard system"""
    
    @pytest.fixture
    def drawdown_guard(self):
        """Create a fresh Drawdown Guard for each test"""
        return DrawdownGuard(
            max_daily_loss_percentage=0.15,    # 15% daily limit
            max_hourly_loss_percentage=0.05,   # 5% hourly limit
            emergency_threshold_percentage=0.20 # 20% emergency threshold
        )
    
    def test_initialization(self, drawdown_guard):
        """Test 1: Proper initialization of Drawdown Guard"""
        assert drawdown_guard.config.max_daily_loss_percentage == 0.15
        assert drawdown_guard.config.max_hourly_loss_percentage == 0.05
        assert drawdown_guard.config.emergency_threshold_percentage == 0.20
        
        assert drawdown_guard.daily_pnl == 0.0
        assert drawdown_guard.hourly_pnl == 0.0
        assert drawdown_guard.total_pnl == 0.0
        
        assert drawdown_guard.emergency_stop_active == False
        assert drawdown_guard.hourly_limit_breached == False
        assert drawdown_guard.daily_limit_breached == False
    
    def test_small_profits_and_losses_ok(self, drawdown_guard):
        """Test 2: Wszystko OK - Seria małych zysków i strat"""
        
        # Seria małych transakcji które nie przekraczają żadnego progu
        test_trades = [0.02, -0.01, 0.015, -0.008, 0.025, -0.012, 0.018]
        
        for trade_pnl in test_trades:
            drawdown_guard.update_pnl(trade_pnl)
            
            # Po każdej transakcji system powinien być bezpieczny
            is_safe = drawdown_guard.check_portfolio_health()
            assert is_safe == True, f"System should be safe after trade: {trade_pnl}"
        
        # Sprawdź końcowe wartości
        expected_daily_pnl = sum(test_trades)
        assert abs(drawdown_guard.daily_pnl - expected_daily_pnl) < 0.001
        assert drawdown_guard.emergency_stop_active == False
        assert drawdown_guard.total_trades_monitored == len(test_trades)
    
    def test_hourly_limit_breach_and_recovery(self, drawdown_guard):
        """Test 3: Przekroczenie limitu godzinnego i powrót do normalności"""
        
        # Symuluj dużą stratę przekraczającą limit godzinny (5%)
        large_loss = -0.08  # 8% strata
        drawdown_guard.update_pnl(large_loss)
        
        # System powinien wykryć przekroczenie limitu godzinnego
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == False, "System should detect hourly limit breach"
        assert drawdown_guard.hourly_limit_breached == True
        assert drawdown_guard.hourly_breaches == 1
        
        # Sprawdź że emergency stop nie jest aktywny (to tylko limit godzinny)
        assert drawdown_guard.emergency_stop_active == False
        
        # Symuluj upływ godziny
        with patch.object(drawdown_guard, 'last_hourly_reset', 
                         datetime.now() - timedelta(hours=1, minutes=5)):
            
            # Po upływie godziny system powinien się zresetować
            is_safe = drawdown_guard.check_portfolio_health()
            assert is_safe == True, "System should recover after hourly reset"
            assert drawdown_guard.hourly_pnl == 0.0, "Hourly P&L should reset to 0"
            assert drawdown_guard.hourly_limit_breached == False, "Hourly breach flag should reset"
            
            # Ale dzienny P&L powinien zostać
            assert drawdown_guard.daily_pnl == large_loss, "Daily P&L should persist"
    
    def test_daily_limit_breach_persistent(self, drawdown_guard):
        """Test 4: Przekroczenie limitu dziennego - trwałe do końca dnia"""
        
        # Seria strat przekraczających limit dzienny (15%)
        losses = [-0.05, -0.04, -0.03, -0.05]  # Łącznie -17%
        
        for loss in losses:
            drawdown_guard.update_pnl(loss)
        
        # System powinien wykryć przekroczenie limitu dziennego
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == False, "System should detect daily limit breach"
        assert drawdown_guard.daily_limit_breached == True
        assert drawdown_guard.daily_breaches == 1
        
        # Symuluj upływ godziny (ale nie całego dnia)
        with patch.object(drawdown_guard, 'last_hourly_reset', 
                         datetime.now() - timedelta(hours=1, minutes=5)):
            
            # Po upływie godziny limit dzienny nadal powinien być aktywny
            is_safe = drawdown_guard.check_portfolio_health()
            assert is_safe == False, "Daily limit should persist after hourly reset"
            assert drawdown_guard.daily_limit_breached == True
            assert drawdown_guard.daily_pnl < -0.15, "Daily P&L should still show loss"
    
    def test_emergency_threshold_activation(self, drawdown_guard):
        """Test 5: Aktywacja progu awaryjnego"""
        
        # Symuluj katastrofalną stratę przekraczającą próg awaryjny (20%)
        catastrophic_loss = -0.25  # 25% strata
        drawdown_guard.update_pnl(catastrophic_loss)
        
        # System powinien aktywować emergency stop
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == False, "System should activate emergency stop"
        assert drawdown_guard.emergency_stop_active == True
        assert drawdown_guard.emergency_stops_triggered == 1
        
        # Emergency stop powinien pozostać aktywny nawet po resetach czasowych
        with patch.object(drawdown_guard, 'last_hourly_reset', 
                         datetime.now() - timedelta(hours=2)):
            with patch.object(drawdown_guard, 'last_daily_reset', 
                             datetime.now() - timedelta(days=1)):
                
                is_safe = drawdown_guard.check_portfolio_health()
                assert is_safe == False, "Emergency stop should persist across time resets"
                assert drawdown_guard.emergency_stop_active == True
    
    def test_emergency_stop_recovery(self, drawdown_guard):
        """Test 6: Powrót z emergency stop po poprawie sytuacji"""
        
        # Aktywuj emergency stop
        drawdown_guard.update_pnl(-0.25)  # 25% strata
        drawdown_guard.check_portfolio_health()
        assert drawdown_guard.emergency_stop_active == True
        
        # Symuluj znaczną poprawę (zyski redukujące stratę poniżej 3%)
        recovery_profit = 0.23  # Zysk redukujący stratę do -2%
        drawdown_guard.update_pnl(recovery_profit)
        
        # System powinien wykryć poprawę i wyłączyć emergency stop
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == True, "System should recover from emergency stop"
        assert drawdown_guard.emergency_stop_active == False
        assert drawdown_guard.daily_pnl > -0.03, "Daily P&L should be above recovery threshold"
    
    def test_force_emergency_stop(self, drawdown_guard):
        """Test 7: Wymuszenie emergency stop"""
        
        # Wymuś emergency stop ręcznie
        drawdown_guard.force_emergency_stop("Manual test override")
        
        assert drawdown_guard.emergency_stop_active == True
        assert drawdown_guard.emergency_stops_triggered == 1
        
        # System powinien pozostać zatrzymany
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == False, "Forced emergency stop should prevent trading"
    
    def test_reset_emergency_stop(self, drawdown_guard):
        """Test 8: Reset emergency stop"""
        
        # Aktywuj emergency stop
        drawdown_guard.force_emergency_stop("Test")
        assert drawdown_guard.emergency_stop_active == True
        
        # Resetuj emergency stop
        drawdown_guard.reset_emergency_stop()
        assert drawdown_guard.emergency_stop_active == False
        
        # System powinien wrócić do normalnego działania
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == True, "System should work normally after emergency stop reset"
    
    def test_daily_reset_at_midnight(self, drawdown_guard):
        """Test 9: Reset dzienny o północy"""
        
        # Dodaj straty
        drawdown_guard.update_pnl(-0.10)  # 10% strata
        assert drawdown_guard.daily_pnl == -0.10
        
        # Symuluj przejście przez północ
        yesterday = datetime.now() - timedelta(days=1)
        with patch.object(drawdown_guard, 'last_daily_reset', yesterday):
            
            # Po północy dzienny P&L powinien się zresetować
            is_safe = drawdown_guard.check_portfolio_health()
            assert drawdown_guard.daily_pnl == 0.0, "Daily P&L should reset at midnight"
            assert drawdown_guard.daily_limit_breached == False, "Daily breach flag should reset"
            assert is_safe == True, "System should be safe after daily reset"
    
    def test_status_summary(self, drawdown_guard):
        """Test 10: Podsumowanie statusu"""
        
        # Dodaj kilka transakcji
        drawdown_guard.update_pnl(0.05)
        drawdown_guard.update_pnl(-0.03)
        drawdown_guard.update_pnl(-0.08)  # Przekroczenie limitu godzinnego
        
        drawdown_guard.check_portfolio_health()
        
        # Pobierz status
        status = drawdown_guard.get_status_summary()
        
        assert status["total_trades_monitored"] == 3
        assert status["hourly_limit_breached"] == True
        assert status["daily_pnl"] == 0.05 - 0.03 - 0.08
        assert status["config"]["max_daily_loss"] == 0.15
        assert "emergency_stop_active" in status
        assert "hourly_breaches" in status
    
    def test_multiple_breaches_counting(self, drawdown_guard):
        """Test 11: Liczenie wielokrotnych naruszeń"""
        
        # Pierwsze naruszenie godzinne
        drawdown_guard.update_pnl(-0.06)
        drawdown_guard.check_portfolio_health()
        assert drawdown_guard.hourly_breaches == 1
        
        # Reset godzinny
        with patch.object(drawdown_guard, 'last_hourly_reset', 
                         datetime.now() - timedelta(hours=1, minutes=5)):
            drawdown_guard.check_portfolio_health()
        
        # Drugie naruszenie godzinne
        drawdown_guard.update_pnl(-0.07)
        drawdown_guard.check_portfolio_health()
        assert drawdown_guard.hourly_breaches == 2
        
        # Sprawdź że statystyki są poprawnie liczone
        status = drawdown_guard.get_status_summary()
        assert status["hourly_breaches"] == 2
        assert status["total_trades_monitored"] == 2
    
    def test_edge_case_exact_thresholds(self, drawdown_guard):
        """Test 12: Przypadki graniczne - dokładne progi"""
        
        # Dokładnie na progu godzinnym (5%)
        drawdown_guard.update_pnl(-0.05)
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == False, "Exactly at threshold should trigger limit"
        
        # Reset i test progu dziennego
        drawdown_guard.reset_emergency_stop()
        drawdown_guard.hourly_pnl = 0.0
        drawdown_guard.hourly_limit_breached = False
        
        # Dokładnie na progu dziennym (15%)
        drawdown_guard.daily_pnl = -0.15
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == False, "Exactly at daily threshold should trigger limit"
        
        # Test progu awaryjnego
        drawdown_guard.daily_pnl = -0.20
        is_safe = drawdown_guard.check_portfolio_health()
        assert is_safe == False, "Exactly at emergency threshold should trigger stop"
        assert drawdown_guard.emergency_stop_active == True

class TestDrawdownGuardIntegration:
    """Testy integracyjne dla Drawdown Guard"""
    
    def test_realistic_trading_scenario(self):
        """Test 13: Realistyczny scenariusz tradingu"""
        
        guard = DrawdownGuard()
        
        # Symuluj dzień tradingu z mieszanymi wynikami
        trading_day = [
            0.02,   # Zysk 2%
            -0.01,  # Strata 1%
            0.03,   # Zysk 3%
            -0.02,  # Strata 2%
            -0.04,  # Strata 4% (przekroczenie limitu godzinnego)
            0.01,   # Próba zysku (ale limit godzinny nadal aktywny)
        ]
        
        safe_results = []
        
        for i, trade in enumerate(trading_day):
            guard.update_pnl(trade)
            is_safe = guard.check_portfolio_health()
            safe_results.append(is_safe)
            
            # Po 4. transakcji (łączna strata 4%) limit godzinny powinien być aktywny
            if i >= 4:  # Po 5. transakcji (indeks 4)
                assert is_safe == False, f"Should be unsafe after trade {i+1}"
        
        # Sprawdź końcowy stan
        assert guard.hourly_limit_breached == True
        assert guard.emergency_stop_active == False  # Nie osiągnięto progu awaryjnego
        assert guard.total_trades_monitored == len(trading_day)
    
    def test_performance_under_load(self):
        """Test 14: Wydajność pod obciążeniem"""
        
        guard = DrawdownGuard()
        
        # Symuluj 1000 transakcji
        import random
        random.seed(42)  # Dla powtarzalności testów
        
        start_time = time.time()
        
        for _ in range(1000):
            # Losowe P&L między -0.01 a 0.01
            pnl = random.uniform(-0.01, 0.01)
            guard.update_pnl(pnl)
            guard.check_portfolio_health()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Test powinien wykonać się szybko (< 1 sekunda)
        assert execution_time < 1.0, f"Performance test took too long: {execution_time:.3f}s"
        assert guard.total_trades_monitored == 1000

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
