# 14-Day Live Paper Trading Guide

## 🎯 Overview

This guide explains how to run the complete 14-day live paper trading validation for THE OVERMIND PROTOCOL. This is the final validation phase before considering live trading deployment.

## 🚀 Quick Start

### 1. Prerequisites

Ensure your environment is properly configured:

```bash
# Check .env configuration
cat .env | grep -E "(HELIUS_API_KEY|QUICKNODE_MAINNET_RPC_URL|ENABLED_STRATEGIES)"

# Verify SOL Momentum is enabled
grep "sol_momentum" .env
```

Required environment variables:
- `HELIUS_API_KEY` - Your Helius API key
- `QUICKNODE_MAINNET_RPC_URL` - Your QuickNode Mainnet endpoint
- `ENABLED_STRATEGIES` - Must include "sol_momentum"

### 2. Start 14-Day Trading Session

```bash
# Start the complete 14-day paper trading session
python scripts/start_14day_paper_trading.py
```

This will:
- Initialize the SOL Momentum strategy
- Start paper trading with $10,000 virtual balance
- Run continuously for 14 days
- Generate daily reports automatically
- Save all data for analysis

### 3. Monitor Progress

```bash
# List all trading sessions
python scripts/monitor_paper_trading.py

# View session summary
python scripts/monitor_paper_trading.py <session_id>

# View performance chart
python scripts/monitor_paper_trading.py <session_id> chart

# View detailed trading statistics
python scripts/monitor_paper_trading.py <session_id> stats
```

## 📊 What to Expect

### Trading Behavior

The system will:
- **Generate signals every 5 minutes** using SOL Momentum strategy
- **Execute trades** when confidence threshold is met (≥60%)
- **Apply risk management** with position sizing and stop-losses
- **Track performance** with comprehensive metrics

### Daily Reports

Each day at 23:59, the system generates:
- Portfolio value and P&L
- Number of trades executed
- Signal generation statistics
- Position details

### Data Storage

All data is saved in `brain/src/live_trading_data/`:
- `<session_id>.json` - Complete session data
- `<session_id>_day_X.json` - Individual daily reports
- `<session_id>_final_report.txt` - Final comprehensive report

## 🛡️ Risk Management

### Built-in Protections

- **Position Sizing**: Maximum 15% of portfolio per position
- **Stop-Loss**: Dynamic stop-loss based on volatility (2-10%)
- **Take-Profit**: 2:1 risk-reward ratio
- **Daily Loss Limit**: Maximum 5% daily loss
- **Confidence Filtering**: Only execute high-confidence signals

### Paper Trading Safety

- **No Real Money**: All trading is simulated
- **Real Price Data**: Uses live Helius API data
- **Realistic Execution**: Includes fees and slippage simulation

## 📈 Performance Metrics

### Key Metrics Tracked

1. **Return Metrics**
   - Total return (absolute and percentage)
   - Daily returns
   - Annualized return

2. **Risk Metrics**
   - Maximum drawdown
   - Volatility (daily and annualized)
   - Sharpe ratio
   - Value at Risk (VaR)

3. **Trading Metrics**
   - Total trades executed
   - Win rate
   - Average trade duration
   - Signal execution rate

4. **Consistency Metrics**
   - Daily win rate
   - Consecutive wins/losses
   - Recovery factor

## 🔧 Troubleshooting

### Common Issues

1. **"Helius API key not configured"**
   ```bash
   # Add to .env file
   echo "HELIUS_API_KEY=your_api_key_here" >> .env
   ```

2. **"SOL Momentum strategy not enabled"**
   ```bash
   # Update ENABLED_STRATEGIES in .env
   ENABLED_STRATEGIES=soul_meteor,meteora_damm_v2,developer_tracking,memecoin_hunter,sol_momentum
   ```

3. **"No signals generated"**
   - This is normal during stable market conditions
   - The strategy waits for clear momentum signals
   - Lower confidence threshold in strategy parameters if needed

4. **Session interrupted**
   ```bash
   # Check for existing session data
   python scripts/monitor_paper_trading.py
   
   # Resume monitoring existing session
   python scripts/monitor_paper_trading.py <session_id>
   ```

### Logs and Debugging

- **Live trading logs**: `live_trading.log`
- **Session data**: `brain/src/live_trading_data/`
- **Debug mode**: Set `logging.DEBUG` in script

## 📋 Success Criteria

### Minimum Performance Targets

For successful validation, the strategy should achieve:

1. **Positive Returns**: Total return > 0% over 14 days
2. **Risk Management**: Maximum drawdown < 15%
3. **Consistency**: Win rate > 45%
4. **Activity**: At least 10 completed trades
5. **Sharpe Ratio**: > 0.5 (risk-adjusted returns)

### Benchmark Comparison

The strategy will be compared against:
- **Buy-and-Hold SOL**: Simple SOL holding strategy
- **Crypto Market Index**: Diversified crypto portfolio
- **Risk-Free Rate**: 2% annual return

## 🎯 Next Steps

### After 14-Day Completion

1. **Review Final Report**
   - Analyze comprehensive performance metrics
   - Compare against benchmarks
   - Identify areas for improvement

2. **Strategy Optimization**
   - Use optimization results to fine-tune parameters
   - Consider additional risk management rules
   - Evaluate different confidence thresholds

3. **Live Trading Decision**
   - If performance meets criteria, consider live deployment
   - Start with small position sizes
   - Maintain strict risk management

### Continuous Improvement

- **Parameter Optimization**: Regular backtesting with new data
- **Strategy Enhancement**: Add new indicators or filters
- **Risk Management**: Adjust limits based on performance
- **Market Adaptation**: Monitor changing market conditions

## 🚨 Important Notes

### Before Live Trading

- **Never trade with money you can't afford to lose**
- **Start with small amounts** (< 1% of total capital)
- **Monitor performance closely** for first few weeks
- **Have exit strategy** if performance deteriorates

### Regulatory Considerations

- **Check local regulations** for automated trading
- **Understand tax implications** of trading activities
- **Consider professional advice** for large amounts
- **Maintain detailed records** for compliance

## 📞 Support

If you encounter issues:

1. **Check logs**: Review `live_trading.log` for errors
2. **Verify configuration**: Ensure all environment variables are set
3. **Monitor resources**: Check system CPU/memory usage
4. **Review documentation**: Check strategy and risk management docs

---

**Remember**: This is paper trading for validation purposes. Real trading involves significant risks and should only be undertaken after thorough testing and with proper risk management.
