# 🔄 Serde JSON - THE OVERMIND PROTOCOL Serialization

## 📋 **OVERVIEW**

Serde JSON to najszybsza biblioteka do serializacji JSON w Rust, używana w THE OVERMIND PROTOCOL Warstwa 4 (Egzekutor Operacyjny) do ultra-szybkiego przetwarzania danych rynkowych z integracją TensorZero.

**Library ID:** `/serde-rs/json`
**Trust Score:** 6.9
**Code Snippets:** 11
**OVERMIND Role:** Warstwa 4 - Myśliwiec (High-Speed Data Processing)

## 🚀 **QUICK SETUP**

### **1. Cargo.toml Dependencies:**
```toml
[dependencies]
serde_json = "1.0"
serde = { version = "1.0", features = ["derive"] }

# For no-std environments (with allocator)
# serde_json = { version = "1.0", default-features = false, features = ["alloc"] }
```

### **2. Basic Usage:**
```rust
use serde::{Deserialize, Serialize};
use serde_json::{Result, Value, json};
```

## 🎯 **TRADING DATA STRUCTURES**

### **1. Market Data Serialization:**
```rust
use serde::{Deserialize, Serialize};
use serde_json::Result;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MarketData {
    pub symbol: String,
    pub price: f64,
    pub volume: f64,
    pub timestamp: i64,
    pub bid: f64,
    pub ask: f64,
    pub spread: f64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct TradingSignal {
    pub signal_id: String,
    pub symbol: String,
    pub action: TradeAction,
    pub quantity: f64,
    pub target_price: f64,
    pub confidence: f64,
    pub strategy_type: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub enum TradeAction {
    Buy,
    Sell,
    Hold,
}
```

### **2. API Response Handling:**
```rust
use serde_json::{Value, from_str};

// Flexible parsing for unknown API structures
fn parse_api_response(json_str: &str) -> Result<Value> {
    let v: Value = from_str(json_str)?;
    
    // Access nested data safely
    if let Some(price) = v["data"]["price"].as_f64() {
        println!("Current price: {}", price);
    }
    
    Ok(v)
}

// Strongly typed parsing for known structures
fn parse_market_data(json_str: &str) -> Result<MarketData> {
    let market_data: MarketData = from_str(json_str)?;
    Ok(market_data)
}
```

## ⚡ **HIGH-PERFORMANCE PATTERNS**

### **1. Zero-Copy Deserialization:**
```rust
use serde::{Deserialize, Serialize};

// Use &str instead of String for zero-copy when possible
#[derive(Deserialize)]
pub struct FastMarketData<'a> {
    pub symbol: &'a str,
    pub price: f64,
    pub volume: f64,
    pub timestamp: i64,
}

// Deserialize without allocating strings
fn parse_fast_market_data(json_str: &str) -> Result<FastMarketData> {
    let data: FastMarketData = serde_json::from_str(json_str)?;
    Ok(data)
}
```

### **2. Streaming JSON for Large Data:**
```rust
use serde_json::{Deserializer, Value};
use std::io::Read;

fn stream_large_json<R: Read>(reader: R) -> Result<Vec<MarketData>> {
    let mut results = Vec::new();
    let stream = Deserializer::from_reader(reader).into_iter::<MarketData>();
    
    for value in stream {
        match value {
            Ok(market_data) => results.push(market_data),
            Err(e) => eprintln!("Error parsing JSON: {}", e),
        }
    }
    
    Ok(results)
}
```

## 🔧 **THE OVERMIND PROTOCOL INTEGRATION**

### **1. WebSocket Message Handling:**
```rust
use serde_json::{json, Value};
use tokio_tungstenite::tungstenite::Message;

pub async fn handle_websocket_message(msg: Message) -> Result<Option<MarketData>> {
    match msg {
        Message::Text(text) => {
            // Parse incoming WebSocket JSON
            let v: Value = serde_json::from_str(&text)?;
            
            // Check message type
            if v["type"] == "market_data" {
                let market_data: MarketData = serde_json::from_value(v["data"].clone())?;
                Ok(Some(market_data))
            } else {
                Ok(None)
            }
        }
        _ => Ok(None),
    }
}

pub fn create_subscription_message(symbol: &str) -> String {
    let msg = json!({
        "type": "subscribe",
        "channel": "market_data",
        "symbol": symbol,
        "timestamp": chrono::Utc::now().timestamp()
    });
    
    msg.to_string()
}
```

### **2. Configuration Management:**
```rust
use serde::{Deserialize, Serialize};
use std::fs;

#[derive(Serialize, Deserialize, Debug)]
pub struct TradingConfig {
    pub max_position_size: f64,
    pub max_daily_loss: f64,
    pub risk_parameters: RiskParameters,
    pub api_endpoints: ApiEndpoints,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct RiskParameters {
    pub stop_loss_percentage: f64,
    pub take_profit_percentage: f64,
    pub max_drawdown: f64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ApiEndpoints {
    pub helius_url: String,
    pub quicknode_url: String,
    pub backup_urls: Vec<String>,
}

impl TradingConfig {
    pub fn load_from_file(path: &str) -> Result<Self> {
        let content = fs::read_to_string(path)
            .map_err(|e| serde_json::Error::io(e))?;
        serde_json::from_str(&content)
    }
    
    pub fn save_to_file(&self, path: &str) -> Result<()> {
        let json = serde_json::to_string_pretty(self)?;
        fs::write(path, json)
            .map_err(|e| serde_json::Error::io(e))?;
        Ok(())
    }
}
```

