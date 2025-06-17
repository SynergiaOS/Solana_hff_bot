# 🧠 AI-Hedge-Fund Framework - THE OVERMIND PROTOCOL Python Brain

## 📋 **OVERVIEW**

AI-Hedge-Fund Framework to główny szkielet dla Warstwy 3 (Mózg AI) w THE OVERMIND PROTOCOL. Framework zapewnia multi-agentową architekturę z długoterminową pamięcią i integracją z narzędziami zewnętrznymi.

**Source:** GitHub - virattt/ai-hedge-fund  
**Architecture:** Multi-agent AI system with RAG memory  
**Use Case:** OVERMIND Python Brain - Strategic Decision Making  
**OVERMIND Role:** Warstwa 3 - Mózg AI (Strategic Intelligence)

## 🎯 **KLUCZOWE FUNKCJONALNOŚCI DLA THE OVERMIND PROTOCOL**

### **1. Multi-Agent Architecture:**
```python
# AI Hedge Fund Agent System
# 1. Data Collection Agent - zbiera dane rynkowe
# 2. Analysis Agent - analizuje trendy i wzorce
# 3. Risk Assessment Agent - ocenia ryzyko
# 4. Portfolio Manager Agent - zarządza pozycjami
# 5. Execution Agent - generuje sygnały trading

# Rezultat: Skoordynowane decyzje AI z różnych perspektyw
```

### **2. Supported Integration Points:**
- **LLM Providers** - OpenAI, Groq, Ollama (local)
- **Financial Data** - Financial Datasets API
- **Backtesting** - Historical performance analysis
- **Real-time Processing** - Live market data integration
- **FastAPI Backend** - REST API for external communication
- **Vector Memory** - Long-term learning capabilities

## 🚀 **IMPLEMENTACJA DLA THE OVERMIND PROTOCOL**

### **1. Installation & Setup:**
```bash
# Clone ai-hedge-fund framework
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your-openai-api-key
# GROQ_API_KEY=your-groq-api-key
# FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
```

### **2. Basic Usage:**
```python
# Run AI hedge fund for specific tickers
poetry run python src/main.py --ticker AAPL,MSFT,NVDA

# Run with reasoning display
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --show-reasoning

# Run with local LLMs (Ollama)
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --ollama

# Run for specific date range
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01
```

### **3. THE OVERMIND PROTOCOL Integration:**
```python
import asyncio
from typing import Dict, List, Optional
import json
import redis.asyncio as redis
from ai_hedge_fund import HedgeFundAgent, VectorMemory

class OVERMINDPythonBrain:
    """Python AI Brain for THE OVERMIND PROTOCOL"""
    
    def __init__(self):
        # Initialize AI Hedge Fund framework
        self.hedge_fund = HedgeFundAgent(
            memory=VectorMemory(provider="chroma"),
            llm_provider="openai"  # or "groq", "ollama"
        )
        
        # DragonflyDB connection for communication with Rust
        self.dragonfly = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
        # Vector memory for long-term learning
        self.vector_memory = VectorMemory()
        
    async def start_brain_loop(self):
        """Main brain loop - listens for market events and generates decisions"""
        
        while True:
            try:
                # Listen for market events from Rust executor
                market_event = await self.dragonfly.blpop('overmind:market_events', timeout=1)
                
                if market_event:
                    event_data = json.loads(market_event[1])
                    
                    # Process with AI brain
                    decision = await self.process_market_event(event_data)
                    
                    # Send decision back to Rust executor
                    await self.send_trading_decision(decision)
                    
            except Exception as e:
                print(f"Brain loop error: {e}")
                await asyncio.sleep(1)
    
    async def process_market_event(self, event_data: Dict) -> Dict:
        """Process market event with AI reasoning and memory"""
        
        # 1. Retrieve relevant context from vector memory
        context = await self.vector_memory.similarity_search(
            query=f"Market event: {event_data['symbol']} price: {event_data['price']}",
            top_k=5
        )
        
        # 2. Run AI hedge fund analysis
        analysis = await self.hedge_fund.analyze_market_data(
            symbol=event_data['symbol'],
            price_data=event_data,
            historical_context=context
        )
        
        # 3. Generate trading decision
        decision = {
            'symbol': event_data['symbol'],
            'action': analysis['recommendation'],  # BUY, SELL, HOLD
            'confidence': analysis['confidence'],
            'reasoning': analysis['reasoning'],
            'quantity': self.calculate_position_size(analysis),
            'timestamp': event_data['timestamp'],
            'ai_context': context
        }
        
        # 4. Store experience in vector memory
        await self.vector_memory.store_experience(
            situation=event_data,
            decision=decision,
            context=context
        )
        
        return decision
    
    def calculate_position_size(self, analysis: Dict) -> float:
        """Calculate position size based on AI confidence and risk"""
        base_size = 1000.0  # Base position size
        confidence_multiplier = analysis['confidence']
        risk_factor = analysis.get('risk_score', 0.5)
        
        # Adjust size based on confidence and risk
        position_size = base_size * confidence_multiplier * (1 - risk_factor)
        
        return max(100.0, min(position_size, 5000.0))  # Min 100, Max 5000
    
    async def send_trading_decision(self, decision: Dict):
        """Send trading decision to Rust executor via DragonflyDB"""
        
        # Only send high-confidence decisions
        if decision['confidence'] > 0.7:
            await self.dragonfly.lpush(
                'overmind:trading_commands',
                json.dumps(decision)
            )
            
            print(f"🧠 AI Decision: {decision['action']} {decision['symbol']} "
                  f"(Confidence: {decision['confidence']:.2f})")

# Usage example
async def main():
    brain = OVERMINDPythonBrain()
    
    print("🧠 THE OVERMIND PROTOCOL Python Brain starting...")
    await brain.start_brain_loop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 **BACKTESTING CAPABILITIES**

### **1. Historical Analysis:**
```python
# Run backtester for performance analysis
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA

