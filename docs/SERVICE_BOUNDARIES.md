# 🏗️ THE OVERMIND PROTOCOL - Service Boundaries & Architecture

## 🎯 Overview

This document defines clear service boundaries and responsibilities for THE OVERMIND PROTOCOL's 5-layer architecture, ensuring clean separation of concerns and maintainable code.

## 🏛️ 5-Layer Architecture

### Layer 1: 🏗️ Infrastructure (Forteca)
**Location**: `infrastructure/`, `deployment/`, `monitoring/`
**Technology**: Docker, Kubernetes, Prometheus, Grafana
**Responsibility**: 
- Container orchestration
- Service discovery and networking
- Monitoring and observability
- Resource management

**Service Boundaries**:
- ✅ Manages container lifecycle
- ✅ Provides networking between services
- ✅ Collects metrics and logs
- ❌ Does NOT contain business logic
- ❌ Does NOT make trading decisions

### Layer 2: 📡 Data Ingestion (Zmysły)
**Location**: `src/modules/data_ingestor/`
**Technology**: Rust, WebSockets, HTTP clients
**Responsibility**:
- Real-time market data collection
- Solana blockchain monitoring
- Data normalization and validation
- Rate limiting and connection management

**Service Boundaries**:
- ✅ Connects to external data sources
- ✅ Normalizes data formats
- ✅ Handles connection failures
- ❌ Does NOT analyze data
- ❌ Does NOT make trading decisions

### Layer 3: 🧠 AI Brain (Mózg AI)
**Location**: `brain/`
**Technology**: Python, LangChain, OpenAI, Vector DB
**Responsibility**:
- Market analysis and pattern recognition
- Trading strategy generation
- Risk assessment
- Long-term memory and learning

**Service Boundaries**:
- ✅ Analyzes market data
- ✅ Generates trading signals
- ✅ Manages AI memory and context
- ✅ Provides strategic recommendations
- ❌ Does NOT execute trades directly
- ❌ Does NOT manage infrastructure

### Layer 4: ⚡ HFT Executor (Myśliwiec)
**Location**: `src/`
**Technology**: Rust, Solana SDK, Jito bundles
**Responsibility**:
- High-frequency trade execution
- Order management
- Risk controls and position limits
- Performance optimization

**Service Boundaries**:
- ✅ Executes trades with sub-50ms latency
- ✅ Manages positions and orders
- ✅ Enforces risk limits
- ✅ Optimizes execution strategies
- ❌ Does NOT generate trading signals
- ❌ Does NOT perform market analysis

### Layer 5: 🎛️ Control Center (Centrum Kontroli)
**Location**: `mission_control/`
**Technology**: Streamlit, Python
**Responsibility**:
- User interface and dashboard
- Goal management and configuration
- System monitoring and control
- Manual overrides and emergency stops

**Service Boundaries**:
- ✅ Provides user interface
- ✅ Manages trading goals
- ✅ Displays system status
- ✅ Enables manual control
- ❌ Does NOT execute trades
- ❌ Does NOT store critical data

## 🔗 Inter-Service Communication

### Communication Patterns

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Layer 2   │───▶│   Layer 3   │───▶│   Layer 4   │
│ Data Ingest │    │  AI Brain   │    │ HFT Executor│
└─────────────┘    └─────────────┘    └─────────────┘
       │                  ▲                  ▲
       │                  │                  │
       ▼                  │                  │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Layer 1   │    │   Layer 5   │────┘   Layer 4   │
