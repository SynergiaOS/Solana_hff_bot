# 🎯 RULES FOR AUGMENT AGENT - THE OVERMIND PROTOCOL

## 📋 **OVERVIEW**

Te zasady definiują jak Augment Agent ma pracować z THE OVERMIND PROTOCOL - systematycznie, bezpiecznie i efektywnie.

**Motto:** "Czytaj → Planuj → Testuj → Implementuj → Weryfikuj"
**Status:** PRODUCTION RULES
**Use Case:** Systematic Development of THE OVERMIND PROTOCOL

## 🎯 **GOLDEN RULE: "Captain and Co-Pilot"**

### **YOU (Operator/Captain):**
- Odpowiedzialny za strategię, architekturę, weryfikację i finalne decyzje
- Znasz kontekst biznesowy i cele THE OVERMIND PROTOCOL
- **ZAWSZE weryfikuj kod Augmenta, szczególnie w krytycznych modułach (executor, risk)**

### **AUGMENT (Co-Pilot):**
- Odpowiedzialny za precyzyjne wykonanie zadań technicznych
- Ekspert techniczny ale nie zna Twoich intencji
- **Nigdy nie podejmuje decyzji bez Twojej akceptacji**

**Rule:** Nigdy ślepo nie akceptuj sugestii Augmenta. TY jesteś dowódcą.

## 📚 **MANDATORY INFORMATION GATHERING**

### **PRZED KAŻDYM ZADANIEM:**

#### **1. Przeczytaj Dokumentację:**
```bash
# ZAWSZE zacznij od przeczytania odpowiedniej dokumentacji
cat library/README.md                    # Przegląd bibliotek
cat library/ai/overmind-protocol.md      # Główna architektura
cat library/solana/solana-sdk.md         # Solana integration
cat library/rust/tokio-async.md          # Async patterns
cat library/trading/nautilus-trader.md   # Trading patterns
```

#### **2. Sprawdź Memory:**
```bash
# Sprawdź co system już wie
- THE OVERMIND PROTOCOL architecture
- Existing codebase structure
- Previous decisions and patterns
- Known issues and solutions
```

#### **3. Pobierz Aktualne Informacje:**
```bash
# Jeśli potrzebujesz świeżych informacji
- Web search dla najnowszych rozwiązań
- GitHub API dla aktualnego stanu repo
- Library documentation dla specific patterns
```

## 🔄 **SYSTEMATIC WORKFLOW**

### **FAZA 1: INFORMATION GATHERING (Obowiązkowa)**
```
1. 📚 READ documentation relevant to task
2. 🧠 CHECK memory for existing patterns
3. 🌐 SEARCH web for latest solutions (if needed)
4. 📊 ANALYZE current codebase state
5. ✅ CONFIRM understanding with user
```

### **FAZA 2: PLANNING (Szczegółowy Plan)**
```
1. 🎯 DEFINE precise task breakdown
2. 📝 LIST all files that need changes
3. 🔍 IDENTIFY dependencies and risks
4. 📋 CREATE step-by-step action plan
5. ✅ GET user approval for plan
```

### **FAZA 3: IMPLEMENTATION (Rozdział po Rozdziale)**
```
1. 🔧 IMPLEMENT one module at a time
2. 🧪 WRITE tests for each module
3. ✅ RUN tests and verify functionality
4. 📊 SHOW results to user
5. 🔄 GET approval before next module
```

### **FAZA 4: VERIFICATION (Comprehensive Testing)**
```
1. 🧪 RUN all existing tests
2. 🔍 CHECK integration points
3. 📊 VERIFY performance metrics
4. 🛡️ SECURITY review (if applicable)
5. ✅ FINAL user approval
```

## 🧪 **TESTING METHODOLOGY**

### **Test-Driven Development:**
```rust
// ZAWSZE zacznij od testów
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_overmind_component() {
        // 1. Arrange - setup test data
        // 2. Act - execute function
        // 3. Assert - verify results
    }
}
```

### **Testing Hierarchy:**
1. **Unit Tests** - Individual functions
2. **Integration Tests** - Module interactions
3. **System Tests** - End-to-end workflows
4. **Performance Tests** - Latency and throughput
5. **Security Tests** - Risk management

### **Testing Commands:**
```bash
# Run tests systematically
cargo test --lib                    # Unit tests
cargo test --test integration       # Integration tests
cargo test --workspace             # All tests
cargo bench                        # Performance tests
```

## 📊 **STRUCTURED TASK EXECUTION**

### **Template for Every Task:**

#### **STEP 1: Information Gathering**
```
📚 DOCUMENTATION READ:
- [ ] Relevant library/*.md files
- [ ] Existing code patterns
- [ ] Architecture decisions

🧠 MEMORY CHECK:
- [ ] Previous implementations
- [ ] Known patterns
- [ ] User preferences

🌐 RESEARCH (if needed):
- [ ] Latest solutions
- [ ] Best practices
- [ ] Security considerations
```

