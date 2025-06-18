# THE OVERMIND PROTOCOL - AI Brain

🧠 **Advanced AI Brain for autonomous trading decisions**

## Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -e .

# Copy configuration template
cp ../config/environments/.env.brain.template .env

# Edit configuration with your API keys
nano .env
```

### 2. Configure API Keys

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Alternative LLM providers
GROQ_API_KEY=your_groq_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 3. Start AI Brain

```bash
# Development mode (standalone)
python -m overmind_brain.main

# Server mode (FastAPI)
python -m overmind_brain.main server

# Or with uvicorn directly
uvicorn overmind_brain.main:app --host 0.0.0.0 --port 8000
```

### 4. Test Brain

```bash
# Health check
curl http://localhost:8000/health

# Brain status
curl http://localhost:8000/status

# Manual analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "SOL/USDT",
    "price": 100.0,
    "volume": 1000000
  }'
```

## Architecture

```
🧠 AI Brain Components:
├── 📚 Vector Memory (Chroma DB)
├── 🎯 Decision Engine (OpenAI GPT-4)
├── 🛡️ Risk Analyzer
├── 📊 Market Analyzer
└── 🌐 FastAPI Server
```

## API Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /status` - Comprehensive status
- `GET /debug/components` - Debug info

### Analysis
- `POST /analyze` - Manual market analysis
- `GET /memory/search?query=...` - Search experiences
- `GET /memory/recent` - Recent experiences
- `GET /memory/stats` - Memory statistics

### Control
- `POST /memory/update-outcome` - Update outcomes
- `POST /control/emergency-stop` - Emergency stop

## Configuration

### Environment Variables

```bash
# AI Core
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.1

# Vector Memory
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
CHROMA_COLLECTION_NAME=overmind_memory

# Communication
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379

# Risk Management
MAX_PORTFOLIO_RISK=0.02
MAX_POSITION_SIZE=0.1
MIN_DECISION_CONFIDENCE=0.6

# Server
BRAIN_HOST=0.0.0.0
BRAIN_PORT=8000
```

## Development

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_vector_memory.py -v
```

### Component Testing

```bash
# Test imports
python -c "
import sys
sys.path.insert(0, 'src')
from overmind_brain.brain import OVERMINDBrain
print('✅ All components imported successfully')
"

# Test brain creation
python -c "
import sys
sys.path.insert(0, 'src')
from overmind_brain.brain import OVERMINDBrain
brain = OVERMINDBrain(redis_host='localhost', openai_api_key='test')
print('✅ Brain created successfully')
"
```

## Docker Deployment

```bash
# Build image
docker build -t overmind-brain .

# Run container
docker run -d \
  --name overmind-brain \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e DRAGONFLY_HOST=host.docker.internal \
  overmind-brain

# Check logs
docker logs overmind-brain
```

## Integration with THE OVERMIND PROTOCOL

### Communication Flow

```
Rust Executor → DragonflyDB → AI Brain → Decision → DragonflyDB → Rust Executor
```

### Message Format

**Incoming (Market Events):**
```json
{
  "symbol": "SOL/USDT",
  "price": 100.0,
  "volume": 1000000,
  "trend": "bullish",
  "timestamp": "2024-06-17T12:00:00Z"
}
```

**Outgoing (Trading Commands):**
```json
{
  "symbol": "SOL/USDT",
  "action": "BUY",
  "confidence": 0.8,
  "reasoning": "Strong bullish signals",
  "quantity": 100.0,
  "timestamp": "2024-06-17T12:00:00Z",
  "source": "overmind_brain"
}
```

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status | jq

# Memory statistics
curl http://localhost:8000/memory/stats | jq
```

### Logs

```bash
# View logs
tail -f logs/overmind_brain.log
tail -f logs/ai_decisions.log
tail -f logs/vector_memory.log
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the brain directory
   cd brain
   # Install in development mode
   pip install -e .
   ```

2. **OpenAI API Errors**
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   # Test API connection
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

3. **DragonflyDB Connection**
   ```bash
   # Test Redis connection
   redis-cli -h localhost -p 6379 ping
   ```

4. **Memory Issues**
   ```bash
   # Clear vector memory (development only)
   curl -X POST http://localhost:8000/memory/clear?confirm=true
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true

# Start with debug endpoints
export ENABLE_DEBUG_ENDPOINTS=true
python -m overmind_brain.main server
```

## Performance

### Typical Performance
- **Decision Latency:** 2-5 seconds
- **Memory Usage:** ~500MB with models loaded
- **Throughput:** Continuous event processing
- **Confidence Threshold:** 60% minimum for execution

### Optimization Tips
- Use faster OpenAI models for development (gpt-3.5-turbo)
- Adjust temperature for faster/more deterministic responses
- Implement caching for repeated queries
- Use smaller embedding models for faster similarity search

## Security

### API Security
```bash
# Enable API key authentication
export ENABLE_API_KEY_AUTH=true
export API_KEY=your_secure_api_key

# Use with requests
curl -H "X-API-Key: your_secure_api_key" \
     http://localhost:8000/status
```

### Rate Limiting
```bash
# Configure rate limits
export RATE_LIMIT_REQUESTS=100
export RATE_LIMIT_WINDOW=60
```

## Support

For issues and questions:
1. Check logs in `logs/` directory
2. Review configuration in `.env` file
3. Test individual components
4. Check THE OVERMIND PROTOCOL documentation

---

**🧠 THE OVERMIND PROTOCOL AI Brain - Ready for autonomous trading decisions!**
