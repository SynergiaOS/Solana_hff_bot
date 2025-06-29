"""THE OVERMIND PROTOCOL - On-Chain Analysis Agent
Specialized agent for analyzing on-chain data, token distribution, and blockchain metrics.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import urllib.request

# Try to import MinionAgent, fall back to mock if not available
try:
    from minion_agent import AgentConfig, MinionAgent
except ImportError:
    from ..mock_minion_agent import AgentConfig, MinionAgent
import urllib.parse
import urllib.error

logger = logging.getLogger(__name__)

class OnChainAnalysisAgent:
    """Specialized agent for on-chain analysis using MinionAgent framework."""
    
    def __init__(self):
        """Initialize the OnChainAnalysisAgent with proper configuration."""
        self.config = AgentConfig(
            name="onchain_analysis_agent",
            description="Agent specialized in analyzing on-chain data including token distribution, holder analysis, transaction patterns, and blockchain metrics for Solana tokens",
            model_id="deepseek/deepseek-reasoner",
            agent_type="CodeAgent",
            tools=[
                "analyze_token_holders",
                "check_token_distribution",
                "analyze_transaction_patterns",
                "assess_liquidity_pools",
                "detect_whale_activity"
            ]
        )
        
        # Initialize the MinionAgent with our config
        self.agent = MinionAgent(self.config)
        
        # Register our tools with the agent
        self._register_tools()

    def _register_tools(self):
        """Register on-chain analysis tools with the MinionAgent."""
        self.agent.register_tool("analyze_token_holders", self._analyze_token_holders)
        self.agent.register_tool("check_token_distribution", self._check_token_distribution)
        self.agent.register_tool("analyze_transaction_patterns", self._analyze_transaction_patterns)
        self.agent.register_tool("assess_liquidity_pools", self._assess_liquidity_pools)
        self.agent.register_tool("detect_whale_activity", self._detect_whale_activity)

        # 🛡️ RUGPULL SCANNER - Poziom 1: Zero-jedynkowe testy dyskwalifikacyjne
        self.agent.register_tool("check_lp_burned", self._check_lp_burned)
        self.agent.register_tool("verify_mint_authority", self._verify_mint_authority)
        self.agent.register_tool("check_freeze_authority", self._check_freeze_authority)
        self.agent.register_tool("verify_ownership_renounced", self._verify_ownership_renounced)
        self.agent.register_tool("perform_rugpull_level1_scan", self._perform_rugpull_level1_scan)

        # 📊 RUGPULL SCANNER - Analiza Dystrybucji Holderów
        self.agent.register_tool("analyze_holder_concentration", self._analyze_holder_concentration)
        self.agent.register_tool("detect_whale_dumping_risk", self._detect_whale_dumping_risk)
        self.agent.register_tool("check_dex_exclusions", self._check_dex_exclusions)
        self.agent.register_tool("perform_holder_distribution_scan", self._perform_holder_distribution_scan)
    
    async def _analyze_token_holders(self, token_address: str, limit: int = 100) -> Dict[str, Any]:
        """Analyze token holder distribution and patterns.
        
        Args:
            token_address: Token mint address
            limit: Number of top holders to analyze
            
        Returns:
            Dict containing holder analysis results
        """
        logger.info(f"👥 Analyzing token holders for: {token_address}")
        
        # Note: This is a placeholder implementation
        # In production, integrate with Solana RPC, Helius, or other on-chain data providers
        
        # Simulated holder analysis results
        mock_result = {
            "token_address": token_address,
            "total_holders": 15420,
            "analyzed_holders": limit,
            "holder_distribution": {
                "top_10_percentage": 45.2,  # Top 10 holders own 45.2% of supply
                "top_50_percentage": 67.8,
                "top_100_percentage": 78.5
            },
            "holder_categories": {
                "whales": {"count": 8, "percentage": 32.1},
                "large_holders": {"count": 42, "percentage": 23.4},
                "medium_holders": {"count": 156, "percentage": 18.2},
                "small_holders": {"count": 15214, "percentage": 26.3}
            },
            "distribution_score": 0.72,  # 0-1 scale, higher = more distributed
            "concentration_risk": "medium",
            "potential_rug_indicators": [],
            "holder_growth_24h": 156,  # New holders in 24h
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Add potential rug pull indicators based on distribution
        if mock_result["holder_distribution"]["top_10_percentage"] > 80:
            mock_result["potential_rug_indicators"].append("Extreme holder concentration")
        
        if mock_result["holder_categories"]["whales"]["percentage"] > 50:
            mock_result["potential_rug_indicators"].append("Whale dominance detected")
        
        return mock_result
    
    async def _check_token_distribution(self, token_address: str) -> Dict[str, Any]:
        """Check token distribution and supply metrics.
        
        Args:
            token_address: Token mint address
            
        Returns:
            Dict containing distribution analysis
        """
        logger.info(f"📊 Checking token distribution for: {token_address}")
        
        # Simulated distribution data
        mock_result = {
            "token_address": token_address,
            "total_supply": 1000000000,  # 1B tokens
            "circulating_supply": 750000000,  # 750M tokens
            "supply_percentage_circulating": 75.0,
            "locked_tokens": {
                "amount": 150000000,
                "percentage": 15.0,
                "lock_duration": "12 months",
                "unlock_schedule": "linear"
            },
            "burned_tokens": {
                "amount": 100000000,
                "percentage": 10.0
            },
            "team_allocation": {
                "amount": 50000000,
                "percentage": 5.0,
                "vesting_period": "24 months"
            },
            "liquidity_allocation": {
                "amount": 200000000,
                "percentage": 20.0,
                "locked_duration": "6 months"
            },
            "distribution_fairness_score": 0.78,  # 0-1 scale
            "red_flags": [],
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Check for red flags
        if mock_result["team_allocation"]["percentage"] > 20:
            mock_result["red_flags"].append("High team allocation percentage")
        
        if mock_result["supply_percentage_circulating"] < 50:
            mock_result["red_flags"].append("Low circulating supply percentage")
        
        return mock_result
    
    async def _analyze_transaction_patterns(self, token_address: str, timeframe: str = "24h") -> Dict[str, Any]:
        """Analyze transaction patterns and trading behavior.
        
        Args:
            token_address: Token mint address
            timeframe: Analysis timeframe
            
        Returns:
            Dict containing transaction pattern analysis
        """
        logger.info(f"📈 Analyzing transaction patterns for {token_address} ({timeframe})")
        
        # Simulated transaction pattern analysis
        mock_result = {
            "token_address": token_address,
            "timeframe": timeframe,
            "transaction_metrics": {
                "total_transactions": 2456,
                "buy_transactions": 1523,
                "sell_transactions": 933,
                "buy_sell_ratio": 1.63,
                "average_transaction_size": 1250.0,
                "median_transaction_size": 450.0
            },
            "trading_patterns": {
                "bot_activity_percentage": 23.5,
                "whale_transaction_count": 12,
                "sandwich_attacks_detected": 3,
                "mev_activity_score": 0.34
            },
            "price_impact_analysis": {
                "average_price_impact": 0.023,  # 2.3%
                "largest_price_impact": 0.156,  # 15.6%
                "high_impact_transactions": 8
            },
            "liquidity_analysis": {
                "effective_spread": 0.012,  # 1.2%
                "market_depth_score": 0.67,
                "liquidity_concentration": "medium"
            },
            "anomalies_detected": [
                {
                    "type": "unusual_volume_spike",
                    "severity": "medium",
                    "description": "Volume spike 340% above average"
                }
            ],
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        return mock_result
    
    async def _assess_liquidity_pools(self, token_address: str) -> Dict[str, Any]:
        """Assess liquidity pools and DEX information.
        
        Args:
            token_address: Token mint address
            
        Returns:
            Dict containing liquidity pool analysis
        """
        logger.info(f"🏊 Assessing liquidity pools for: {token_address}")
        
        # Simulated liquidity pool analysis
        mock_result = {
            "token_address": token_address,
            "pools": [
                {
                    "dex": "Raydium",
                    "pair": f"{token_address}/SOL",
                    "liquidity_usd": 250000,
                    "volume_24h": 180000,
                    "apr": 0.45,
                    "fee_tier": 0.0025,
                    "pool_age_days": 15
                },
                {
                    "dex": "Orca",
                    "pair": f"{token_address}/USDC",
                    "liquidity_usd": 125000,
                    "volume_24h": 95000,
                    "apr": 0.38,
                    "fee_tier": 0.003,
                    "pool_age_days": 8
                }
            ],
            "total_liquidity_usd": 375000,
            "total_volume_24h": 275000,
            "volume_to_liquidity_ratio": 0.73,
            "liquidity_distribution": {
                "concentrated": 0.65,
                "spread": 0.35
            },
            "pool_health_score": 0.78,  # 0-1 scale
            "liquidity_risks": [
                {
                    "risk": "low_liquidity",
                    "severity": "low",
                    "description": "Relatively low total liquidity"
                }
            ],
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        return mock_result
    
    async def _detect_whale_activity(self, token_address: str, timeframe: str = "24h") -> Dict[str, Any]:
        """Detect whale activity and large holder movements.
        
        Args:
            token_address: Token mint address
            timeframe: Analysis timeframe
            
        Returns:
            Dict containing whale activity analysis
        """
        logger.info(f"🐋 Detecting whale activity for {token_address} ({timeframe})")
        
        # Simulated whale activity analysis
        mock_result = {
            "token_address": token_address,
            "timeframe": timeframe,
            "whale_transactions": [
                {
                    "whale_address": "5Q544f...Kp9uF",
                    "transaction_type": "buy",
                    "amount": 1500000,
                    "value_usd": 75000,
                    "price_impact": 0.034,
                    "timestamp": "2024-01-01T10:30:00Z"
                },
                {
                    "whale_address": "7R123a...Mn2pL",
                    "transaction_type": "sell",
                    "amount": 800000,
                    "value_usd": 38000,
                    "price_impact": 0.021,
                    "timestamp": "2024-01-01T11:15:00Z"
                }
            ],
            "whale_activity_summary": {
                "total_whale_transactions": 12,
                "net_whale_flow": 2300000,  # Positive = net buying
                "whale_flow_direction": "accumulation",
                "average_whale_transaction_size": 1200000,
                "largest_whale_transaction": 1500000
            },
            "whale_impact_metrics": {
                "total_price_impact": 0.187,
                "market_influence_score": 0.72,
                "whale_coordination_detected": False
            },
            "alerts": [
                {
                    "type": "whale_accumulation",
                    "severity": "medium",
                    "description": "Net whale accumulation detected over 24h period"
                }
            ],
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        return mock_result
    
    async def comprehensive_onchain_analysis(self, token_address: str) -> Dict[str, Any]:
        """Perform comprehensive on-chain analysis for a token.
        
        Args:
            token_address: Token mint address to analyze
            
        Returns:
            Dict containing comprehensive on-chain analysis
        """
        prompt = f"""
        Perform comprehensive on-chain analysis for token {token_address}. Please:
        1. Analyze token holder distribution using analyze_token_holders
        2. Check token distribution and supply metrics using check_token_distribution
        3. Analyze recent transaction patterns using analyze_transaction_patterns
        4. Assess liquidity pools using assess_liquidity_pools
        5. Detect whale activity using detect_whale_activity
        6. Synthesize findings into overall token health assessment
        
        Token Address: {token_address}
        
        Focus on identifying potential risks, opportunities, and trading implications.
        Return comprehensive analysis in JSON format with clear recommendations.
        """
        
        try:
            result = await self.agent.execute(prompt)
            logger.info(f"🔍 Comprehensive on-chain analysis completed for {token_address}")
            return result
        except Exception as e:
            logger.error(f"❌ Error in comprehensive on-chain analysis: {e}")
            return {"error": str(e), "token_address": token_address}
    
    async def detect_rug_pull_signals(self, token_address: str) -> Dict[str, Any]:
        """Detect potential rug pull signals through on-chain analysis.
        
        Args:
            token_address: Token mint address to analyze
            
        Returns:
            Dict containing rug pull risk assessment
        """
        prompt = f"""
        Analyze token {token_address} for potential rug pull signals. Please:
        1. Check holder distribution for concentration risks
        2. Analyze token distribution for red flags
        3. Look for suspicious transaction patterns
        4. Assess liquidity pool health and stability
        5. Detect unusual whale activity patterns
        6. Calculate overall rug pull risk score
        
        Focus specifically on identifying warning signs and red flags.
        Return risk assessment in JSON format with clear risk level and recommendations.
        """
        
        try:
            result = await self.agent.execute(prompt)
            logger.info(f"🚨 Rug pull signal analysis completed for {token_address}")
            return result
        except Exception as e:
            logger.error(f"❌ Error detecting rug pull signals: {e}")
            return {
                "error": str(e),
                "token_address": token_address,
                "rug_pull_risk": "HIGH",
                "recommendation": "AVOID"
            }
    
    async def monitor_token_health(self, token_addresses: List[str]) -> Dict[str, Any]:
        """Monitor overall health of multiple tokens.
        
        Args:
            token_addresses: List of token addresses to monitor
            
        Returns:
            Dict containing health monitoring results
        """
        prompt = f"""
        Monitor the health of multiple tokens: {token_addresses}. Please:
        1. Perform basic on-chain analysis for each token
        2. Compare relative health scores
        3. Identify tokens with declining health
        4. Detect any concerning patterns across tokens
        5. Prioritize tokens requiring immediate attention
        
        Return monitoring report in JSON format with ranked health scores.
        """
        
        try:
            result = await self.agent.execute(prompt)
            logger.info(f"📊 Token health monitoring completed for {len(token_addresses)} tokens")
            return result
        except Exception as e:
            logger.error(f"❌ Error monitoring token health: {e}")
            return {"error": str(e), "monitored_tokens": token_addresses}

    # 🛡️ RUGPULL SCANNER - Poziom 1: Zero-jedynkowe testy dyskwalifikacyjne

    async def _check_lp_burned(self, token_address: str) -> Dict[str, Any]:
        """Check if liquidity pool tokens are burned (sent to burn address).

        This is a CRITICAL zero-one test. If LP is not burned, token can be rug pulled.

        Args:
            token_address: Token mint address to check

        Returns:
            Dict with LP burn status and risk assessment
        """
        logger.info(f"🔥 Checking LP burned status for: {token_address}")

        # Solana burn address: 11111111111111111111111111111111
        burn_address = "11111111111111111111111111111111"

        # In production, this would query Solana RPC for actual LP token holders
        # For now, simulate the check with realistic scenarios

        # Simulate LP burn check
        import random
        is_burned = random.choice([True, False, False])  # 33% chance burned (realistic)

        result = {
            "token_address": token_address,
            "lp_burned": is_burned,
            "burn_address": burn_address,
            "risk_level": "LOW" if is_burned else "CRITICAL",
            "test_result": "PASS" if is_burned else "FAIL",
            "recommendation": "PROCEED" if is_burned else "REJECT_IMMEDIATELY",
            "details": {
                "check_type": "LP_BURN_VERIFICATION",
                "burn_percentage": 100.0 if is_burned else 0.0,
                "liquidity_locked": is_burned,
                "rug_pull_protection": is_burned
            }
        }

        if not is_burned:
            result["warning"] = "🚨 CRITICAL: LP tokens not burned - high rug pull risk!"
            logger.warning(f"🚨 LP NOT BURNED for {token_address} - CRITICAL RISK!")
        else:
            logger.info(f"✅ LP burned for {token_address} - protection confirmed")

        return result

    async def _verify_mint_authority(self, token_address: str) -> Dict[str, Any]:
        """Verify if mint authority has been renounced (disabled).

        If mint authority exists, developer can print unlimited tokens and crash price.

        Args:
            token_address: Token mint address to check

        Returns:
            Dict with mint authority status and risk assessment
        """
        logger.info(f"🏭 Verifying mint authority for: {token_address}")

        # In production, query Solana RPC for mint account info
        # For now, simulate realistic scenarios

        import random
        authority_renounced = random.choice([True, True, False])  # 66% chance renounced

        result = {
            "token_address": token_address,
            "mint_authority_renounced": authority_renounced,
            "risk_level": "LOW" if authority_renounced else "CRITICAL",
            "test_result": "PASS" if authority_renounced else "FAIL",
            "recommendation": "PROCEED" if authority_renounced else "REJECT_IMMEDIATELY",
            "details": {
                "check_type": "MINT_AUTHORITY_VERIFICATION",
                "can_mint_new_tokens": not authority_renounced,
                "supply_inflation_risk": not authority_renounced,
                "developer_control": not authority_renounced
            }
        }

        if not authority_renounced:
            result["warning"] = "🚨 CRITICAL: Mint authority active - unlimited token printing possible!"
            logger.warning(f"🚨 MINT AUTHORITY ACTIVE for {token_address} - CRITICAL RISK!")
        else:
            logger.info(f"✅ Mint authority renounced for {token_address} - supply protected")

        return result

    async def _check_freeze_authority(self, token_address: str) -> Dict[str, Any]:
        """Check if freeze authority has been renounced.

        If freeze authority exists, developer can freeze trading at any time.

        Args:
            token_address: Token mint address to check

        Returns:
            Dict with freeze authority status and risk assessment
        """
        logger.info(f"🧊 Checking freeze authority for: {token_address}")

        # In production, query Solana RPC for mint account freeze authority
        # For now, simulate realistic scenarios

        import random
        authority_renounced = random.choice([True, True, False])  # 66% chance renounced

        result = {
            "token_address": token_address,
            "freeze_authority_renounced": authority_renounced,
            "risk_level": "LOW" if authority_renounced else "CRITICAL",
            "test_result": "PASS" if authority_renounced else "FAIL",
            "recommendation": "PROCEED" if authority_renounced else "REJECT_IMMEDIATELY",
            "details": {
                "check_type": "FREEZE_AUTHORITY_VERIFICATION",
                "can_freeze_trading": not authority_renounced,
                "trading_halt_risk": not authority_renounced,
                "developer_control": not authority_renounced
            }
        }

        if not authority_renounced:
            result["warning"] = "🚨 CRITICAL: Freeze authority active - trading can be halted!"
            logger.warning(f"🚨 FREEZE AUTHORITY ACTIVE for {token_address} - CRITICAL RISK!")
        else:
            logger.info(f"✅ Freeze authority renounced for {token_address} - trading protected")

        return result

    async def _verify_ownership_renounced(self, token_address: str) -> Dict[str, Any]:
        """Verify if contract ownership has been renounced.

        If ownership exists, developer can change contract rules after launch.

        Args:
            token_address: Token mint address to check

        Returns:
            Dict with ownership status and risk assessment
        """
        logger.info(f"👑 Verifying ownership renouncement for: {token_address}")

        # In production, check if update authority is null
        # For now, simulate realistic scenarios

        import random
        ownership_renounced = random.choice([True, False, False])  # 33% chance renounced

        result = {
            "token_address": token_address,
            "ownership_renounced": ownership_renounced,
            "risk_level": "LOW" if ownership_renounced else "HIGH",  # Not always critical
            "test_result": "PASS" if ownership_renounced else "WARNING",
            "recommendation": "PROCEED" if ownership_renounced else "PROCEED_WITH_CAUTION",
            "details": {
                "check_type": "OWNERSHIP_VERIFICATION",
                "can_update_contract": not ownership_renounced,
                "rule_change_risk": not ownership_renounced,
                "developer_control": not ownership_renounced
            }
        }

        if not ownership_renounced:
            result["warning"] = "⚠️ WARNING: Ownership not renounced - contract rules can change!"
            logger.warning(f"⚠️ OWNERSHIP NOT RENOUNCED for {token_address} - proceed with caution")
        else:
            logger.info(f"✅ Ownership renounced for {token_address} - contract immutable")

        return result

    async def _perform_rugpull_level1_scan(self, token_address: str) -> Dict[str, Any]:
        """Perform complete Level 1 rugpull scan with all zero-one tests.

        This is the main entry point for contract-level rugpull detection.
        Any CRITICAL failure results in immediate token disqualification.

        Args:
            token_address: Token mint address to scan

        Returns:
            Dict with complete Level 1 scan results and final verdict
        """
        logger.info(f"🛡️ Starting Level 1 Rugpull Scan for: {token_address}")

        try:
            # Run all zero-one tests in parallel for speed
            import asyncio

            lp_check, mint_check, freeze_check, ownership_check = await asyncio.gather(
                self._check_lp_burned(token_address),
                self._verify_mint_authority(token_address),
                self._check_freeze_authority(token_address),
                self._verify_ownership_renounced(token_address),
                return_exceptions=True
            )

            # Collect all test results
            tests = {
                "lp_burned": lp_check,
                "mint_authority": mint_check,
                "freeze_authority": freeze_check,
                "ownership": ownership_check
            }

            # Count critical failures (zero-one tests)
            critical_failures = []
            warnings = []

            for test_name, test_result in tests.items():
                if isinstance(test_result, Exception):
                    critical_failures.append(f"{test_name}: {str(test_result)}")
                    continue

                # Only process dict results (successful tests)
                if isinstance(test_result, dict):
                    if test_result.get("risk_level") == "CRITICAL":
                        critical_failures.append(f"{test_name}: {test_result.get('warning', 'Critical failure')}")
                    elif test_result.get("risk_level") == "HIGH":
                        warnings.append(f"{test_name}: {test_result.get('warning', 'High risk detected')}")
                else:
                    # Unexpected result type
                    critical_failures.append(f"{test_name}: Unexpected result type")

            # Determine final verdict
            has_critical_failures = len(critical_failures) > 0
            overall_risk = "CRITICAL" if has_critical_failures else ("HIGH" if warnings else "LOW")

            # Final recommendation based on zero-one logic
            if has_critical_failures:
                recommendation = "REJECT_IMMEDIATELY"
                verdict = "DISQUALIFIED"
                logger.error(f"🚨 LEVEL 1 SCAN FAILED for {token_address} - {len(critical_failures)} critical failures")
            elif warnings:
                recommendation = "PROCEED_WITH_EXTREME_CAUTION"
                verdict = "CONDITIONAL_PASS"
                logger.warning(f"⚠️ LEVEL 1 SCAN WARNING for {token_address} - {len(warnings)} warnings")
            else:
                recommendation = "PROCEED_TO_LEVEL2"
                verdict = "PASS"
                logger.info(f"✅ LEVEL 1 SCAN PASSED for {token_address} - all tests passed")

            # Compile final report
            scan_result = {
                "token_address": token_address,
                "scan_level": "LEVEL_1_CONTRACT_ANALYSIS",
                "timestamp": datetime.now().isoformat(),
                "overall_risk": overall_risk,
                "verdict": verdict,
                "recommendation": recommendation,
                "tests_performed": {
                    "lp_burned": tests["lp_burned"],
                    "mint_authority": tests["mint_authority"],
                    "freeze_authority": tests["freeze_authority"],
                    "ownership": tests["ownership"]
                },
                "summary": {
                    "total_tests": 4,
                    "critical_failures": len(critical_failures),
                    "warnings": len(warnings),
                    "passes": 4 - len(critical_failures) - len(warnings)
                },
                "critical_failures": critical_failures,
                "warnings": warnings,
                "next_steps": "Proceed to Level 2 (Social Analysis)" if verdict == "PASS" else "Token disqualified"
            }

            return scan_result

        except Exception as e:
            logger.error(f"❌ Level 1 scan failed for {token_address}: {e}")
            return {
                "token_address": token_address,
                "scan_level": "LEVEL_1_CONTRACT_ANALYSIS",
                "verdict": "ERROR",
                "recommendation": "REJECT_IMMEDIATELY",
                "error": str(e),
                "overall_risk": "CRITICAL"
            }

    # 📊 RUGPULL SCANNER - Analiza Dystrybucji Holderów

    async def _analyze_holder_concentration(self, token_address: str, top_n: int = 20) -> Dict[str, Any]:
        """Analyze holder concentration to detect centralization risks.

        Args:
            token_address: Token mint address to analyze
            top_n: Number of top holders to analyze (default: 20)

        Returns:
            Dict with concentration analysis and risk assessment
        """
        logger.info(f"📊 Analyzing holder concentration for: {token_address}")

        # In production, this would query Solana RPC for actual holder data
        # For now, simulate realistic holder distribution scenarios

        import random

        # Generate realistic holder distribution
        total_supply = 1_000_000_000  # 1B tokens
        holders = []

        # Simulate different concentration scenarios
        scenario = random.choice(["healthy", "concentrated", "whale_dominated"])

        if scenario == "healthy":
            # Healthy distribution - no single holder >5%
            for i in range(top_n):
                percentage = random.uniform(0.5, 4.5)  # 0.5% to 4.5%
                holders.append({
                    "rank": i + 1,
                    "address": f"holder_{i+1}_address",
                    "balance": int(total_supply * percentage / 100),
                    "percentage": percentage,
                    "is_dex": i < 3  # First 3 are DEX addresses
                })
        elif scenario == "concentrated":
            # Concentrated - some holders >5% but <10%
            for i in range(top_n):
                if i < 3:
                    percentage = random.uniform(6.0, 9.5)  # 6% to 9.5%
                else:
                    percentage = random.uniform(0.5, 4.0)
                holders.append({
                    "rank": i + 1,
                    "address": f"holder_{i+1}_address",
                    "balance": int(total_supply * percentage / 100),
                    "percentage": percentage,
                    "is_dex": i < 2  # First 2 are DEX addresses
                })
        else:  # whale_dominated
            # Whale dominated - major holder >10%
            for i in range(top_n):
                if i == 0:
                    percentage = random.uniform(15.0, 25.0)  # Whale: 15-25%
                elif i < 4:
                    percentage = random.uniform(5.0, 8.0)   # Other whales: 5-8%
                else:
                    percentage = random.uniform(0.1, 2.0)
                holders.append({
                    "rank": i + 1,
                    "address": f"holder_{i+1}_address",
                    "balance": int(total_supply * percentage / 100),
                    "percentage": percentage,
                    "is_dex": i < 2  # First 2 are DEX addresses
                })

        # Filter out DEX addresses for concentration analysis
        non_dex_holders = [h for h in holders if not h["is_dex"]]

        # Calculate concentration metrics
        top_1_percentage = non_dex_holders[0]["percentage"] if non_dex_holders else 0
        top_5_percentage = sum(h["percentage"] for h in non_dex_holders[:5])
        top_10_percentage = sum(h["percentage"] for h in non_dex_holders[:10])

        # Risk assessment based on concentration
        concentration_risk = "LOW"
        risk_factors = []

        if top_1_percentage > 10:
            concentration_risk = "CRITICAL"
            risk_factors.append(f"Single holder owns {top_1_percentage:.1f}% (>10% threshold)")
        elif top_1_percentage > 5:
            concentration_risk = "HIGH"
            risk_factors.append(f"Single holder owns {top_1_percentage:.1f}% (>5% threshold)")

        if top_5_percentage > 30:
            concentration_risk = "CRITICAL"
            risk_factors.append(f"Top 5 holders own {top_5_percentage:.1f}% (>30% threshold)")
        elif top_5_percentage > 20:
            if concentration_risk == "LOW":
                concentration_risk = "HIGH"
            risk_factors.append(f"Top 5 holders own {top_5_percentage:.1f}% (>20% threshold)")

        if top_10_percentage > 50:
            concentration_risk = "CRITICAL"
            risk_factors.append(f"Top 10 holders own {top_10_percentage:.1f}% (>50% threshold)")

        result = {
            "token_address": token_address,
            "analysis_type": "HOLDER_CONCENTRATION",
            "total_holders_analyzed": len(holders),
            "non_dex_holders": len(non_dex_holders),
            "concentration_metrics": {
                "top_1_holder_percentage": top_1_percentage,
                "top_5_holders_percentage": top_5_percentage,
                "top_10_holders_percentage": top_10_percentage,
                "largest_non_dex_holder": top_1_percentage
            },
            "risk_assessment": {
                "concentration_risk": concentration_risk,
                "risk_factors": risk_factors,
                "recommendation": "REJECT" if concentration_risk == "CRITICAL" else ("CAUTION" if concentration_risk == "HIGH" else "PROCEED")
            },
            "holders_detail": holders[:10],  # Return top 10 for analysis
            "scenario_simulated": scenario  # For testing purposes
        }

        if concentration_risk == "CRITICAL":
            logger.warning(f"🚨 CRITICAL concentration risk for {token_address}: {risk_factors}")
        elif concentration_risk == "HIGH":
            logger.warning(f"⚠️ HIGH concentration risk for {token_address}: {risk_factors}")
        else:
            logger.info(f"✅ Healthy holder distribution for {token_address}")

        return result

    async def _detect_whale_dumping_risk(self, token_address: str) -> Dict[str, Any]:
        """Detect potential whale dumping risk based on large holder behavior.

        Args:
            token_address: Token mint address to analyze

        Returns:
            Dict with whale dumping risk assessment
        """
        logger.info(f"🐋 Detecting whale dumping risk for: {token_address}")

        # In production, analyze recent transaction patterns of large holders
        # For now, simulate whale behavior analysis

        import random

        # Simulate whale activity scenarios
        whale_scenario = random.choice(["stable", "accumulating", "distributing", "dumping"])

        whales = []
        total_whale_risk = 0

        # Generate whale data based on scenario
        for i in range(5):  # Top 5 whales
            whale_address = f"whale_{i+1}_address"

            if whale_scenario == "stable":
                recent_activity = "minimal"
                dump_risk = random.uniform(0.1, 0.3)
            elif whale_scenario == "accumulating":
                recent_activity = "buying"
                dump_risk = random.uniform(0.0, 0.2)
            elif whale_scenario == "distributing":
                recent_activity = "selling_gradually"
                dump_risk = random.uniform(0.4, 0.7)
            else:  # dumping
                recent_activity = "selling_heavily"
                dump_risk = random.uniform(0.7, 0.9)

            whale_data = {
                "address": whale_address,
                "rank": i + 1,
                "balance_percentage": random.uniform(3.0, 12.0),
                "recent_activity": recent_activity,
                "dump_risk_score": dump_risk,
                "days_since_last_transaction": random.randint(1, 30),
                "transaction_frequency": random.choice(["low", "medium", "high"])
            }

            whales.append(whale_data)
            total_whale_risk += dump_risk

        # Calculate overall dumping risk
        avg_whale_risk = total_whale_risk / len(whales)

        if avg_whale_risk > 0.7:
            risk_level = "CRITICAL"
            recommendation = "AVOID_IMMEDIATELY"
        elif avg_whale_risk > 0.5:
            risk_level = "HIGH"
            recommendation = "EXTREME_CAUTION"
        elif avg_whale_risk > 0.3:
            risk_level = "MEDIUM"
            recommendation = "MONITOR_CLOSELY"
        else:
            risk_level = "LOW"
            recommendation = "PROCEED"

        result = {
            "token_address": token_address,
            "analysis_type": "WHALE_DUMPING_RISK",
            "whale_scenario": whale_scenario,
            "overall_dump_risk": avg_whale_risk,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "whale_analysis": whales,
            "risk_factors": [],
            "protective_factors": []
        }

        # Add specific risk factors
        if whale_scenario == "dumping":
            result["risk_factors"].append("Heavy selling activity detected from major holders")
        elif whale_scenario == "distributing":
            result["risk_factors"].append("Gradual distribution pattern observed")

        if avg_whale_risk > 0.5:
            result["risk_factors"].append(f"Average whale dump risk: {avg_whale_risk:.2f}")

        # Add protective factors
        if whale_scenario == "accumulating":
            result["protective_factors"].append("Whales are accumulating, indicating confidence")
        elif whale_scenario == "stable":
            result["protective_factors"].append("Stable whale behavior, minimal selling pressure")

        if risk_level == "CRITICAL":
            logger.warning(f"🚨 CRITICAL whale dumping risk for {token_address}")
        elif risk_level == "HIGH":
            logger.warning(f"⚠️ HIGH whale dumping risk for {token_address}")
        else:
            logger.info(f"✅ Acceptable whale dumping risk for {token_address}")

        return result

    async def _check_dex_exclusions(self, token_address: str) -> Dict[str, Any]:
        """Check and exclude DEX addresses from holder concentration analysis.

        Args:
            token_address: Token mint address to analyze

        Returns:
            Dict with DEX exclusion information
        """
        logger.info(f"🏪 Checking DEX exclusions for: {token_address}")

        # Known Solana DEX addresses (in production, maintain comprehensive list)
        known_dex_addresses = {
            "raydium_amm": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            "raydium_pool": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
            "orca_whirlpool": "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
            "jupiter_aggregator": "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
            "serum_dex": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "meteora": "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"
        }

        # In production, query actual holder data and match against DEX addresses
        # For now, simulate DEX detection

        import random

        detected_dexes = []
        total_dex_percentage = 0

        # Simulate DEX holdings
        for dex_name, dex_address in known_dex_addresses.items():
            if random.choice([True, False, False]):  # 33% chance DEX holds tokens
                percentage = random.uniform(5.0, 25.0)  # DEXes typically hold 5-25%
                detected_dexes.append({
                    "dex_name": dex_name,
                    "address": dex_address,
                    "percentage": percentage,
                    "liquidity_provider": True,
                    "exclude_from_concentration": True
                })
                total_dex_percentage += percentage

        # Analysis results
        result = {
            "token_address": token_address,
            "analysis_type": "DEX_EXCLUSION_CHECK",
            "detected_dexes": detected_dexes,
            "total_dex_percentage": total_dex_percentage,
            "dexes_count": len(detected_dexes),
            "exclusion_impact": {
                "addresses_excluded": len(detected_dexes),
                "percentage_excluded": total_dex_percentage,
                "concentration_adjustment": f"Reduced by {total_dex_percentage:.1f}%"
            },
            "liquidity_assessment": {
                "dex_diversity": len(detected_dexes),
                "liquidity_distribution": "healthy" if len(detected_dexes) >= 2 else "concentrated",
                "major_dex_present": any(d["percentage"] > 15 for d in detected_dexes)
            }
        }

        if len(detected_dexes) == 0:
            result["warning"] = "No DEX liquidity detected - potential liquidity risk"
            logger.warning(f"⚠️ No DEX liquidity detected for {token_address}")
        elif len(detected_dexes) == 1:
            result["warning"] = "Single DEX liquidity - centralization risk"
            logger.warning(f"⚠️ Single DEX liquidity for {token_address}")
        else:
            logger.info(f"✅ Multiple DEX liquidity detected for {token_address}")

        return result

    async def _perform_holder_distribution_scan(self, token_address: str) -> Dict[str, Any]:
        """Perform complete holder distribution analysis combining all checks.

        This aggregates concentration analysis, whale dumping risk, and DEX exclusions
        to provide comprehensive holder distribution risk assessment.

        Args:
            token_address: Token mint address to scan

        Returns:
            Dict with complete holder distribution analysis and risk verdict
        """
        logger.info(f"📊 Starting Holder Distribution Scan for: {token_address}")

        try:
            # Run all holder analysis functions in parallel
            import asyncio

            concentration_analysis, whale_risk_analysis, dex_exclusion_analysis = await asyncio.gather(
                self._analyze_holder_concentration(token_address),
                self._detect_whale_dumping_risk(token_address),
                self._check_dex_exclusions(token_address),
                return_exceptions=True
            )

            # Collect analysis results
            analyses = {
                "concentration": concentration_analysis,
                "whale_risk": whale_risk_analysis,
                "dex_exclusions": dex_exclusion_analysis
            }

            # Aggregate risk factors
            critical_risks = []
            high_risks = []
            warnings = []

            for analysis_name, analysis_result in analyses.items():
                if isinstance(analysis_result, Exception):
                    critical_risks.append(f"{analysis_name}: {str(analysis_result)}")
                    continue

                if isinstance(analysis_result, dict):
                    # Check concentration analysis
                    if analysis_name == "concentration":
                        conc_risk = analysis_result.get("risk_assessment", {}).get("concentration_risk", "LOW")
                        if conc_risk == "CRITICAL":
                            critical_risks.extend(analysis_result.get("risk_assessment", {}).get("risk_factors", []))
                        elif conc_risk == "HIGH":
                            high_risks.extend(analysis_result.get("risk_assessment", {}).get("risk_factors", []))

                    # Check whale dumping risk
                    elif analysis_name == "whale_risk":
                        whale_risk = analysis_result.get("risk_level", "LOW")
                        if whale_risk == "CRITICAL":
                            critical_risks.append(f"Critical whale dumping risk detected")
                        elif whale_risk == "HIGH":
                            high_risks.append(f"High whale dumping risk detected")
                        elif whale_risk == "MEDIUM":
                            warnings.append(f"Medium whale dumping risk detected")

                    # Check DEX exclusions
                    elif analysis_name == "dex_exclusions":
                        if "warning" in analysis_result:
                            warnings.append(analysis_result["warning"])

            # Determine overall risk level
            if critical_risks:
                overall_risk = "CRITICAL"
                recommendation = "REJECT_IMMEDIATELY"
                verdict = "DISQUALIFIED"
            elif high_risks:
                overall_risk = "HIGH"
                recommendation = "PROCEED_WITH_EXTREME_CAUTION"
                verdict = "CONDITIONAL_PASS"
            elif warnings:
                overall_risk = "MEDIUM"
                recommendation = "PROCEED_WITH_CAUTION"
                verdict = "CONDITIONAL_PASS"
            else:
                overall_risk = "LOW"
                recommendation = "PROCEED_TO_NEXT_LEVEL"
                verdict = "PASS"

            # Compile comprehensive report
            scan_result = {
                "token_address": token_address,
                "scan_level": "HOLDER_DISTRIBUTION_ANALYSIS",
                "timestamp": datetime.now().isoformat(),
                "overall_risk": overall_risk,
                "verdict": verdict,
                "recommendation": recommendation,
                "detailed_analyses": {
                    "concentration_analysis": analyses["concentration"],
                    "whale_risk_analysis": analyses["whale_risk"],
                    "dex_exclusion_analysis": analyses["dex_exclusions"]
                },
                "risk_summary": {
                    "critical_risks": len(critical_risks),
                    "high_risks": len(high_risks),
                    "warnings": len(warnings),
                    "total_issues": len(critical_risks) + len(high_risks) + len(warnings)
                },
                "risk_factors": {
                    "critical": critical_risks,
                    "high": high_risks,
                    "warnings": warnings
                },
                "next_steps": "Proceed to Social Analysis" if verdict == "PASS" else "Review holder risks"
            }

            # Log results
            if verdict == "DISQUALIFIED":
                logger.error(f"🚨 HOLDER DISTRIBUTION SCAN FAILED for {token_address} - {len(critical_risks)} critical risks")
            elif verdict == "CONDITIONAL_PASS":
                logger.warning(f"⚠️ HOLDER DISTRIBUTION SCAN WARNING for {token_address} - proceed with caution")
            else:
                logger.info(f"✅ HOLDER DISTRIBUTION SCAN PASSED for {token_address}")

            return scan_result

        except Exception as e:
            logger.error(f"❌ Holder distribution scan failed for {token_address}: {e}")
            return {
                "token_address": token_address,
                "scan_level": "HOLDER_DISTRIBUTION_ANALYSIS",
                "verdict": "ERROR",
                "recommendation": "REJECT_IMMEDIATELY",
                "error": str(e),
                "overall_risk": "CRITICAL"
            }

# Factory function for easy instantiation
def create_onchain_analysis_agent() -> OnChainAnalysisAgent:
    """Create and return a configured OnChainAnalysisAgent instance."""
    return OnChainAnalysisAgent()