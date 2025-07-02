#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Strategy Profiles
Mapowanie strategii do faz rynku dla inteligentnej adaptacji
"""

from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum

class MarketRegime(Enum):
    """Fazy rynku"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    NEUTRAL = "NEUTRAL"

# MAPOWANIE STRATEGII DO FAZ RYNKU
STRATEGY_REGIME_MAP = {
    "BULLISH": [
        "memecoin_hunter",          # Polowanie na memecoin w hossie
        "high_vol_sniper",          # Wykorzystanie wysokiej volatility
        "sol_momentum_trader",      # Trading momentum SOL
        "governance_alpha_hunter",  # Alpha z governance (może być bullish)
        "soul_meteor",              # Soul Meteor w hossie
        "developer_tracking",       # Tracking deweloperów
        "liquidity_sniping"         # Sniping płynności
    ],
    "BEARISH": [
        "low_risk_arbitrage",       # Bezpieczny arbitraż
        "governance_alpha_hunter",  # Alpha z governance (defensywne)
        "cross_dex_arbitrage",      # Arbitraż między DEX
        "market_making"             # Market making (ostrożny)
    ],
    "SIDEWAYS": [
        "cross_dex_arbitrage",      # Klasyczny arbitraż
        "market_making",            # Market making w range
        "low_risk_arbitrage",       # Bezpieczny arbitraż
        "meteora_damm"              # DAMM trading
    ],
    "NEUTRAL": [
        "low_risk_arbitrage",       # Tylko bezpieczny arbitraż
        "market_making"             # Podstawowy market making
    ]
}

@dataclass
class StrategyProfile:
    """Profil strategii dla konkretnej fazy rynku"""
    regime: MarketRegime
    strategies: List[str]
    risk_multiplier: float  # Mnożnik ryzyka dla tej fazy
    position_size_multiplier: float  # Mnożnik wielkości pozycji
    confidence_threshold: float  # Minimalny próg pewności dla sygnałów
    description: str