#### **STEP 2: Planning**
```
🎯 TASK BREAKDOWN:
1. [ ] Specific goal definition
2. [ ] File-by-file change list
3. [ ] Dependency analysis
4. [ ] Risk assessment

📋 IMPLEMENTATION PLAN:
1. [ ] Module A: [specific changes]
2. [ ] Module B: [specific changes]
3. [ ] Tests: [test strategy]
4. [ ] Integration: [integration points]
```

#### **STEP 3: Implementation**
```
🔧 DEVELOPMENT:
- [ ] Implement Module A
- [ ] Write tests for Module A
- [ ] Verify Module A works
- [ ] Get user approval
- [ ] Proceed to Module B

🧪 TESTING:
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Performance acceptable
- [ ] No regressions
```

#### **STEP 4: Verification**
```
✅ FINAL CHECKS:
- [ ] All tests pass
- [ ] Code follows patterns
- [ ] Documentation updated
- [ ] User approval received
```

## 🎯 **Core Principles

### **1. Safety First (THE OVERMIND PROTOCOL)**
- **Default Paper Trading**: All trading functionality MUST default to paper trading mode
- **Explicit Live Mode**: Live trading requires explicit `SNIPER_TRADING_MODE=live` environment variable
- **AI Safety**: AI decisions must be validated before execution
- **Risk Limits**: All operations must respect configured risk parameters
- **Input Validation**: Every external input must be validated and sanitized

### **2. Performance Critical (Ultra-HFT)**
- **Sub-25ms Latency**: Target sub-25ms execution with TensorZero optimization
- **Zero-Copy Operations**: Minimize memory allocations in hot paths
- **Async-First**: All I/O operations must be asynchronous
- **Channel Communication**: Use Tokio MPSC channels for inter-module communication
- **Memory Efficiency**: Target <8GB RAM usage under normal load
- **AI Optimization**: Use TensorZero for LLM optimization

### **3. Reliability (5-Layer Architecture)**
- **Error Handling**: All operations return `Result<T, E>` with proper error propagation
- **Graceful Degradation**: System continues operating when non-critical components fail
- **Circuit Breakers**: Automatic halt on anomalous conditions
- **Comprehensive Logging**: All decisions and actions must be logged
- **AI Memory**: Vector database for long-term learning and context

## 🏗️ **THE OVERMIND PROTOCOL Architecture Rules**

### **5-Layer Architecture:**
```
THE OVERMIND PROTOCOL:
├── Warstwa 1: Forteca (Infrastructure)
│   ├── Docker & Docker Compose
│   ├── DragonflyDB (Redis-compatible)
│   └── Kestra (Orchestration)
├── Warstwa 2: Zmysły (Intelligence)
│   ├── Jito-Solana Node (Local)
│   ├── Shredstream Proxy
│   └── MonkeyOCR (Document AI)
├── Warstwa 3: Mózg AI (Strategic Brain)
│   ├── ai-hedge-fund Framework
│   ├── Vector Database (Chroma)
│   └── LLM Engine (OpenAI/Groq)
├── Warstwa 4: Myśliwiec (Executor)
│   ├── TensorZero Gateway
│   ├── Solana_hff_bot (Rust)
│   └── Jito Bundle Execution
└── Warstwa 5: Centrum Kontroli
    ├── Kestra Workflows
    ├── Prometheus Monitoring
    └── Grafana Dashboards
```

### **Rust Module Structure (Warstwa 4):**
```
src/
├── main.rs              # OVERMIND entry point
├── config.rs            # Configuration management
└── modules/
    ├── mod.rs           # Module declarations
    ├── data_ingestor.rs # Market data ingestion
    ├── strategy.rs      # AI-enhanced trading strategies
    ├── risk.rs          # Risk management
    ├── executor.rs      # TensorZero-optimized execution
    ├── persistence.rs   # Data persistence
    └── ai_connector.rs  # AI Brain connector
```

### **Communication Channels:**
- `ai_brain_channel`: AI Brain → Strategy
- `market_data_channel`: DataIngestor → Strategy
- `signal_channel`: Strategy → Risk
- `execution_channel`: Risk → Executor
- `persistence_channel`: All → Persistence
- `vector_memory_channel`: All → Vector Database

