#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Execution Feedback Listener
Zamyka pętlę komunikacji między Rust Executor a Python AI Brain
"""

import json
import redis
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from prompt_formatter import PromptFormatter, create_optimized_prompt
from capital_allocator import create_capital_allocator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ExecutionFeedbackListener')

class ExecutionFeedbackListener:
    """
    Nasłuchuje wyników wykonania transakcji z Rust Executor
    i aktualizuje wiedzę AI Brain w czasie rzeczywistym
    """
    
    def __init__(self):
        """Initialize the feedback listener"""
        # Redis connection for DragonflyDB
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            decode_responses=True
        )
        
        # ChromaDB for vector memory storage
        self.chroma_client = chromadb.PersistentClient(
            path="./brain/vector_memory",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collections
        try:
            self.execution_memory = self.chroma_client.get_collection("execution_memory")
        except:
            self.execution_memory = self.chroma_client.create_collection(
                name="execution_memory",
                metadata={"description": "Long-term memory of trading execution results"}
            )
        
        try:
            self.strategy_performance = self.chroma_client.get_collection("strategy_performance")
        except:
            self.strategy_performance = self.chroma_client.create_collection(
                name="strategy_performance",
                metadata={"description": "Performance tracking of trading strategies"}
            )
        
        # Active positions tracking
        self.active_positions = {}
        self.total_profit = 0.0
        self.total_trades = 0
        self.successful_trades = 0

        # English prompt formatter for DeepSeek optimization
        self.prompt_formatter = PromptFormatter()

        # Running flag
        self.running = False
        self.listener_thread = None

        logger.info("🧠 ExecutionFeedbackListener initialized with DeepSeek-V2 optimization")
        logger.info("📊 Connected to DragonflyDB and ChromaDB")
        logger.info("🇺🇸 English prompt formatting enabled for maximum AI performance")
    
    def start_listening(self):
        """Start the feedback listener in background thread"""
        if self.running:
            logger.warning("⚠️ Listener already running")
            return
        
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        logger.info("🎧 Started execution feedback listener")
    
    def stop_listening(self):
        """Stop the feedback listener"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
        logger.info("⏹️ Stopped execution feedback listener")
    
    def _listen_loop(self):
        """Main listening loop for execution results"""
        logger.info("👂 Listening for execution results on 'overmind:execution_results'...")
        
        while self.running:
            try:
                # Block and wait for new execution results
                result = self.redis_client.brpop("overmind:execution_results", timeout=1)
                
                if result:
                    channel, message = result
                    self._process_execution_result(message)
                    
            except redis.RedisError as e:
                logger.error(f"❌ Redis error: {e}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"❌ Unexpected error in listen loop: {e}")
                time.sleep(1)
    
    def _process_execution_result(self, message: str):
        """Process a single execution result"""
        try:
            result = json.loads(message)
            
            # Extract key information
            command_id = result.get('command_id', 'unknown')
            action = result.get('action', 'UNKNOWN')
            symbol = result.get('symbol', 'UNKNOWN')
            status = result.get('status', 'UNKNOWN')
            profit = float(result.get('profit', 0.0))
            mode = result.get('mode', 'UNKNOWN')
            
            logger.info(f"📨 Processing execution result: {action} {symbol} (Status: {status}, Profit: ${profit:.6f})")
            
            # Update statistics
            self.total_trades += 1
            if status == 'SUCCESS' and profit > 0:
                self.successful_trades += 1
                self.total_profit += profit
            
            # Store in vector memory for long-term learning
            self._store_in_vector_memory(result)
            
            # Update position tracking
            self._update_position_tracking(result)
            
            # Analyze strategy performance
            self._analyze_strategy_performance(result)
            
            # Log summary
            success_rate = (self.successful_trades / self.total_trades) * 100 if self.total_trades > 0 else 0
            logger.info(f"📊 Session Stats: {self.successful_trades}/{self.total_trades} trades successful ({success_rate:.1f}%), Total Profit: ${self.total_profit:.6f}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse execution result JSON: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing execution result: {e}")
    
    def _store_in_vector_memory(self, result: Dict[str, Any]):
        """Store execution result in ChromaDB vector memory with optimized English description"""
        try:
            # Generate optimized English memory prompt using DeepSeek formatter
            memory_prompt = create_optimized_prompt("execution_memory", result)

            # Create structured English description for vector embedding
            action = result.get('action', 'UNKNOWN')
            symbol = result.get('symbol', 'UNKNOWN')
            profit = result.get('profit', 0.0)
            status = result.get('status', 'UNKNOWN')
            confidence = result.get('confidence_score', 0.5)
            strategy = result.get('strategy', 'unknown')

            # Optimized English description for better semantic search
            english_description = f"Trading execution: {action} order for {symbol} using {strategy} strategy. " \
                                f"Result: {status} with ${profit:.6f} profit. Confidence level: {confidence:.2f}. " \
                                f"Execution mode: {result.get('mode', 'UNKNOWN')}. " \
                                f"Performance: {'Profitable' if profit > 0 else 'Loss' if profit < 0 else 'Neutral'}."

            # Store in execution memory with English description
            self.execution_memory.add(
                documents=[english_description],
                metadatas=[{
                    "command_id": result.get('command_id', 'unknown'),
                    "action": action,
                    "symbol": symbol,
                    "profit": profit,
                    "status": status,
                    "timestamp": result.get('timestamp', time.time()),
                    "mode": result.get('mode', 'UNKNOWN'),
                    "confidence": confidence,
                    "strategy": strategy,
                    "language": "english",
                    "prompt_optimized": True
                }],
                ids=[f"exec_{result.get('command_id', int(time.time()))}"]
            )

            logger.debug(f"💾 Stored execution result in vector memory (English optimized): {action} {symbol}")
            logger.debug(f"🧠 Generated DeepSeek memory prompt: {len(memory_prompt)} characters")

        except Exception as e:
            logger.error(f"❌ Failed to store in vector memory: {e}")
    
    def _update_position_tracking(self, result: Dict[str, Any]):
        """Update active positions based on execution result"""
        try:
            action = result.get('action', 'UNKNOWN')
            symbol = result.get('symbol', 'UNKNOWN')
            quantity = result.get('quantity', 0.0)
            price = result.get('actual_price', 0.0)
            
            if action == 'BUY':
                # Open or increase position
                if symbol not in self.active_positions:
                    self.active_positions[symbol] = {
                        'quantity': 0.0,
                        'avg_price': 0.0,
                        'total_cost': 0.0
                    }
                
                pos = self.active_positions[symbol]
                new_total_cost = pos['total_cost'] + (quantity * price)
                new_quantity = pos['quantity'] + quantity
                new_avg_price = new_total_cost / new_quantity if new_quantity > 0 else 0.0
                
                self.active_positions[symbol] = {
                    'quantity': new_quantity,
                    'avg_price': new_avg_price,
                    'total_cost': new_total_cost
                }
                
                logger.info(f"📈 Position updated: {symbol} - Qty: {new_quantity:.6f}, Avg Price: ${new_avg_price:.4f}")
                
            elif action == 'SELL':
                # Close or reduce position
                if symbol in self.active_positions:
                    pos = self.active_positions[symbol]
                    new_quantity = max(0.0, pos['quantity'] - quantity)
                    
                    if new_quantity == 0:
                        # Position closed
                        del self.active_positions[symbol]
                        logger.info(f"🔒 Position closed: {symbol}")
                    else:
                        # Position reduced
                        self.active_positions[symbol]['quantity'] = new_quantity
                        logger.info(f"📉 Position reduced: {symbol} - New Qty: {new_quantity:.6f}")
                        
        except Exception as e:
            logger.error(f"❌ Error updating position tracking: {e}")
    
    def _analyze_strategy_performance(self, result: Dict[str, Any]):
        """Analyze and store strategy performance data"""
        try:
            # Extract strategy information (if available)
            strategy = "unknown"
            if 'strategy' in result:
                strategy = result['strategy']
            elif 'command_id' in result:
                # Try to extract strategy from command_id pattern
                cmd_id = result['command_id']
                if 'scalp' in cmd_id:
                    strategy = 'scalping'
                elif 'momentum' in cmd_id:
                    strategy = 'momentum'
                elif 'arbitrage' in cmd_id:
                    strategy = 'arbitrage'
            
            profit = result.get('profit', 0.0)
            confidence = result.get('confidence_score', 0.5)
            
            # Create strategy performance record
            performance_text = f"Strategy {strategy} executed with profit ${profit:.6f} and confidence {confidence:.2f}"
            
            # Store in strategy performance collection
            self.strategy_performance.add(
                documents=[performance_text],
                metadatas=[{
                    "strategy": strategy,
                    "profit": profit,
                    "confidence": confidence,
                    "symbol": result.get('symbol', 'UNKNOWN'),
                    "timestamp": result.get('timestamp', time.time()),
                    "success": profit > 0
                }],
                ids=[f"strat_{strategy}_{int(time.time())}_{result.get('command_id', 'unknown')[:8]}"]
            )
            
            logger.debug(f"📊 Strategy performance recorded: {strategy} - Profit: ${profit:.6f}")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing strategy performance: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary"""
        success_rate = (self.successful_trades / self.total_trades) * 100 if self.total_trades > 0 else 0
        
        return {
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "success_rate": success_rate,
            "total_profit": self.total_profit,
            "active_positions": len(self.active_positions),
            "positions": self.active_positions
        }
    
    def query_execution_memory(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Query execution memory for similar past experiences"""
        try:
            results = self.execution_memory.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"❌ Error querying execution memory: {e}")
            return {}

def main():
    """Main function for testing the feedback listener"""
    listener = ExecutionFeedbackListener()
    
    try:
        listener.start_listening()
        logger.info("🎧 Execution Feedback Listener is running...")
        logger.info("📊 Waiting for execution results from Rust Executor...")
        
        # Keep running until interrupted
        while True:
            time.sleep(10)
            summary = listener.get_session_summary()
            if summary['total_trades'] > 0:
                logger.info(f"📈 Session Update: {summary['successful_trades']}/{summary['total_trades']} trades, ${summary['total_profit']:.6f} profit")
            
    except KeyboardInterrupt:
        logger.info("⏹️ Shutting down feedback listener...")
    finally:
        listener.stop_listening()

if __name__ == "__main__":
    main()
