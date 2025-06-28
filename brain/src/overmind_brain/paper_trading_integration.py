#!/usr/bin/env python3
"""
Paper Trading Integration
Connects SOL Momentum Strategy with Paper Trading Engine
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from .sol_momentum_integration import SOLMomentumIntegration
    from .paper_trading_engine import PaperTradingEngine, OrderSide, OrderType
    from .risk_management import RiskManager
except ImportError:
    # Direct import for testing
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from sol_momentum_integration import SOLMomentumIntegration
    from paper_trading_engine import PaperTradingEngine, OrderSide, OrderType
    from risk_management import RiskManager

logger = logging.getLogger(__name__)

class PaperTradingIntegration:
    """
    Integration between SOL Momentum Strategy and Paper Trading Engine
    
    Features:
    - Automatic signal execution
    - Position sizing based on confidence
    - Risk management integration
    - Performance tracking
    """
    
    def __init__(self, initial_balance: float = 1000.0):
        self.sol_momentum = SOLMomentumIntegration()
        self.paper_engine = PaperTradingEngine(initial_balance)
        self.risk_manager = RiskManager()

        # Trading parameters
        self.base_position_size = 0.1  # 10% of portfolio per trade
        self.confidence_multiplier = 1.5  # Multiply position size by confidence
        self.min_confidence = 0.6  # Minimum confidence to trade
        
        # State tracking
        self.current_position_size = 0.0
        self.last_signal_time: Optional[datetime] = None
        self.trade_count = 0
        
        logger.info("🔗 Paper Trading Integration initialized")
    
    async def initialize(self) -> bool:
        """Initialize both components"""
        try:
            # Initialize SOL momentum strategy
            sol_success = await self.sol_momentum.initialize()
            if not sol_success:
                logger.error("Failed to initialize SOL Momentum strategy")
                return False
            
            logger.info("✅ Paper Trading Integration ready")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Paper Trading Integration: {e}")
            return False
    
    async def process_signal(self, signal: Dict[str, Any]) -> bool:
        """Process trading signal and execute if appropriate"""
        try:
            action = signal.get('action', 'HOLD')
            confidence = signal.get('confidence', 0.0)
            price = signal.get('price', 0.0)
            
            logger.info(f"📊 Processing signal: {action} (Confidence: {confidence:.2f})")
            
            # Check minimum confidence
            if confidence < self.min_confidence:
                logger.info(f"⚠️ Signal confidence {confidence:.2f} below minimum {self.min_confidence}")
                return False
            
            # Calculate position size based on confidence
            portfolio_value = self.paper_engine.get_portfolio_value()
            base_size = portfolio_value * self.base_position_size
            confidence_adjusted_size = base_size * (confidence * self.confidence_multiplier)
            
            # Execute based on signal
            if action == 'BUY':
                return await self._execute_buy_signal(signal, confidence_adjusted_size)
            elif action == 'SELL':
                return await self._execute_sell_signal(signal)
            else:
                logger.info("📊 HOLD signal - no action taken")
                return True
                
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return False
    
    async def _execute_buy_signal(self, signal: Dict[str, Any], position_size: float) -> bool:
        """Execute buy signal with risk management"""
        try:
            price = signal.get('price', 0.0)
            confidence = signal.get('confidence', 0.0)

            # Check if we already have a position
            current_position = self.paper_engine.positions.get('SOL')
            if current_position and current_position.quantity > 0:
                logger.info("⚠️ Already have SOL position, skipping BUY signal")
                return False

            # Use risk manager to calculate optimal position size
            portfolio_value = self.paper_engine.get_portfolio_value()
            volatility = 0.03  # Estimate 3% volatility for SOL (could be calculated from price history)

            quantity, risk_details = self.risk_manager.calculate_position_size(
                symbol="SOL",
                entry_price=price,
                portfolio_value=portfolio_value,
                confidence=confidence,
                volatility=volatility
            )

            # Calculate stop-loss and take-profit prices
            stop_loss_price = self.risk_manager.calculate_stop_loss_price("SOL", price, "BUY", volatility)
            take_profit_price = self.risk_manager.calculate_take_profit_price(price, stop_loss_price, "BUY")

            logger.info(f"🛡️ Risk Management: Entry=${price:.2f}, Stop=${stop_loss_price:.2f}, Target=${take_profit_price:.2f}")
            logger.info(f"📏 Position: {quantity:.4f} SOL ({risk_details['portfolio_pct']:.1f}% of portfolio)")
            
            # Place buy order
            order_id = await self.paper_engine.place_order(
                symbol="SOL",
                side=OrderSide.BUY,
                quantity=quantity,
                order_type=OrderType.MARKET,
                strategy_id="sol_momentum"
            )
            
            self.current_position_size = quantity
            self.last_signal_time = datetime.now()
            self.trade_count += 1
            
            logger.info(f"✅ BUY executed: {quantity:.4f} SOL @ ${price:.4f} "
                       f"(Confidence: {confidence:.2f}, Order: {order_id[:8]})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing BUY signal: {e}")
            return False
    
    async def _execute_sell_signal(self, signal: Dict[str, Any]) -> bool:
        """Execute sell signal"""
        try:
            price = signal.get('price', 0.0)
            confidence = signal.get('confidence', 0.0)
            
            # Check if we have a position to sell
            current_position = self.paper_engine.positions.get('SOL')
            if not current_position or current_position.quantity <= 0:
                logger.info("⚠️ No SOL position to sell")
                return False
            
            # Sell entire position
            quantity = current_position.quantity
            
            # Place sell order
            order_id = await self.paper_engine.place_order(
                symbol="SOL",
                side=OrderSide.SELL,
                quantity=quantity,
                order_type=OrderType.MARKET,
                strategy_id="sol_momentum"
            )
            
            self.current_position_size = 0.0
            self.last_signal_time = datetime.now()
            self.trade_count += 1
            
            logger.info(f"✅ SELL executed: {quantity:.4f} SOL @ ${price:.4f} "
                       f"(Confidence: {confidence:.2f}, Order: {order_id[:8]})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing SELL signal: {e}")
            return False
    
    async def run_trading_cycle(self) -> Dict[str, Any]:
        """Run one complete trading cycle"""
        try:
            # Generate signal from SOL momentum strategy
            signal = await self.sol_momentum.generate_trading_signal()
            
            if not signal:
                return {"status": "no_signal", "message": "No signal generated"}
            
            # Process the signal
            executed = await self.process_signal(signal)
            
            # Get current portfolio status
            portfolio = self.paper_engine.get_portfolio_summary()
            metrics = self.paper_engine.get_performance_metrics()

            # Check risk limits
            position_data = {symbol: {"value": pos.quantity * pos.current_price, "portfolio_pct": (pos.quantity * pos.current_price / portfolio.total_value) * 100}
                           for symbol, pos in portfolio.positions.items()}
            risk_alerts = self.risk_manager.check_risk_limits(portfolio.total_value, portfolio.daily_pnl, position_data)

            # Get risk summary
            returns = []  # Would need historical returns for proper calculation
            risk_summary = self.risk_manager.get_risk_summary(portfolio.total_value, position_data, returns)

            return {
                "status": "success",
                "signal": signal,
                "executed": executed,
                "portfolio_value": portfolio.total_value,
                "total_pnl": portfolio.total_pnl,
                "daily_pnl": portfolio.daily_pnl,
                "cash_balance": portfolio.cash_balance,
                "positions": len(portfolio.positions),
                "trade_count": self.trade_count,
                "metrics": metrics,
                "risk_alerts": len(risk_alerts),
                "risk_level": risk_summary["risk_level"],
                "risk_score": risk_summary["risk_score"]
            }
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            return {"status": "error", "message": str(e)}
    
    async def run_continuous_trading(self, interval_seconds: int = 60, max_cycles: int = 10):
        """Run continuous paper trading"""
        logger.info(f"🔄 Starting continuous paper trading (interval: {interval_seconds}s, max cycles: {max_cycles})")
        
        for cycle in range(max_cycles):
            try:
                logger.info(f"\n📊 Trading Cycle {cycle + 1}/{max_cycles}")
                
                # Run trading cycle
                result = await self.run_trading_cycle()
                
                if result["status"] == "success":
                    signal = result["signal"]
                    logger.info(f"Signal: {signal['action']} (Confidence: {signal['confidence']:.2f})")
                    logger.info(f"Executed: {result['executed']}")
                    logger.info(f"Portfolio Value: ${result['portfolio_value']:.2f}")
                    logger.info(f"Total P&L: ${result['total_pnl']:.2f}")
                    
                    if result["executed"]:
                        logger.info(f"🎯 Trade executed! Total trades: {result['trade_count']}")
                
                # Wait for next cycle
                if cycle < max_cycles - 1:
                    await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in trading cycle {cycle + 1}: {e}")
                await asyncio.sleep(interval_seconds)
        
        # Final summary
        final_portfolio = self.paper_engine.get_portfolio_summary()
        final_metrics = self.paper_engine.get_performance_metrics()
        
        logger.info(f"\n🏁 Trading Session Complete!")
        logger.info(f"Final Portfolio Value: ${final_portfolio.total_value:.2f}")
        logger.info(f"Total Return: {final_metrics['total_return_pct']:.2f}%")
        logger.info(f"Total Trades: {final_metrics['total_trades']}")
        logger.info(f"Win Rate: {final_metrics['win_rate_pct']:.1f}%")
        
        return final_metrics

# Test function
async def test_paper_trading_integration():
    """Test the complete paper trading integration"""
    print("🧪 Testing Paper Trading Integration")
    print("=" * 50)
    
    try:
        # Initialize integration
        integration = PaperTradingIntegration(initial_balance=1000.0)
        
        # Initialize components
        success = await integration.initialize()
        if not success:
            print("❌ Integration initialization failed")
            return False
        
        print("✅ Integration initialized successfully")
        
        # Run a few trading cycles
        print("\n🔄 Running trading cycles...")
        final_metrics = await integration.run_continuous_trading(
            interval_seconds=2,  # Fast for testing
            max_cycles=5
        )
        
        print(f"\n📊 Final Results:")
        print(f"   Total Return: {final_metrics['total_return_pct']:.2f}%")
        print(f"   Total Trades: {final_metrics['total_trades']}")
        print(f"   Portfolio Value: ${final_metrics['portfolio_value']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper trading integration test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_paper_trading_integration())
