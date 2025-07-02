#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Exit Strategy Manager
AI-driven exit decisions based on multi-factor analysis for Post-Trade Intelligence
"""

import asyncio
import json
import time
import redis
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExitStrategyManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        self.exit_decisions = {}
        self.position_history = {}
        
        # DeepSeek AI integration
        self.deepseek_api_key = "sk-fa74e467d54d48b88c33f8930be38256"
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        
        # Exit strategy parameters
        self.profit_targets = {
            'conservative': 0.05,   # 5% profit target
            'moderate': 0.10,       # 10% profit target
            'aggressive': 0.20      # 20% profit target
        }
        
        self.stop_losses = {
            'tight': -0.02,         # 2% stop loss
            'moderate': -0.05,      # 5% stop loss
            'loose': -0.10          # 10% stop loss
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            'high_volatility': 0.15,
            'negative_sentiment': 0.3,
            'whale_selling': 0.7,
            'time_decay': 24 * 3600  # 24 hours
        }
    
    async def get_position_data(self) -> Dict:
        """Get current position data from Redis"""
        try:
            position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
            if position_updates:
                return json.loads(position_updates[0])
            return {}
        except Exception as e:
            logger.error(f"❌ Error getting position data: {e}")
            return {}
    
    async def get_news_intelligence(self) -> Dict:
        """Get latest news intelligence from Redis"""
        try:
            news_updates = self.redis_client.lrange('overmind:news_intelligence', 0, 0)
            if news_updates:
                return json.loads(news_updates[0])
            return {}
        except Exception as e:
            logger.error(f"❌ Error getting news intelligence: {e}")
            return {}
    
    async def get_whale_analytics(self) -> Dict:
        """Get latest whale analytics from Redis"""
        try:
            whale_updates = self.redis_client.lrange('overmind:whale_analytics', 0, 0)
            if whale_updates:
                return json.loads(whale_updates[0])
            return {}
        except Exception as e:
            logger.error(f"❌ Error getting whale analytics: {e}")
            return {}
    
    def calculate_technical_score(self, position: Dict) -> float:
        """Calculate technical analysis score for exit decision"""
        try:
            pnl_percentage = position.get('pnl_percentage', 0)
            current_price = position.get('current_price', 0)
            avg_entry_price = position.get('avg_entry_price', 0)
            
            if avg_entry_price == 0:
                return 0.5
            
            # Price momentum (simplified)
            price_momentum = (current_price - avg_entry_price) / avg_entry_price
            
            # Technical score based on P&L and momentum
            if pnl_percentage > 15:  # Strong profit
                return 0.8  # Strong exit signal
            elif pnl_percentage > 5:  # Moderate profit
                return 0.6  # Moderate exit signal
            elif pnl_percentage < -5:  # Loss
                return 0.7  # Exit to cut losses
            else:
                return 0.4  # Hold
                
        except Exception as e:
            logger.error(f"❌ Error calculating technical score: {e}")
            return 0.5
    
    def calculate_sentiment_score(self, symbol: str, news_data: Dict) -> float:
        """Calculate sentiment-based exit score"""
        try:
            news_intelligence = news_data.get('news_intelligence', {})
            symbol_news = news_intelligence.get(symbol, {})
            
            sentiment = symbol_news.get('avg_sentiment', 0.5)
            confidence = symbol_news.get('confidence', 0.0)
            signals = symbol_news.get('signals', [])
            
            # Convert sentiment to exit score
            if 'NEGATIVE_SENTIMENT' in signals and confidence > 0.5:
                return 0.8  # Strong exit signal on negative news
            elif sentiment < 0.3 and confidence > 0.3:
                return 0.7  # Exit on negative sentiment
            elif sentiment > 0.7 and confidence > 0.3:
                return 0.3  # Hold on positive sentiment
            else:
                return 0.5  # Neutral
                
        except Exception as e:
            logger.error(f"❌ Error calculating sentiment score: {e}")
            return 0.5
    
    def calculate_whale_score(self, symbol: str, whale_data: Dict) -> float:
        """Calculate whale activity-based exit score"""
        try:
            whale_analytics = whale_data.get('whale_analytics', {})
            symbol_whales = whale_analytics.get(symbol, {})
            
            sell_pressure = symbol_whales.get('sell_pressure', 0.5)
            whale_count = symbol_whales.get('whale_count', 0)
            signals = symbol_whales.get('signals', [])
            
            # Exit score based on whale activity
            if 'WHALE_DISTRIBUTION' in signals:
                return 0.8  # Strong exit signal
            elif sell_pressure > 0.7:
                return 0.7  # High sell pressure
            elif 'WHALE_ACCUMULATION' in signals:
                return 0.2  # Hold on accumulation
            else:
                return 0.5  # Neutral
                
        except Exception as e:
            logger.error(f"❌ Error calculating whale score: {e}")
            return 0.5
    
    def calculate_time_decay_score(self, position: Dict) -> float:
        """Calculate time-based exit score"""
        try:
            entry_time = position.get('entry_time', time.time())
            current_time = time.time()
            position_age = current_time - entry_time
            
            # Time decay factor (positions get riskier over time)
            if position_age > 7 * 24 * 3600:  # 7 days
                return 0.7  # Old position, consider exit
            elif position_age > 3 * 24 * 3600:  # 3 days
                return 0.6  # Aging position
            elif position_age > 24 * 3600:  # 1 day
                return 0.5  # Normal
            else:
                return 0.4  # Fresh position
                
        except Exception as e:
            logger.error(f"❌ Error calculating time decay score: {e}")
            return 0.5
    
    async def get_ai_exit_recommendation(self, symbol: str, analysis_data: Dict) -> Dict:
        """Get AI recommendation from DeepSeek"""
        try:
            prompt = f"""
            Analyze this trading position for exit decision:
            
            Symbol: {symbol}
            Technical Score: {analysis_data['technical_score']:.2f}
            Sentiment Score: {analysis_data['sentiment_score']:.2f}
            Whale Score: {analysis_data['whale_score']:.2f}
            Time Decay Score: {analysis_data['time_decay_score']:.2f}
            
            Position P&L: {analysis_data.get('pnl_percentage', 0):.2f}%
            Position Age: {analysis_data.get('position_age_hours', 0):.1f} hours
            
            Provide exit recommendation:
            1. EXIT_IMMEDIATELY (score > 0.8)
            2. EXIT_PARTIAL (score 0.6-0.8) 
            3. HOLD (score 0.4-0.6)
            4. ACCUMULATE (score < 0.4)
            
            Return JSON: {{"action": "EXIT_IMMEDIATELY", "confidence": 0.85, "reasoning": "explanation"}}
            """
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are an expert crypto trading AI focused on optimal exit strategies."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 200
            }
            
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.deepseek_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data['choices'][0]['message']['content']
                
                # Try to parse JSON response
                try:
                    return json.loads(ai_response)
                except:
                    # Fallback parsing
                    if "EXIT_IMMEDIATELY" in ai_response:
                        return {"action": "EXIT_IMMEDIATELY", "confidence": 0.8, "reasoning": "AI analysis"}
                    elif "EXIT_PARTIAL" in ai_response:
                        return {"action": "EXIT_PARTIAL", "confidence": 0.6, "reasoning": "AI analysis"}
                    elif "ACCUMULATE" in ai_response:
                        return {"action": "ACCUMULATE", "confidence": 0.4, "reasoning": "AI analysis"}
                    else:
                        return {"action": "HOLD", "confidence": 0.5, "reasoning": "AI analysis"}
            
        except Exception as e:
            logger.error(f"❌ Error getting AI recommendation: {e}")
        
        # Fallback to rule-based decision
        composite_score = (
            analysis_data['technical_score'] * 0.3 +
            analysis_data['sentiment_score'] * 0.25 +
            analysis_data['whale_score'] * 0.25 +
            analysis_data['time_decay_score'] * 0.2
        )
        
        if composite_score > 0.75:
            return {"action": "EXIT_IMMEDIATELY", "confidence": composite_score, "reasoning": "High composite exit score"}
        elif composite_score > 0.6:
            return {"action": "EXIT_PARTIAL", "confidence": composite_score, "reasoning": "Moderate exit signals"}
        elif composite_score < 0.4:
            return {"action": "ACCUMULATE", "confidence": 1 - composite_score, "reasoning": "Strong hold signals"}
        else:
            return {"action": "HOLD", "confidence": 0.5, "reasoning": "Neutral signals"}
    
    async def analyze_position_exit(self, symbol: str, position: Dict, news_data: Dict, whale_data: Dict) -> Dict:
        """Comprehensive exit analysis for a position"""
        try:
            # Calculate individual scores
            technical_score = self.calculate_technical_score(position)
            sentiment_score = self.calculate_sentiment_score(symbol, news_data)
            whale_score = self.calculate_whale_score(symbol, whale_data)
            time_decay_score = self.calculate_time_decay_score(position)
            
            # Prepare analysis data
            analysis_data = {
                'symbol': symbol,
                'technical_score': technical_score,
                'sentiment_score': sentiment_score,
                'whale_score': whale_score,
                'time_decay_score': time_decay_score,
                'pnl_percentage': position.get('pnl_percentage', 0),
                'position_age_hours': (time.time() - position.get('entry_time', time.time())) / 3600,
                'unrealized_pnl': position.get('unrealized_pnl', 0),
                'quantity': position.get('quantity', 0)
            }
            
            # Get AI recommendation
            ai_recommendation = await self.get_ai_exit_recommendation(symbol, analysis_data)
            
            # Combine all analysis
            exit_analysis = {
                'symbol': symbol,
                'analysis_scores': analysis_data,
                'ai_recommendation': ai_recommendation,
                'composite_score': (technical_score + sentiment_score + whale_score + time_decay_score) / 4,
                'timestamp': time.time()
            }
            
            return exit_analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing position exit for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': time.time()
            }
    
    async def generate_exit_signals(self) -> Dict:
        """Generate exit signals for all positions"""
        try:
            # Get all required data
            position_data = await self.get_position_data()
            news_data = await self.get_news_intelligence()
            whale_data = await self.get_whale_analytics()
            
            positions = position_data.get('positions', {})
            exit_signals = {}
            
            for symbol, position in positions.items():
                if position.get('quantity', 0) > 0:  # Only analyze open positions
                    exit_analysis = await self.analyze_position_exit(symbol, position, news_data, whale_data)
                    exit_signals[symbol] = exit_analysis
                    
                    # Small delay between analyses
                    await asyncio.sleep(1)
            
            return exit_signals
            
        except Exception as e:
            logger.error(f"❌ Error generating exit signals: {e}")
            return {}
    
    async def publish_exit_signals(self, exit_signals: Dict):
        """Publish exit signals to Redis"""
        try:
            exit_update = {
                'timestamp': time.time(),
                'exit_signals': exit_signals,
                'update_type': 'exit_strategy'
            }
            
            self.redis_client.lpush('overmind:exit_signals', json.dumps(exit_update))
            
            # Keep only last 50 updates
            self.redis_client.ltrim('overmind:exit_signals', 0, 49)
            
            # Also publish individual exit actions
            for symbol, analysis in exit_signals.items():
                ai_rec = analysis.get('ai_recommendation', {})
                action = ai_rec.get('action', 'HOLD')
                
                if action in ['EXIT_IMMEDIATELY', 'EXIT_PARTIAL']:
                    exit_signal = {
                        'action': 'SELL',
                        'symbol': symbol,
                        'quantity': analysis['analysis_scores']['quantity'] if action == 'EXIT_IMMEDIATELY' else analysis['analysis_scores']['quantity'] * 0.5,
                        'confidence': ai_rec.get('confidence', 0.5),
                        'strategy': 'POST_TRADE_INTELLIGENCE',
                        'reasoning': ai_rec.get('reasoning', 'AI exit decision'),
                        'mev_protection': True,
                        'exit_type': action
                    }
                    
                    self.redis_client.lpush('overmind:trading_signals', json.dumps(exit_signal))
            
        except Exception as e:
            logger.error(f"❌ Error publishing exit signals: {e}")
    
    def print_exit_summary(self, exit_signals: Dict):
        """Print exit strategy summary"""
        print("\n🎯 THE OVERMIND PROTOCOL - EXIT STRATEGY MANAGER")
        print("=" * 60)
        
        if not exit_signals:
            print("📊 No positions to analyze")
            return
        
        for symbol, analysis in exit_signals.items():
            ai_rec = analysis.get('ai_recommendation', {})
            action = ai_rec.get('action', 'HOLD')
            confidence = ai_rec.get('confidence', 0.5)
            composite_score = analysis.get('composite_score', 0.5)
            
            # Action indicator
            if action == 'EXIT_IMMEDIATELY':
                indicator = "🔴 EXIT NOW"
            elif action == 'EXIT_PARTIAL':
                indicator = "🟠 EXIT 50%"
            elif action == 'ACCUMULATE':
                indicator = "🟢 BUY MORE"
            else:
                indicator = "⚪ HOLD"
            
            pnl = analysis.get('analysis_scores', {}).get('pnl_percentage', 0)
            
            print(f"{indicator} {symbol}: {action} (Conf: {confidence:.2f}) | "
                  f"P&L: {pnl:+.2f}% | Score: {composite_score:.2f}")
            
            reasoning = ai_rec.get('reasoning', '')
            if reasoning:
                print(f"   💭 {reasoning[:80]}...")
        
        print(f"🔄 Last Update: {datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')}")
    
    async def exit_strategy_loop(self):
        """Main exit strategy monitoring loop"""
        logger.info("🚀 Starting Exit Strategy Manager...")
        
        while True:
            try:
                # Generate exit signals
                exit_signals = await self.generate_exit_signals()
                
                # Publish to Redis
                await self.publish_exit_signals(exit_signals)
                
                # Print summary
                self.print_exit_summary(exit_signals)
                
                # Wait 2 minutes before next analysis
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"❌ Error in exit strategy loop: {e}")
                await asyncio.sleep(60)

async def main():
    exit_manager = ExitStrategyManager()
    await exit_manager.exit_strategy_loop()

if __name__ == "__main__":
    asyncio.run(main())
