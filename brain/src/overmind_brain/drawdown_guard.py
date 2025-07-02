#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Drawdown Guard Module
Globalny bezpiecznik chroniący cały kapitał przed katastrofalnymi stratami
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DrawdownConfig:
    """Konfiguracja limitów drawdown"""
    max_daily_loss_percentage: float = 0.15      # 15% maksymalna dzienna strata
    max_hourly_loss_percentage: float = 0.05     # 5% maksymalna godzinna strata  
    emergency_threshold_percentage: float = 0.20  # 20% próg awaryjny
    recovery_threshold_percentage: float = 0.03   # 3% próg powrotu do normalności

class DrawdownGuard:
    """
    Globalny system ochrony przed drawdown
    
    Główne funkcje:
    - Monitorowanie strat godzinnych i dziennych
    - Automatyczne zatrzymanie tradingu przy przekroczeniu limitów
    - Reset limitów czasowych
    - Ochrona przed katastrofalnymi stratami
    """
    
    def __init__(self, 
                 max_daily_loss_percentage: float = 0.15,
                 max_hourly_loss_percentage: float = 0.05, 
                 emergency_threshold_percentage: float = 0.20):
        """
        Inicjalizacja Drawdown Guard
        
        Args:
            max_daily_loss_percentage: Maksymalna dzienna strata (0.15 = 15%)
            max_hourly_loss_percentage: Maksymalna godzinna strata (0.05 = 5%)
            emergency_threshold_percentage: Próg awaryjny (0.20 = 20%)
        """
        
        # Konfiguracja limitów
        self.config = DrawdownConfig(
            max_daily_loss_percentage=max_daily_loss_percentage,
            max_hourly_loss_percentage=max_hourly_loss_percentage,
            emergency_threshold_percentage=emergency_threshold_percentage
        )
        
        # Śledzenie P&L
        self.daily_pnl = 0.0
        self.hourly_pnl = 0.0
        self.total_pnl = 0.0
        
        # Śledzenie czasu
        self.last_hourly_reset = datetime.now()
        self.last_daily_reset = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Stany systemu
        self.emergency_stop_active = False
        self.hourly_limit_breached = False
        self.daily_limit_breached = False
        
        # Statystyki
        self.total_trades_monitored = 0
        self.emergency_stops_triggered = 0
        self.hourly_breaches = 0
        self.daily_breaches = 0
        
        logger.info("🛡️ Drawdown Guard initialized")
        logger.info(f"   Daily limit: {self.config.max_daily_loss_percentage:.1%}")
        logger.info(f"   Hourly limit: {self.config.max_hourly_loss_percentage:.1%}")
        logger.info(f"   Emergency threshold: {self.config.emergency_threshold_percentage:.1%}")
    
    def update_pnl(self, pnl_change: float) -> None:
        """
        Aktualizuje P&L z nowej transakcji
        
        Args:
            pnl_change: Zmiana P&L z ostatniej transakcji (dodatnia = zysk, ujemna = strata)
        """
        
        # Aktualizuj wszystkie poziomy P&L
        self.daily_pnl += pnl_change
        self.hourly_pnl += pnl_change
        self.total_pnl += pnl_change
        self.total_trades_monitored += 1
        
        logger.debug(f"📊 P&L updated: trade={pnl_change:.4f}, daily={self.daily_pnl:.4f}, hourly={self.hourly_pnl:.4f}")
        
        # Sprawdź czy to była znacząca transakcja
        if abs(pnl_change) > 0.01:  # Transakcje > $0.01
            if pnl_change > 0:
                logger.info(f"💰 Profit recorded: ${pnl_change:.4f} (Daily: ${self.daily_pnl:.4f})")
            else:
                logger.warning(f"📉 Loss recorded: ${pnl_change:.4f} (Daily: ${self.daily_pnl:.4f})")
    
    def _reset_hourly_if_needed(self) -> bool:
        """
        Resetuje godzinny P&L jeśli minęła godzina
        
        Returns:
            True jeśli nastąpił reset, False w przeciwnym razie
        """
        
        current_time = datetime.now()
        time_since_reset = current_time - self.last_hourly_reset
        
        if time_since_reset >= timedelta(hours=1):
            logger.info(f"🔄 Hourly P&L reset: ${self.hourly_pnl:.4f} -> $0.00")
            self.hourly_pnl = 0.0
            self.last_hourly_reset = current_time
            self.hourly_limit_breached = False  # Reset flagi naruszenia
            return True
        
        return False
    
    def _reset_daily_if_needed(self) -> bool:
        """
        Resetuje dzienny P&L o północy
        
        Returns:
            True jeśli nastąpił reset, False w przeciwnym razie
        """
        
        current_time = datetime.now()
        current_day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if current_day_start > self.last_daily_reset:
            logger.info(f"🌅 Daily P&L reset: ${self.daily_pnl:.4f} -> $0.00")
            self.daily_pnl = 0.0
            self.last_daily_reset = current_day_start
            self.daily_limit_breached = False  # Reset flagi naruszenia
            # UWAGA: Emergency stop NIE jest resetowany automatycznie - wymaga ręcznej interwencji
            return True
        
        return False
    
    def check_portfolio_health(self) -> bool:
        """
        Główna metoda sprawdzająca zdrowie portfela
        
        Returns:
            True jeśli trading może kontynuować
            False jeśli trading powinien zostać zatrzymany
        """
        
        # KROK 1: Reset czasowy (godzinny i dzienny)
        hourly_reset = self._reset_hourly_if_needed()
        daily_reset = self._reset_daily_if_needed()
        
        if hourly_reset or daily_reset:
            logger.info("🔄 Time-based reset completed")

        # KROK 2: Sprawdzenie aktywnego emergency stop (najwyższy priorytet)
        if self.emergency_stop_active:
            logger.debug("🚨 Emergency stop is active - trading halted")
            return False

        # KROK 3: Sprawdzenie progu awaryjnego
        emergency_loss_threshold = -abs(self.config.emergency_threshold_percentage)

        if self.daily_pnl <= emergency_loss_threshold:
            if not self.emergency_stop_active:
                self.emergency_stops_triggered += 1
                self.emergency_stop_active = True
                logger.critical("🚨 EMERGENCY STOP TRIGGERED!")
                logger.critical(f"   Daily P&L: ${self.daily_pnl:.4f} ({self.daily_pnl:.2%})")
                logger.critical(f"   Emergency threshold: {emergency_loss_threshold:.2%}")
                logger.critical("   🛑 ALL TRADING HALTED")
            return False

        # KROK 4: Sprawdzenie limitu dziennego (wyższy priorytet niż godzinny)
        daily_loss_threshold = -abs(self.config.max_daily_loss_percentage)

        if self.daily_pnl <= daily_loss_threshold:
            if not self.daily_limit_breached:
                self.daily_breaches += 1
                self.daily_limit_breached = True
                logger.error("🚨 DAILY LOSS LIMIT BREACHED!")
                logger.error(f"   Daily P&L: ${self.daily_pnl:.4f} ({self.daily_pnl:.2%})")
                logger.error(f"   Daily limit: {daily_loss_threshold:.2%}")
                logger.error("   ⏸️ Trading paused for remainder of day")
            return False

        # KROK 5: Sprawdzenie limitu godzinnego
        hourly_loss_threshold = -abs(self.config.max_hourly_loss_percentage)

        if self.hourly_pnl <= hourly_loss_threshold:
            if not self.hourly_limit_breached:
                self.hourly_breaches += 1
                self.hourly_limit_breached = True
                logger.error("⚠️ HOURLY LOSS LIMIT BREACHED!")
                logger.error(f"   Hourly P&L: ${self.hourly_pnl:.4f} ({self.hourly_pnl:.2%})")
                logger.error(f"   Hourly limit: {hourly_loss_threshold:.2%}")
                logger.error("   ⏸️ Trading paused for remainder of hour")
            return False

        # KROK 6: Sprawdzenie warunków powrotu do normalności
        if self.emergency_stop_active:
            recovery_threshold = -abs(self.config.recovery_threshold_percentage)
            if self.daily_pnl >= recovery_threshold:
                self.emergency_stop_active = False
                logger.info("✅ EMERGENCY STOP DEACTIVATED - Portfolio recovered")
                logger.info(f"   Daily P&L improved to: ${self.daily_pnl:.4f}")
        
        # KROK 7: Wszystko OK - trading może kontynuować
        logger.debug(f"✅ Portfolio health check passed")
        logger.debug(f"   Daily P&L: ${self.daily_pnl:.4f}")
        logger.debug(f"   Hourly P&L: ${self.hourly_pnl:.4f}")

        return True
    
    def get_status_summary(self) -> dict:
        """
        Zwraca podsumowanie statusu Drawdown Guard
        
        Returns:
            Słownik z kluczowymi metrykami i statusami
        """
        
        return {
            "emergency_stop_active": self.emergency_stop_active,
            "hourly_limit_breached": self.hourly_limit_breached,
            "daily_limit_breached": self.daily_limit_breached,
            "daily_pnl": self.daily_pnl,
            "hourly_pnl": self.hourly_pnl,
            "total_pnl": self.total_pnl,
            "total_trades_monitored": self.total_trades_monitored,
            "emergency_stops_triggered": self.emergency_stops_triggered,
            "hourly_breaches": self.hourly_breaches,
            "daily_breaches": self.daily_breaches,
            "config": {
                "max_daily_loss": self.config.max_daily_loss_percentage,
                "max_hourly_loss": self.config.max_hourly_loss_percentage,
                "emergency_threshold": self.config.emergency_threshold_percentage
            }
        }
    
    def force_emergency_stop(self, reason: str = "Manual override") -> None:
        """
        Wymusza awaryjne zatrzymanie systemu
        
        Args:
            reason: Powód wymuszenia emergency stop
        """
        
        self.emergency_stop_active = True
        self.emergency_stops_triggered += 1
        
        logger.critical("🚨 FORCED EMERGENCY STOP ACTIVATED!")
        logger.critical(f"   Reason: {reason}")
        logger.critical("   🛑 ALL TRADING HALTED")
    
    def reset_emergency_stop(self) -> None:
        """
        Resetuje emergency stop (tylko dla testów lub ręcznej interwencji)
        """
        
        if self.emergency_stop_active:
            self.emergency_stop_active = False
            logger.warning("⚠️ Emergency stop manually reset")
        else:
            logger.info("ℹ️ Emergency stop was not active")
    
    def __str__(self) -> str:
        """String representation dla debugowania"""
        return (f"DrawdownGuard(daily_pnl={self.daily_pnl:.4f}, "
                f"hourly_pnl={self.hourly_pnl:.4f}, "
                f"emergency_active={self.emergency_stop_active})")
    
    def __repr__(self) -> str:
        """Detailed representation dla debugowania"""
        return self.__str__()