### Dependencies (Cargo.toml)
```toml
[dependencies]
# Core async runtime
tokio = { version = "1.35", features = ["full"] }

# Solana blockchain
solana-sdk = "1.18"
solana-client = "1.18"

# Web framework
axum = "0.7"

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Error handling
anyhow = "1.0"
thiserror = "1.0"

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

# Database
sqlx = { version = "0.7", features = ["runtime-tokio-rustls", "postgres", "chrono", "uuid"] }

# HTTP client
reqwest = { version = "0.11", features = ["json"] }

# WebSocket
tokio-tungstenite = "0.21"

# Time
chrono = { version = "0.4", features = ["serde"] }

# UUID
uuid = { version = "1.0", features = ["v4", "serde"] }

# Environment
dotenvy = "0.15"

[profile.release]
lto = true
codegen-units = 1
panic = "abort"

[profile.contabo]
inherits = "release"
opt-level = 3
target-cpu = "native"
```

## 🔒 Security Rules

### Secret Management
- **Environment Variables**: All secrets via environment variables with `SNIPER_` prefix
- **No Hardcoding**: Never hardcode API keys, private keys, or passwords
- **Validation**: Validate all secrets at startup

### Required Environment Variables
```bash
# Trading Configuration
SNIPER_TRADING_MODE=paper          # paper|live
SNIPER_MAX_POSITION_SIZE=1000      # USD
SNIPER_MAX_DAILY_LOSS=500          # USD

# Solana Configuration
SNIPER_SOLANA_RPC_URL=             # Required
SNIPER_WALLET_PRIVATE_KEY=         # Required for live trading

# API Keys
SNIPER_HELIUS_API_KEY=             # Required
SNIPER_QUICKNODE_API_KEY=          # Required

# Database
SNIPER_DATABASE_URL=               # PostgreSQL connection string

# Server
SNIPER_SERVER_PORT=8080            # API server port
```

### Input Validation
- **Sanitize All Inputs**: Use proper parsing and validation
- **Range Checks**: Validate numeric ranges
- **Type Safety**: Leverage Rust's type system for validation

## 📊 Performance Rules

### Latency Targets
- **Order Processing**: <50ms end-to-end
- **Market Data**: <10ms ingestion to strategy
- **Risk Check**: <5ms per signal
- **Execution**: <20ms signal to blockchain

### Memory Management
- **Bounded Channels**: Use bounded channels to prevent memory leaks
- **Resource Cleanup**: Implement proper Drop traits
- **Memory Monitoring**: Track memory usage in production

### Optimization Profiles
- **Development**: Fast compilation, debug symbols
- **Release**: Standard optimizations
- **Contabo**: Optimized for 6 vCPU, 24GB RAM VDS

## 🧪 Testing Rules

### Test Coverage
- **Unit Tests**: Every public function must have unit tests
- **Integration Tests**: Test module interactions
- **Performance Tests**: Benchmark critical paths
- **Paper Trading Tests**: Validate all strategies in simulation

### Test Structure
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_function_name() {
        // Arrange
        // Act
        // Assert
    }
}
```

## 📝 Logging Rules

### Log Levels
- **ERROR**: System failures, trading halts
- **WARN**: Risk limit breaches, degraded performance
- **INFO**: Trading decisions, system state changes
- **DEBUG**: Detailed execution flow
- **TRACE**: Performance metrics, raw data

### Log Format
```rust
use tracing::{info, warn, error, debug, trace};

// Include correlation IDs
info!(
    correlation_id = %correlation_id,
    symbol = %symbol,
    action = %action,
    "Trade signal generated"
);
```

### Structured Logging
- **JSON Format**: Use structured JSON logging in production
- **Correlation IDs**: Track requests across modules
- **Performance Metrics**: Log execution times for critical operations

## 🚀 Deployment Rules

### Build Process
```bash
# Development
cargo build

# Production (Contabo optimized)
cargo build --profile contabo

# Docker
docker build -t snipercor:latest .
```

### Runtime Configuration
- **Resource Limits**: Configure appropriate CPU and memory limits
- **Health Checks**: Implement comprehensive health endpoints
- **Graceful Shutdown**: Handle SIGTERM for clean shutdown

## 🔧 Code Style Rules

### Rust Conventions
- **snake_case**: Functions, variables, modules
- **PascalCase**: Types, structs, enums
- **SCREAMING_SNAKE_CASE**: Constants
- **Documentation**: All public items must have doc comments

### Error Handling
```rust
use anyhow::{Result, Context};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum TradingError {
    #[error("Invalid signal: {0}")]
    InvalidSignal(String),
    #[error("Risk limit exceeded")]
    RiskLimitExceeded,
}

