#!/bin/bash

# Final fix for remaining Rust compilation errors

echo "🔧 Final Rust compilation fixes..."

cd overmind-protocol/core

# Fix 1: Add StrategyType import to risk.rs
echo "Adding StrategyType import..."
sed -i '4i use crate::modules::strategy::StrategyType;' src/modules/risk.rs

# Fix 2: Fix AIMetrics Clone derive (find the correct line)
echo "Fixing AIMetrics Clone derive..."
sed -i 's/^pub struct AIMetrics {/#[derive(Debug, Clone)]\npub struct AIMetrics {/' src/modules/ai_connector.rs

# Fix 3: Add initialize_connection method
echo "Adding initialize_connection method..."
cat >> src/modules/ai_connector.rs << 'EOF'

    async fn initialize_connection(&mut self) -> Result<()> {
        info!("🔗 Initializing AI Connector connection...");
        // TODO: Add actual connection initialization logic
        Ok(())
    }
EOF

# Fix 4: Remove unused variables
echo "Fixing unused variables..."
sed -i 's/let mut conn = dragonfly_client.clone();/let _conn = dragonfly_client.clone();/' src/modules/ai_connector.rs
sed -i 's/let config = self.config.clone();/let _config = self.config.clone();/' src/modules/ai_connector.rs

# Test compilation
echo "🧪 Testing final compilation..."
if cargo check --quiet; then
    echo "✅ All Rust compilation errors fixed!"
    
    # Try to run tests
    echo "🧪 Running Rust tests..."
    if cargo test --quiet; then
        echo "✅ All Rust tests pass!"
    else
        echo "⚠️ Some tests failed, but compilation works"
    fi
else
    echo "❌ Still have compilation errors:"
    cargo check
fi

cd ../..
echo "🔧 Final Rust fixes completed"