# Backtest with local LLMs
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA --ollama

# Backtest for specific period
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01
```

### **2. Performance Metrics:**
```python
# Backtesting results include:
backtest_results = {
    'total_return': 0.15,  # 15% return
    'sharpe_ratio': 1.2,
    'max_drawdown': 0.08,  # 8% max drawdown
    'win_rate': 0.65,      # 65% winning trades
    'trades_count': 150,
    'avg_trade_duration': '2.3 days'
}
```

## 🔧 **FASTAPI BACKEND INTEGRATION**

### **1. REST API Endpoints:**
```python
# Start FastAPI backend
cd app/backend
poetry run uvicorn main:app --reload

# Available endpoints:
# POST /hedge-fund/run - Run AI hedge fund analysis
# GET /ping - Health check
```

### **2. API Integration Example:**
```python
import requests

# Run hedge fund via API
response = requests.post('http://localhost:8000/hedge-fund/run', json={
    'tickers': ['AAPL', 'MSFT', 'NVDA'],
    'start_date': '2024-01-01',
    'end_date': '2024-03-01',
    'show_reasoning': True
})

results = response.json()
```

## 🎯 **INTEGRATION Z THE OVERMIND PROTOCOL**

### **1. Docker Integration:**
```yaml
# docker-compose.yml addition for Python Brain
version: '3.8'
services:
  overmind-python-brain:
    build: ./ai-hedge-fund
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DRAGONFLY_URL=redis://dragonfly:6379
      - VECTOR_DB_URL=http://chroma:8000
    depends_on:
      - dragonfly
      - chroma
    volumes:
      - ./ai-hedge-fund:/app
    command: poetry run python src/overmind_brain.py
```

### **2. Pixi Integration:**
```toml
# pixi.toml - Unified environment management
[project]
name = "overmind-protocol"
channels = ["conda-forge"]
platforms = ["linux-64"]

[tasks]
# Python Brain tasks
start-brain = "cd ai-hedge-fund && poetry run python src/overmind_brain.py"
test-brain = "cd ai-hedge-fund && poetry run pytest"
backtest = "cd ai-hedge-fund && poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA"

# Rust Executor tasks
build-executor = "cargo build --release --manifest-path solana_executor/Cargo.toml"
test-executor = "cargo test --manifest-path solana_executor/Cargo.toml"

# Full system tasks
start-overmind = { depends_on = ["start-brain", "build-executor"] }
test-all = { depends_on = ["test-brain", "test-executor"] }

[dependencies]
python = "3.11"
poetry = "*"
redis = ">=5.0"
```

## 📚 **RESOURCES**

- [AI Hedge Fund GitHub](https://github.com/virattt/ai-hedge-fund)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vector Memory Patterns](https://python.langchain.com/docs/modules/data_connection/vectorstores/)

---

**Status:** 🧠 **AI-POWERED** - Multi-agent framework dla THE OVERMIND PROTOCOL Python Brain