pub async fn process_signal(signal: Signal) -> Result<()> {
    validate_signal(&signal)
        .context("Failed to validate trading signal")?;
    Ok(())
}
```

### Async Patterns
```rust
// Prefer async/await over manual Future implementation
pub async fn fetch_market_data() -> Result<MarketData> {
    let response = reqwest::get("https://api.example.com/data").await?;
    let data = response.json().await?;
    Ok(data)
}
```

## ⚠️ Critical Safety Rules

### Trading Safety
1. **Paper Trading Default**: System MUST start in paper trading mode
2. **Live Trading Confirmation**: Require explicit confirmation for live trading
3. **Emergency Stop**: Implement immediate trading halt capability
4. **Position Limits**: Enforce maximum position sizes
5. **Loss Limits**: Implement daily and total loss limits

### System Safety
1. **Graceful Degradation**: Continue operating with reduced functionality
2. **Circuit Breakers**: Automatic halt on anomalous conditions
3. **Resource Monitoring**: Monitor CPU, memory, and network usage
4. **Backup Systems**: Implement fallback mechanisms for critical components

---

## 🛡️ **SAFETY PROTOCOLS**

### **Critical Modules (Extra Caution):**
- `src/modules/executor.rs` - Trading execution
- `src/modules/risk.rs` - Risk management
- `src/modules/strategy.rs` - Trading strategies
- `src/modules/ai_connector.rs` - AI Brain integration
- `Cargo.toml` - Dependencies
- `docker-compose.yml` - Infrastructure

### **Never Do Without Permission:**
- Commit or push code
- Change dependency versions
- Modify risk parameters
- Deploy to production
- Delete files or data
- Modify AI model parameters

### **Always Ask Before:**
- Major architectural changes
- New dependency additions
- Security-related modifications
- Performance optimizations that change behavior
- AI model integration changes

## 📝 **COMMUNICATION PROTOCOL**

### **Progress Updates:**
```
🎯 TASK: [Brief description]
📚 RESEARCH: [What was read/researched]
📋 PLAN: [Step-by-step plan]
🔧 PROGRESS: [Current step]
🧪 TESTS: [Test results]
❓ QUESTION: [If clarification needed]
```

### **Code Presentation:**
```
<augment_code_snippet path="src/modules/example.rs" mode="EXCERPT">
````rust
// Show only relevant code snippets
// Keep under 10 lines when possible
````
</augment_code_snippet>
```

### **Decision Points:**
```
🤔 DECISION NEEDED:
Option A: [Description + pros/cons]
Option B: [Description + pros/cons]
Recommendation: [Your preference with reasoning]
```

## 🎯 **THE OVERMIND PROTOCOL SPECIFIC RULES**

### **Architecture Compliance:**
- **Warstwa 1:** Infrastructure (Docker, DragonflyDB, Kestra)
- **Warstwa 2:** Intelligence (Geyser, ShredStream, MonkeyOCR)
- **Warstwa 3:** AI Brain (ai-hedge-fund, Vector DB, LLM)
- **Warstwa 4:** Executor (Rust, TensorZero, Solana SDK)
- **Warstwa 5:** Control (Monitoring, Management)

### **Integration Requirements:**
- ai-hedge-fund framework for Python brain
- TensorZero for LLM optimization
- Vector database for long-term memory
- DragonflyDB for real-time communication
- Jito-Solana for ultra-low latency

### **Performance Standards:**
- Sub-25ms execution latency
- 99.9% uptime requirement
- Real-time data processing
- Fault-tolerant design
- Scalable architecture

## 🔄 **ITERATIVE DEVELOPMENT**

### **Chapter-by-Chapter Approach:**
```
Chapter 1: Core Infrastructure
├── Setup basic modules
├── Write foundational tests
├── Verify basic functionality
└── User approval ✅

Chapter 2: Data Integration
├── Implement data ingestion
├── Add data processing tests
├── Verify data flow
└── User approval ✅

Chapter 3: AI Integration
├── Connect ai-hedge-fund
├── Implement vector memory
├── Test AI decision making
└── User approval ✅

[Continue systematically...]
```

### **Rollback Strategy:**
- Always work on feature branches
- Commit working states frequently
- Keep previous version available
- Document all changes made

## 📊 **SUCCESS METRICS**

### **Quality Gates:**
- [ ] All tests pass (100%)
- [ ] Code coverage > 80%
- [ ] Performance benchmarks met
- [ ] Security review passed
- [ ] User acceptance received

### **Documentation Requirements:**
- [ ] Code comments for complex logic
- [ ] README updates for new features
- [ ] Architecture decisions recorded
- [ ] API documentation current

## 🎯 **FINAL CHECKLIST**

### **Before Marking Task Complete:**
- [ ] Information gathering completed
- [ ] Detailed plan approved
- [ ] Implementation tested thoroughly
- [ ] All tests passing
- [ ] Performance verified
- [ ] Security reviewed
- [ ] Documentation updated
- [ ] User final approval received

---

**🎯 REMEMBER: Read → Plan → Test → Implement → Verify**
**🧠 ALWAYS start with documentation and memory**
**🤝 NEVER proceed without user approval at key decision points**
**🛡️ SAFETY FIRST in critical trading modules**

**Status:** ✅ **PRODUCTION READY** - Rules for THE OVERMIND PROTOCOL Development

**🛡️ These rules are non-negotiable. Violations may result in financial loss or system failure.**