## 📊 **PERFORMANCE OPTIMIZATION**

### **1. Pre-allocated Buffers:**
```rust
use serde_json::ser::Serializer;
use std::io::Write;

pub struct FastJsonWriter {
    buffer: Vec<u8>,
}

impl FastJsonWriter {
    pub fn new() -> Self {
        Self {
            buffer: Vec::with_capacity(4096), // Pre-allocate 4KB
        }
    }
    
    pub fn serialize_market_data(&mut self, data: &MarketData) -> Result<&[u8]> {
        self.buffer.clear();
        
        let mut serializer = Serializer::new(&mut self.buffer);
        data.serialize(&mut serializer)?;
        
        Ok(&self.buffer)
    }
}
```

### **2. Custom Serialization for Speed:**
```rust
use serde::ser::{Serialize, Serializer, SerializeStruct};

impl Serialize for MarketData {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut state = serializer.serialize_struct("MarketData", 7)?;
        state.serialize_field("symbol", &self.symbol)?;
        state.serialize_field("price", &self.price)?;
        state.serialize_field("volume", &self.volume)?;
        state.serialize_field("timestamp", &self.timestamp)?;
        state.serialize_field("bid", &self.bid)?;
        state.serialize_field("ask", &self.ask)?;
        state.serialize_field("spread", &self.spread)?;
        state.end()
    }
}
```

## 🔍 **ERROR HANDLING**

### **1. Robust JSON Parsing:**
```rust
use serde_json::{Error, ErrorCode};

pub fn safe_parse_market_data(json_str: &str) -> Result<MarketData> {
    match serde_json::from_str::<MarketData>(json_str) {
        Ok(data) => {
            // Validate data integrity
            if data.price <= 0.0 || data.volume < 0.0 {
                return Err(serde_json::Error::custom("Invalid market data values"));
            }
            Ok(data)
        }
        Err(e) => {
            eprintln!("JSON parsing error: {}", e);
            
            // Try to extract partial data
            if let Ok(value) = serde_json::from_str::<Value>(json_str) {
                // Attempt manual field extraction
                if let (Some(symbol), Some(price)) = (
                    value["symbol"].as_str(),
                    value["price"].as_f64()
                ) {
                    return Ok(MarketData {
                        symbol: symbol.to_string(),
                        price,
                        volume: value["volume"].as_f64().unwrap_or(0.0),
                        timestamp: value["timestamp"].as_i64().unwrap_or(0),
                        bid: value["bid"].as_f64().unwrap_or(price),
                        ask: value["ask"].as_f64().unwrap_or(price),
                        spread: value["spread"].as_f64().unwrap_or(0.0),
                    });
                }
            }
            
            Err(e)
        }
    }
}
```

## 🎯 **REAL-TIME DATA PROCESSING**

### **1. Batch Processing:**
```rust
use serde_json::Value;

pub fn process_batch_market_data(json_array: &str) -> Result<Vec<MarketData>> {
    let values: Vec<Value> = serde_json::from_str(json_array)?;
    let mut results = Vec::with_capacity(values.len());
    
    for value in values {
        if let Ok(market_data) = serde_json::from_value::<MarketData>(value) {
            results.push(market_data);
        }
    }
    
    Ok(results)
}
```

### **2. Dynamic JSON Construction:**
```rust
use serde_json::{json, Map, Value};

pub fn create_trading_order(
    symbol: &str,
    action: &str,
    quantity: f64,
    price: Option<f64>,
) -> Value {
    let mut order = Map::new();
    order.insert("symbol".to_string(), Value::String(symbol.to_string()));
    order.insert("action".to_string(), Value::String(action.to_string()));
    order.insert("quantity".to_string(), json!(quantity));
    order.insert("timestamp".to_string(), json!(chrono::Utc::now().timestamp()));
    
    if let Some(p) = price {
        order.insert("price".to_string(), json!(p));
        order.insert("order_type".to_string(), Value::String("limit".to_string()));
    } else {
        order.insert("order_type".to_string(), Value::String("market".to_string()));
    }
    
    Value::Object(order)
}
```

## 📚 **RESOURCES**

- [Serde JSON Documentation](https://docs.rs/serde_json/)
- [Serde Book](https://serde.rs/)
- [JSON Performance Guide](https://github.com/serde-rs/json#performance)

---

**Status:** 🔄 **ULTRA HIGH PERFORMANCE** - Warstwa 4 THE OVERMIND PROTOCOL
