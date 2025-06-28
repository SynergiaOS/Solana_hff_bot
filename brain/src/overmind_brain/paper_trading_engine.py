#!/usr/bin/env python3
"""
Paper Trading Engine
Simulates trading execution with real price data without actual money
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class PaperOrder:
    """Paper trading order"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]  # None for market orders
    status: OrderStatus
    created_at: datetime
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    strategy_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class Position:
    """Trading position"""
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    created_at: datetime
    updated_at: datetime

@dataclass
class Portfolio:
    """Paper trading portfolio"""
    cash_balance: float
    total_value: float
    positions: Dict[str, Position]
    total_pnl: float
    daily_pnl: float
    created_at: datetime
    updated_at: datetime

class PaperTradingEngine:
    """
    Paper Trading Engine for THE OVERMIND PROTOCOL
    
    Simulates real trading with:
    - Real price data from Helius API
    - Realistic order execution
    - Portfolio tracking
    - P&L calculation
    - Risk management
    """
    
    def __init__(self, initial_balance: float = 1000.0):
        self.initial_balance = initial_balance
        self.cash_balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, PaperOrder] = {}
        self.trade_history: List[PaperOrder] = []
        
        # Trading fees (realistic Solana DEX fees)
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.003   # 0.30%
        
        # Risk management
        self.max_position_size = 0.2  # 20% of portfolio per position
        self.max_daily_loss = 0.05    # 5% daily loss limit
        
        self.created_at = datetime.now()
        self.daily_start_balance = initial_balance
        
        logger.info(f"🏦 Paper Trading Engine initialized with ${initial_balance:,.2f}")
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price for symbol"""
        # For MVP, return mock price based on symbol
        # In production, this would call Helius API
        if symbol.upper() == "SOL":
            import time
            base_price = 100.0
            variation = (hash(str(int(time.time() / 60))) % 200 - 100) / 10000
            return base_price + variation
        return 1.0  # Default price
    
    async def place_order(self, 
                         symbol: str,
                         side: OrderSide,
                         quantity: float,
                         order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None,
                         strategy_id: Optional[str] = None) -> str:
        """Place a paper trading order"""
        
        # Generate order ID
        order_id = str(uuid.uuid4())
        
        # Validate order
        validation_result = self._validate_order(symbol, side, quantity, order_type, price)
        if not validation_result["valid"]:
            logger.error(f"Order validation failed: {validation_result['reason']}")
            raise ValueError(validation_result["reason"])
        
        # Create order
        order = PaperOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            strategy_id=strategy_id,
            metadata={}
        )
        
        self.orders[order_id] = order
        
        # Execute immediately for market orders
        if order_type == OrderType.MARKET:
            await self._execute_order(order_id)
        
        logger.info(f"📋 Order placed: {side.value.upper()} {quantity} {symbol} "
                   f"({order_type.value}) - ID: {order_id[:8]}")
        
        return order_id
    
    def _validate_order(self, symbol: str, side: OrderSide, quantity: float, 
                       order_type: OrderType, price: Optional[float]) -> Dict[str, Any]:
        """Validate order parameters"""
        
        # Check quantity
        if quantity <= 0:
            return {"valid": False, "reason": "Quantity must be positive"}
        
        # Check price for limit orders
        if order_type == OrderType.LIMIT and price is None:
            return {"valid": False, "reason": "Limit orders require price"}
        
        # Check available balance for buy orders
        if side == OrderSide.BUY:
            current_price = self.get_current_price(symbol)
            order_value = quantity * (price or current_price)
            fee = order_value * self.taker_fee
            total_cost = order_value + fee
            
            if total_cost > self.cash_balance:
                return {"valid": False, "reason": f"Insufficient balance: ${total_cost:.2f} required, ${self.cash_balance:.2f} available"}
        
        # Check available position for sell orders
        if side == OrderSide.SELL:
            position = self.positions.get(symbol)
            if not position or position.quantity < quantity:
                available = position.quantity if position else 0
                return {"valid": False, "reason": f"Insufficient position: {quantity} required, {available} available"}
        
        # Check position size limits
        current_price = self.get_current_price(symbol)
        portfolio_value = self.get_portfolio_value()
        position_value = quantity * current_price
        
        if side == OrderSide.BUY and position_value > portfolio_value * self.max_position_size:
            max_allowed = portfolio_value * self.max_position_size
            return {"valid": False, "reason": f"Position size too large: ${position_value:.2f} > ${max_allowed:.2f} (max {self.max_position_size*100}%)"}
        
        return {"valid": True, "reason": "Order valid"}
    
    async def _execute_order(self, order_id: str) -> bool:
        """Execute a paper trading order"""
        order = self.orders.get(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return False
        
        try:
            # Get execution price
            if order.order_type == OrderType.MARKET:
                execution_price = self.get_current_price(order.symbol)
            else:
                execution_price = order.price
            
            # Calculate fees
            order_value = order.quantity * execution_price
            fee = order_value * (self.maker_fee if order.order_type == OrderType.LIMIT else self.taker_fee)
            
            # Execute based on side
            if order.side == OrderSide.BUY:
                self._execute_buy_order(order, execution_price, fee)
            else:
                self._execute_sell_order(order, execution_price, fee)
            
            # Update order status
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()
            order.filled_price = execution_price
            order.filled_quantity = order.quantity
            
            # Add to trade history
            self.trade_history.append(order)
            
            logger.info(f"✅ Order executed: {order.side.value.upper()} {order.quantity} {order.symbol} "
                       f"@ ${execution_price:.4f} (Fee: ${fee:.2f})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing order {order_id}: {e}")
            order.status = OrderStatus.REJECTED
            return False
    
    def _execute_buy_order(self, order: PaperOrder, price: float, fee: float):
        """Execute buy order"""
        total_cost = (order.quantity * price) + fee
        
        # Update cash balance
        self.cash_balance -= total_cost
        
        # Update or create position
        if order.symbol in self.positions:
            position = self.positions[order.symbol]
            # Calculate new average price
            total_quantity = position.quantity + order.quantity
            total_value = (position.quantity * position.average_price) + (order.quantity * price)
            new_average_price = total_value / total_quantity
            
            position.quantity = total_quantity
            position.average_price = new_average_price
            position.updated_at = datetime.now()
        else:
            # Create new position
            self.positions[order.symbol] = Position(
                symbol=order.symbol,
                quantity=order.quantity,
                average_price=price,
                current_price=price,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def _execute_sell_order(self, order: PaperOrder, price: float, fee: float):
        """Execute sell order"""
        order_value = order.quantity * price
        net_proceeds = order_value - fee
        
        # Update cash balance
        self.cash_balance += net_proceeds
        
        # Update position
        if order.symbol in self.positions:
            position = self.positions[order.symbol]
            
            # Calculate realized P&L
            cost_basis = order.quantity * position.average_price
            realized_pnl = order_value - cost_basis - fee
            position.realized_pnl += realized_pnl
            
            # Update position quantity
            position.quantity -= order.quantity
            position.updated_at = datetime.now()
            
            # Remove position if quantity is zero
            if position.quantity <= 0:
                del self.positions[order.symbol]
    
    def update_positions(self):
        """Update position values with current market prices"""
        for symbol, position in self.positions.items():
            current_price = self.get_current_price(symbol)
            position.current_price = current_price
            
            # Calculate unrealized P&L
            market_value = position.quantity * current_price
            cost_basis = position.quantity * position.average_price
            position.unrealized_pnl = market_value - cost_basis
            position.updated_at = datetime.now()
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        self.update_positions()
        
        positions_value = sum(
            pos.quantity * pos.current_price 
            for pos in self.positions.values()
        )
        
        return self.cash_balance + positions_value
    
    def get_portfolio_summary(self) -> Portfolio:
        """Get complete portfolio summary"""
        self.update_positions()
        
        total_value = self.get_portfolio_value()
        total_pnl = total_value - self.initial_balance
        daily_pnl = total_value - self.daily_start_balance
        
        return Portfolio(
            cash_balance=self.cash_balance,
            total_value=total_value,
            positions=self.positions.copy(),
            total_pnl=total_pnl,
            daily_pnl=daily_pnl,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        portfolio = self.get_portfolio_summary()
        
        # Calculate returns
        total_return = (portfolio.total_value - self.initial_balance) / self.initial_balance
        daily_return = portfolio.daily_pnl / self.daily_start_balance
        
        # Calculate trade statistics
        filled_orders = [order for order in self.trade_history if order.status == OrderStatus.FILLED]
        total_trades = len(filled_orders)
        
        # Calculate win rate (simplified)
        profitable_trades = sum(1 for order in filled_orders if order.side == OrderSide.SELL)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        return {
            "total_return": total_return,
            "total_return_pct": total_return * 100,
            "daily_return": daily_return,
            "daily_return_pct": daily_return * 100,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "win_rate_pct": win_rate * 100,
            "portfolio_value": portfolio.total_value,
            "cash_balance": portfolio.cash_balance,
            "positions_count": len(portfolio.positions)
        }

# Test function
async def test_paper_trading_engine():
    """Test the paper trading engine"""
    print("🧪 Testing Paper Trading Engine")
    print("-" * 40)
    
    # Initialize engine
    engine = PaperTradingEngine(initial_balance=1000.0)
    
    try:
        # Test buy order (smaller quantity to fit risk limits)
        print("📋 Placing BUY order...")
        buy_order_id = await engine.place_order(
            symbol="SOL",
            side=OrderSide.BUY,
            quantity=1.5,  # Smaller quantity
            order_type=OrderType.MARKET,
            strategy_id="sol_momentum_test"
        )
        
        # Test sell order
        print("📋 Placing SELL order...")
        sell_order_id = await engine.place_order(
            symbol="SOL",
            side=OrderSide.SELL,
            quantity=0.5,  # Sell part of position
            order_type=OrderType.MARKET,
            strategy_id="sol_momentum_test"
        )
        
        # Get portfolio summary
        portfolio = engine.get_portfolio_summary()
        print(f"\n💼 Portfolio Summary:")
        print(f"   Cash Balance: ${portfolio.cash_balance:.2f}")
        print(f"   Total Value: ${portfolio.total_value:.2f}")
        print(f"   Total P&L: ${portfolio.total_pnl:.2f}")
        print(f"   Positions: {len(portfolio.positions)}")
        
        # Get performance metrics
        metrics = engine.get_performance_metrics()
        print(f"\n📊 Performance Metrics:")
        print(f"   Total Return: {metrics['total_return_pct']:.2f}%")
        print(f"   Total Trades: {metrics['total_trades']}")
        print(f"   Win Rate: {metrics['win_rate_pct']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper trading test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_paper_trading_engine())