class StrategyRegimeMapper:
    """
    Mapowanie strategii do odpowiednich faz rynku
    
    Główne funkcje:
    - Definiowanie które strategie są odpowiednie dla każdej fazy rynku
    - Dynamiczne dostosowywanie parametrów ryzyka
    - Filtrowanie sygnałów na podstawie obecnej fazy rynku
    """
    
    def __init__(self):
        """Inicjalizacja mapowania strategii do faz rynku"""
        
        # PROFILE STRATEGII dla każdej fazy rynku
        self.strategy_profiles = {
            
            # BULLISH - Hossa: Agresywne strategie wzrostowe
            MarketRegime.BULLISH: StrategyProfile(
                regime=MarketRegime.BULLISH,
                strategies=STRATEGY_REGIME_MAP["BULLISH"],
                risk_multiplier=1.25,           # 25% więcej ryzyka w hossie
                position_size_multiplier=1.2,   # 20% większe pozycje
                confidence_threshold=0.55,      # Niższy próg pewności (więcej sygnałów)
                description="Aggressive growth strategies for bull market"
            ),
            
            # BEARISH - Bessa: Ostrożne, defensywne strategie
            MarketRegime.BEARISH: StrategyProfile(
                regime=MarketRegime.BEARISH,
                strategies=STRATEGY_REGIME_MAP["BEARISH"],
                risk_multiplier=0.65,           # 35% mniej ryzyka w bessie
                position_size_multiplier=0.7,   # 30% mniejsze pozycje
                confidence_threshold=0.75,      # Wyższy próg pewności (mniej sygnałów)
                description="Conservative defensive strategies for bear market"
            ),
            
            # SIDEWAYS - Konsolidacja: Strategie range-bound
            MarketRegime.SIDEWAYS: StrategyProfile(
                regime=MarketRegime.SIDEWAYS,
                strategies=STRATEGY_REGIME_MAP["SIDEWAYS"],
                risk_multiplier=0.8,            # 20% mniej ryzyka
                position_size_multiplier=0.9,   # 10% mniejsze pozycje
                confidence_threshold=0.65,      # Średni próg pewności
                description="Range-bound strategies for sideways market"
            ),
            
            # NEUTRAL - Nieokreślony: Tylko najbezpieczniejsze strategie
            MarketRegime.NEUTRAL: StrategyProfile(
                regime=MarketRegime.NEUTRAL,
                strategies=STRATEGY_REGIME_MAP["NEUTRAL"],
                risk_multiplier=0.5,            # 50% mniej ryzyka
                position_size_multiplier=0.6,   # 40% mniejsze pozycje
                confidence_threshold=0.8,       # Bardzo wysoki próg pewności
                description="Ultra-safe strategies for uncertain market conditions"
            )
        }
        
        # MAPOWANIE STRATEGII DO DOZWOLONYCH FAZ (dla szybkiego lookup)
        self.strategy_regime_map = {}
        for regime, profile in self.strategy_profiles.items():
            for strategy in profile.strategies:
                if strategy not in self.strategy_regime_map:
                    self.strategy_regime_map[strategy] = set()
                self.strategy_regime_map[strategy].add(regime)
    
    def is_strategy_allowed(self, strategy: str, current_regime: MarketRegime) -> bool:
        """
        Sprawdza czy strategia jest dozwolona w obecnej fazie rynku
        
        Args:
            strategy: Nazwa strategii
            current_regime: Obecna faza rynku
            
        Returns:
            True jeśli strategia jest dozwolona
        """
        
        # Standardowe mapowanie
        if strategy in self.strategy_regime_map:
            return current_regime in self.strategy_regime_map[strategy]
        
        # Nieznana strategia - domyślnie dozwolona tylko w NEUTRAL
        return current_regime == MarketRegime.NEUTRAL
    
    def get_allowed_strategies(self, current_regime: MarketRegime) -> List[str]:
        """
        Zwraca listę dozwolonych strategii dla obecnej fazy rynku
        
        Args:
            current_regime: Obecna faza rynku
            
        Returns:
            Lista nazw dozwolonych strategii
        """
        
        if current_regime in self.strategy_profiles:
            return self.strategy_profiles[current_regime].strategies.copy()
        
        return []
    
    def get_regime_parameters(self, current_regime: MarketRegime) -> Dict:
        """
        Zwraca parametry dla obecnej fazy rynku
        
        Args:
            current_regime: Obecna faza rynku
            
        Returns:
            Słownik z parametrami ryzyka i pozycji
        """
        
        if current_regime in self.strategy_profiles:
            profile = self.strategy_profiles[current_regime]
            return {
                "risk_multiplier": profile.risk_multiplier,
                "position_size_multiplier": profile.position_size_multiplier,
                "confidence_threshold": profile.confidence_threshold,
                "description": profile.description
            }
        
        # Domyślne parametry dla nieznanej fazy
        return {
            "risk_multiplier": 0.5,
            "position_size_multiplier": 0.5,
            "confidence_threshold": 0.9,
            "description": "Unknown regime - ultra conservative"
        }
    
    def validate_strategy_signal(self, strategy: str, confidence: float, 
                                current_regime: MarketRegime,
                                market_indicators: Dict = None) -> Dict:
        """
        Kompleksowa walidacja sygnału strategii
        
        Args:
            strategy: Nazwa strategii
            confidence: Pewność sygnału
            current_regime: Obecna faza rynku
            market_indicators: Wskaźniki rynku
            
        Returns:
            Słownik z wynikiem walidacji
        """
        
        result = {
            "allowed": False,
            "adjusted_confidence": confidence,
            "reason": "",
            "regime_match": False,
            "confidence_pass": False
        }
        
        # Sprawdź czy strategia jest dozwolona w obecnej fazie
        if not self.is_strategy_allowed(strategy, current_regime):
            result["reason"] = f"Strategy {strategy} not allowed in {current_regime.value} regime"
            return result
        
        result["regime_match"] = True
        
        # Sprawdź próg pewności dla obecnej fazy
        regime_params = self.get_regime_parameters(current_regime)
        confidence_threshold = regime_params["confidence_threshold"]
        
        if confidence < confidence_threshold:
            result["reason"] = f"Confidence {confidence:.2f} below threshold {confidence_threshold:.2f} for {current_regime.value}"
            return result
        
        result["confidence_pass"] = True
        result["allowed"] = True
        result["reason"] = f"Signal validated for {current_regime.value} regime"
        
        return result
