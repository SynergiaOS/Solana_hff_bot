#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Market Regime Detector
Inteligentna detekcja faz rynku: BULLISH, BEARISH, SIDEWAYS
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
import requests

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Fazy rynku"""
    BULLISH = "BULLISH"      # Hossa - trend wzrostowy
    BEARISH = "BEARISH"      # Bessa - trend spadkowy  
    SIDEWAYS = "SIDEWAYS"    # Konsolidacja - rynek boczny
    NEUTRAL = "NEUTRAL"      # Nieokreślony

@dataclass
class RegimeIndicators:
    """Wskaźniki techniczne dla detekcji fazy rynku"""
    current_price: float
    sma_200: float
    sma_50: float
    ema_20: float
    rsi: float
    adx: float
    volatility: float
    volume_ratio: float
    price_vs_sma200: float  # Procent odchylenia od SMA200
    trend_strength: float   # Siła trendu (0-1)

@dataclass
class RegimeAnalysis:
    """Kompletna analiza fazy rynku"""
    regime: MarketRegime
    confidence: float
    indicators: RegimeIndicators
    reasoning: List[str]
    timestamp: float

class MarketRegimeDetector:
    """
    Detektor faz rynku wykorzystujący analizę techniczną
    
    Główne funkcje:
    - Pobieranie danych historycznych SOL/USDC
    - Obliczanie wskaźników technicznych (SMA, EMA, RSI, ADX)
    - Klasyfikacja fazy rynku na podstawie drzewa decyzyjnego
    - Śledzenie zmian faz rynku w czasie
    """
    
    def __init__(self, helius_api_key: str = "edbcd361-78a0-4998-bd1e-8d4666722f82"):
        """
        Inicjalizacja Market Regime Detector
        
        Args:
            helius_api_key: Klucz API do Helius dla danych cenowych
        """
        
        self.helius_api_key = helius_api_key
        
        # Konfiguracja detekcji
        self.config = {
            'lookback_hours': 24,        # 24 godziny danych historycznych
            'interval_minutes': 15,      # 15-minutowe świece
            'sma_period': 200,          # Okres SMA dla trendu długoterminowego
            'sma_short_period': 50,     # Okres SMA dla trendu krótkoterminowego
            'ema_period': 20,           # Okres EMA dla sygnałów
            'rsi_period': 14,           # Okres RSI
            'adx_period': 14,           # Okres ADX
            'volatility_period': 20,    # Okres dla volatility
            
            # Progi decyzyjne
            'bullish_adx_threshold': 25,    # ADX > 25 dla silnego trendu
            'bearish_adx_threshold': 25,    # ADX > 25 dla silnego trendu
            'sideways_adx_threshold': 20,   # ADX < 20 dla słabego trendu
            'rsi_overbought': 70,           # RSI > 70 = wykupienie
            'rsi_oversold': 30,             # RSI < 30 = wyprzedanie
            'volatility_high_threshold': 0.05,  # 5% volatility = wysoka
            'volume_spike_threshold': 1.5,   # 1.5x średni volume = spike
        }
        
        # Cache dla danych
        self.price_data_cache = None
        self.cache_timestamp = 0
        self.cache_duration = 300  # 5 minut cache
        
        # Historia detekcji
        self.regime_history = []
        self.current_regime = MarketRegime.NEUTRAL
        self.last_analysis = None
        
        logger.info("📊 Market Regime Detector initialized")
        logger.info(f"   Lookback: {self.config['lookback_hours']} hours")
        logger.info(f"   Interval: {self.config['interval_minutes']} minutes")
        logger.info(f"   SMA periods: {self.config['sma_period']}, {self.config['sma_short_period']}")
    
    async def get_price_data(self) -> Optional[pd.DataFrame]:
        """
        Pobiera dane cenowe SOL/USDC z ostatnich 24 godzin
        
        Returns:
            DataFrame z kolumnami: timestamp, open, high, low, close, volume
        """
        
        try:
            # Sprawdź cache
            current_time = time.time()
            if (self.price_data_cache is not None and 
                current_time - self.cache_timestamp < self.cache_duration):
                logger.debug("📊 Using cached price data")
                return self.price_data_cache
            
            # Oblicz zakres czasowy
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=self.config['lookback_hours'])
            
            # Dla demonstracji używamy symulowanych danych
            # W produkcji tutaj byłoby wywołanie API Helius/CoinGecko
            logger.info(f"📊 Fetching SOL/USDC data from {start_time} to {end_time}")
            
            # Symulowane dane cenowe (w produkcji zastąpić prawdziwym API)
            price_data = self._generate_sample_data(start_time, end_time)
            
            # Cache wyników
            self.price_data_cache = price_data
            self.cache_timestamp = current_time
            
            logger.info(f"📊 Retrieved {len(price_data)} price points")
            return price_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching price data: {e}")
            return None
    
    def _generate_sample_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """
        Generuje przykładowe dane cenowe dla testów
        W produkcji zastąpić prawdziwym API call
        """
        
        # Generuj timestamps co 15 minut
        timestamps = pd.date_range(start=start_time, end=end_time, freq='15min')
        
        # Symuluj dane cenowe z trendem
        np.random.seed(42)  # Dla powtarzalności
        
        base_price = 150.0  # Bazowa cena SOL
        prices = []
        volume_base = 1000000
        
        for i, ts in enumerate(timestamps):
            # Symuluj trend + noise
            trend = 0.001 * i  # Lekki trend wzrostowy
            noise = np.random.normal(0, 0.02)  # 2% noise
            
            price = base_price * (1 + trend + noise)
            
            # OHLC data
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = price * (1 + np.random.normal(0, 0.005))
            close = price
            
            volume = volume_base * (1 + np.random.normal(0, 0.3))
            
            prices.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(prices)
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> RegimeIndicators:
        """
        Oblicza wskaźniki techniczne dla detekcji fazy rynku
        
        Args:
            df: DataFrame z danymi cenowymi
            
        Returns:
            RegimeIndicators z obliczonymi wskaźnikami
        """
        
        try:
            # Podstawowe ceny
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']
            
            current_price = close.iloc[-1]
            
            # Średnie kroczące
            sma_200 = close.rolling(window=min(200, len(close))).mean().iloc[-1]
            sma_50 = close.rolling(window=min(50, len(close))).mean().iloc[-1]
            ema_20 = close.ewm(span=min(20, len(close))).mean().iloc[-1]
            
            # RSI
            rsi = self._calculate_rsi(close, self.config['rsi_period'])
            
            # ADX (uproszczona wersja)
            adx = self._calculate_adx(high, low, close, self.config['adx_period'])
            
            # Volatility (standard deviation)
            returns = close.pct_change().dropna()
            volatility = returns.rolling(window=min(20, len(returns))).std().iloc[-1] * np.sqrt(96)  # Annualized
            
            # Volume ratio (current vs average)
            avg_volume = volume.rolling(window=min(20, len(volume))).mean().iloc[-1]
            volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1.0
            
            # Dodatkowe metryki
            price_vs_sma200 = (current_price - sma_200) / sma_200 if sma_200 > 0 else 0
            
            # Trend strength (kombinacja ADX i price position)
            trend_strength = min(1.0, adx / 50.0) if adx > 0 else 0
            
            indicators = RegimeIndicators(
                current_price=current_price,
                sma_200=sma_200,
                sma_50=sma_50,
                ema_20=ema_20,
                rsi=rsi,
                adx=adx,
                volatility=volatility,
                volume_ratio=volume_ratio,
                price_vs_sma200=price_vs_sma200,
                trend_strength=trend_strength
            )
            
            logger.debug(f"📊 Technical indicators calculated:")
            logger.debug(f"   Price: ${current_price:.2f}")
            logger.debug(f"   SMA200: ${sma_200:.2f}")
            logger.debug(f"   RSI: {rsi:.1f}")
            logger.debug(f"   ADX: {adx:.1f}")
            logger.debug(f"   Volatility: {volatility:.3f}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error calculating technical indicators: {e}")
            # Return neutral indicators
            return RegimeIndicators(
                current_price=0, sma_200=0, sma_50=0, ema_20=0,
                rsi=50, adx=0, volatility=0, volume_ratio=1.0,
                price_vs_sma200=0, trend_strength=0
            )
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> float:
        """Oblicza RSI (Relative Strength Index)"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
        except:
            return 50.0  # Neutral RSI
    
    def _calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> float:
        """Oblicza ADX (Average Directional Index) - uproszczona wersja"""
        try:
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Directional Movement
            dm_plus = high.diff()
            dm_minus = -low.diff()
            
            dm_plus[dm_plus < 0] = 0
            dm_minus[dm_minus < 0] = 0
            
            # Smoothed values
            tr_smooth = tr.rolling(window=period).mean()
            dm_plus_smooth = dm_plus.rolling(window=period).mean()
            dm_minus_smooth = dm_minus.rolling(window=period).mean()
            
            # Directional Indicators
            di_plus = 100 * dm_plus_smooth / tr_smooth
            di_minus = 100 * dm_minus_smooth / tr_smooth
            
            # ADX
            dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
            adx = dx.rolling(window=period).mean()
            
            return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0.0
        except:
            return 0.0  # Neutral ADX

    def classify_regime(self, indicators: RegimeIndicators) -> Tuple[MarketRegime, float, List[str]]:
        """
        Klasyfikuje fazę rynku na podstawie wskaźników technicznych

        Args:
            indicators: Obliczone wskaźniki techniczne

        Returns:
            Tuple[regime, confidence, reasoning]
        """

        reasoning = []
        confidence = 0.0

        # DRZEWO DECYZYJNE dla klasyfikacji fazy rynku

        # Sprawdź pozycję względem SMA200 (główny trend)
        price_above_sma200 = indicators.current_price > indicators.sma_200
        price_vs_sma200_pct = indicators.price_vs_sma200 * 100

        # Sprawdź siłę trendu (ADX)
        strong_trend = indicators.adx > self.config['bullish_adx_threshold']
        weak_trend = indicators.adx < self.config['sideways_adx_threshold']

        # Sprawdź momentum (RSI)
        rsi_overbought = indicators.rsi > self.config['rsi_overbought']
        rsi_oversold = indicators.rsi < self.config['rsi_oversold']

        # Sprawdź volatility
        high_volatility = indicators.volatility > self.config['volatility_high_threshold']

        # LOGIKA KLASYFIKACJI

        # BULLISH: Cena powyżej SMA200 + silny trend
        if price_above_sma200 and strong_trend:
            confidence += 0.4  # Bazowa pewność
            reasoning.append(f"Price {price_vs_sma200_pct:.1f}% above SMA200")
            reasoning.append(f"Strong trend (ADX: {indicators.adx:.1f})")

            # Dodatkowe potwierdzenia
            if indicators.sma_50 > indicators.sma_200:
                confidence += 0.2
                reasoning.append("SMA50 > SMA200 (golden cross)")

            if not rsi_overbought:
                confidence += 0.2
                reasoning.append(f"RSI not overbought ({indicators.rsi:.1f})")

            if indicators.volume_ratio > 1.2:
                confidence += 0.1
                reasoning.append(f"Above average volume ({indicators.volume_ratio:.1f}x)")

            # Korekta za wykupienie
            if rsi_overbought:
                confidence -= 0.1
                reasoning.append(f"RSI overbought warning ({indicators.rsi:.1f})")

            return MarketRegime.BULLISH, min(confidence, 0.95), reasoning

        # BEARISH: Cena poniżej SMA200 + silny trend
        elif not price_above_sma200 and strong_trend:
            confidence += 0.4  # Bazowa pewność
            reasoning.append(f"Price {abs(price_vs_sma200_pct):.1f}% below SMA200")
            reasoning.append(f"Strong trend (ADX: {indicators.adx:.1f})")

            # Dodatkowe potwierdzenia
            if indicators.sma_50 < indicators.sma_200:
                confidence += 0.2
                reasoning.append("SMA50 < SMA200 (death cross)")

            if not rsi_oversold:
                confidence += 0.2
                reasoning.append(f"RSI not oversold ({indicators.rsi:.1f})")

            if indicators.volume_ratio > 1.2:
                confidence += 0.1
                reasoning.append(f"Above average volume ({indicators.volume_ratio:.1f}x)")

            # Korekta za wyprzedanie
            if rsi_oversold:
                confidence -= 0.1
                reasoning.append(f"RSI oversold warning ({indicators.rsi:.1f})")

            return MarketRegime.BEARISH, min(confidence, 0.95), reasoning

        # SIDEWAYS: Słaby trend (niezależnie od pozycji względem SMA)
        elif weak_trend:
            confidence += 0.3
            reasoning.append(f"Weak trend (ADX: {indicators.adx:.1f})")

            # Dodatkowe potwierdzenia konsolidacji
            if abs(price_vs_sma200_pct) < 5:  # Blisko SMA200
                confidence += 0.2
                reasoning.append(f"Price near SMA200 ({price_vs_sma200_pct:.1f}%)")

            if 40 < indicators.rsi < 60:  # RSI w neutralnej strefie
                confidence += 0.2
                reasoning.append(f"RSI neutral ({indicators.rsi:.1f})")

            if not high_volatility:
                confidence += 0.1
                reasoning.append(f"Low volatility ({indicators.volatility:.3f})")

            return MarketRegime.SIDEWAYS, min(confidence, 0.9), reasoning

        # NEUTRAL: Mieszane sygnały lub niewystarczające dane
        else:
            confidence = 0.3
            reasoning.append("Mixed signals - no clear regime")
            reasoning.append(f"Price vs SMA200: {price_vs_sma200_pct:.1f}%")
            reasoning.append(f"ADX: {indicators.adx:.1f} (moderate trend)")
            reasoning.append(f"RSI: {indicators.rsi:.1f}")

            return MarketRegime.NEUTRAL, confidence, reasoning

    async def detect_regime(self) -> str:
        """
        Główna metoda detekcji fazy rynku

        Returns:
            String z fazą rynku: "BULLISH", "BEARISH", "SIDEWAYS", "NEUTRAL"
        """

        try:
            logger.info("📊 Starting market regime detection...")

            # KROK 1: Pobierz dane cenowe
            price_data = await self.get_price_data()
            if price_data is None or len(price_data) < 50:
                logger.warning("⚠️ Insufficient price data for regime detection")
                return MarketRegime.NEUTRAL.value

            # KROK 2: Oblicz wskaźniki techniczne
            indicators = self.calculate_technical_indicators(price_data)

            # KROK 3: Klasyfikuj fazę rynku
            regime, confidence, reasoning = self.classify_regime(indicators)

            # KROK 4: Stwórz pełną analizę
            analysis = RegimeAnalysis(
                regime=regime,
                confidence=confidence,
                indicators=indicators,
                reasoning=reasoning,
                timestamp=time.time()
            )

            # KROK 5: Zapisz w historii
            self.regime_history.append(analysis)
            if len(self.regime_history) > 100:  # Zachowaj ostatnie 100 analiz
                self.regime_history.pop(0)

            self.current_regime = regime
            self.last_analysis = analysis

            # KROK 6: Loguj wyniki
            logger.info(f"📊 Market regime detected: {regime.value}")
            logger.info(f"   Confidence: {confidence:.1%}")
            logger.info(f"   Price: ${indicators.current_price:.2f}")
            logger.info(f"   SMA200: ${indicators.sma_200:.2f}")
            logger.info(f"   ADX: {indicators.adx:.1f}")
            logger.info(f"   RSI: {indicators.rsi:.1f}")

            for reason in reasoning[:3]:  # Log top 3 reasons
                logger.info(f"   • {reason}")

            return regime.value

        except Exception as e:
            logger.error(f"❌ Error in market regime detection: {e}")
            return MarketRegime.NEUTRAL.value

    def get_regime_summary(self) -> Dict:
        """
        Zwraca podsumowanie obecnej fazy rynku

        Returns:
            Słownik z kluczowymi informacjami o fazie rynku
        """

        if self.last_analysis is None:
            return {
                "regime": MarketRegime.NEUTRAL.value,
                "confidence": 0.0,
                "status": "No analysis available"
            }

        analysis = self.last_analysis

        return {
            "regime": analysis.regime.value,
            "confidence": analysis.confidence,
            "timestamp": analysis.timestamp,
            "indicators": {
                "current_price": analysis.indicators.current_price,
                "sma_200": analysis.indicators.sma_200,
                "price_vs_sma200_pct": analysis.indicators.price_vs_sma200 * 100,
                "rsi": analysis.indicators.rsi,
                "adx": analysis.indicators.adx,
                "volatility": analysis.indicators.volatility,
                "trend_strength": analysis.indicators.trend_strength
            },
            "reasoning": analysis.reasoning,
            "regime_changes_today": len([a for a in self.regime_history
                                       if time.time() - a.timestamp < 86400])
        }

    def get_regime_history(self, hours: int = 24) -> List[Dict]:
        """
        Zwraca historię zmian faz rynku

        Args:
            hours: Liczba godzin wstecz

        Returns:
            Lista analiz z ostatnich godzin
        """

        cutoff_time = time.time() - (hours * 3600)

        recent_history = [
            {
                "regime": analysis.regime.value,
                "confidence": analysis.confidence,
                "timestamp": analysis.timestamp,
                "price": analysis.indicators.current_price
            }
            for analysis in self.regime_history
            if analysis.timestamp > cutoff_time
        ]

        return sorted(recent_history, key=lambda x: x['timestamp'], reverse=True)