│Infrastructure│    │Control Center│    │ HFT Executor│
└─────────────┘    └─────────────┘    └─────────────┘
```

### Communication Protocols

| From | To | Protocol | Purpose |
|------|----|---------|---------| 
| Data Ingest | AI Brain | DragonflyDB | Market data streaming |
| AI Brain | HFT Executor | DragonflyDB | Trading signals |
| Control Center | AI Brain | HTTP/REST | Goal management |
| Control Center | HFT Executor | HTTP/REST | Status monitoring |
| All Services | Infrastructure | Prometheus | Metrics collection |

## 📦 Dependency Management

### Python Services (Brain, Mission Control)
- **Standard**: `pyproject.toml` with `uv` package manager
- **Benefits**: Fast installs, deterministic builds, modern tooling
- **Location**: Each service has its own `pyproject.toml`

### Rust Services (HFT Executor, Data Ingest)
- **Standard**: `Cargo.toml` with cargo
- **Benefits**: Native Rust tooling, excellent performance
- **Location**: Root `Cargo.toml` with workspace configuration

### Global Coordination
- **Standard**: `pixi.toml` for cross-language coordination
- **Benefits**: Unified environment management
- **Location**: Root level for project-wide coordination

## 🛡️ Security Boundaries

### Secrets Management
- **API Keys**: Environment variables only
- **Wallets**: Separate `wallets/` directory with restricted access
- **Database**: Connection strings in environment variables
- **Never**: Hardcode secrets in source code

### Network Security
- **Internal**: Services communicate via private Docker network
- **External**: Only necessary ports exposed to host
- **Encryption**: TLS for all external communications
- **Isolation**: Each service runs in separate container

## 🧪 Testing Boundaries

### Unit Tests
- **Brain**: `brain/tests/` - AI logic and data processing
- **Executor**: `tests/` - Trading logic and risk management
- **Mission Control**: `mission_control/tests/` - UI components

### Integration Tests
- **Cross-Service**: `tests/integration_tests.rs`
- **End-to-End**: `tests/end_to_end_tests.rs`
- **Performance**: `benches/` - Latency and throughput

### Test Data
- **Mock Services**: `tests/mock_*` - Simulated external services
- **Test Wallets**: `wallets/devnet-*` - Safe test credentials
- **Sample Data**: `tests/fixtures/` - Consistent test datasets

## 📊 Monitoring Boundaries

### Service-Level Metrics
- **Health Checks**: Each service exposes `/health` endpoint
- **Performance**: Latency, throughput, error rates
- **Business**: Trading metrics, P&L, positions

### System-Level Metrics
- **Infrastructure**: CPU, memory, network, disk
- **Dependencies**: Database connections, API rate limits
- **Security**: Failed authentication, unusual patterns

## 🚨 Error Handling Boundaries

### Service Isolation
- **Principle**: One service failure should not cascade
- **Implementation**: Circuit breakers, timeouts, retries
- **Recovery**: Graceful degradation and automatic restart

### Error Propagation
- **Internal**: Detailed error information for debugging
- **External**: Sanitized error messages for security
- **Logging**: Structured logs with correlation IDs

## ✅ Compliance Checklist

### Service Design
- [ ] Single responsibility principle
- [ ] Clear input/output contracts
- [ ] Proper error handling
- [ ] Health check endpoints
- [ ] Metrics collection

### Communication
- [ ] Async messaging where possible
- [ ] Timeout and retry logic
- [ ] Circuit breaker patterns
- [ ] Proper authentication

### Data Management
- [ ] No shared databases between services
- [ ] Event sourcing for audit trails
- [ ] Data validation at boundaries
- [ ] Proper backup strategies

### Security
- [ ] Principle of least privilege
- [ ] Input validation and sanitization
- [ ] Secure secret management
- [ ] Regular security audits

---

## 🎯 Benefits of Clear Service Boundaries

1. **Maintainability**: Easy to understand and modify individual services
2. **Scalability**: Services can be scaled independently
3. **Reliability**: Failures are isolated and don't cascade
4. **Testability**: Each service can be tested in isolation
5. **Deployability**: Services can be deployed independently
6. **Team Productivity**: Clear ownership and responsibilities

**🏆 Result**: A robust, maintainable, and scalable trading system that can evolve with changing requirements while maintaining high performance and reliability.**
