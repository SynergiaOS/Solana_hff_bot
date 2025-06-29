import logging
from typing import Dict, List, Any
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)

class PerceptionLayer:
    """Multi-modal perception layer for processing market data inputs"""
    
    def __init__(self):
        self.processors = {
            "market_data": MarketDataProcessor(),
            "news": NewsProcessor(),
            "social": SocialMediaProcessor(),
            "on_chain": OnChainDataProcessor()
        }
        logger.info("Perception Layer initialized")
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data through appropriate processors"""
        # Determine data type
        data_type = self._determine_data_type(input_data)
        
        # Process with appropriate processor
        if data_type in self.processors:
            processed_data = await self.processors[data_type].process(input_data)
        else:
            # Default processing
            processed_data = {
                "type": "unknown",
                "raw_data": input_data,
                "processed": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            logger.warning(f"Unknown data type for perception: {data_type}")
            
        # Add metadata
        processed_data["perception_timestamp"] = datetime.now(timezone.utc).isoformat()
        processed_data["perception_type"] = data_type
        
        return processed_data
        
    def _determine_data_type(self, data: Dict[str, Any]) -> str:
        """Determine the type of input data"""
        # Check for market data indicators
        if any(key in data for key in ["symbol", "price", "volume", "bid", "ask"]):
            return "market_data"
            
        # Check for news indicators
        if any(key in data for key in ["title", "article", "news", "headline"]):
            return "news"
            
        # Check for social media indicators
        if any(key in data for key in ["tweet", "post", "sentiment", "social"]):
            return "social"
            
        # Check for on-chain data indicators
        if any(key in data for key in ["transaction", "block", "address", "signature"]):
            return "on_chain"
            
        # Default to market data
        return "market_data"

class MarketDataProcessor:
    """Processor for market data inputs"""
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process market data"""
        # Extract key fields
        symbol = data.get("symbol", "UNKNOWN")
        price = data.get("price")
        volume = data.get("volume")
        
        # Normalize data format
        normalized_data = {
            "symbol": symbol,
            "price": float(price) if price is not None else None,
            "volume_24h": float(volume) if volume is not None else None,
            "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat())
        }
        
        # Add bid/ask if available
        if "bid" in data and "ask" in data:
            normalized_data["bid"] = float(data["bid"])
            normalized_data["ask"] = float(data["ask"])
            normalized_data["spread"] = normalized_data["ask"] - normalized_data["bid"]
            normalized_data["spread_percentage"] = (normalized_data["spread"] / normalized_data["bid"]) * 100
            
        # Add OHLC if available
        if all(key in data for key in ["open", "high", "low", "close"]):
            normalized_data["ohlc"] = {
                "open": float(data["open"]),
                "high": float(data["high"]),
                "low": float(data["low"]),
                "close": float(data["close"])
            }
            
        # Calculate price change if possible
        if "previous_price" in data and price is not None:
            prev_price = float(data["previous_price"])
            normalized_data["price_change"] = normalized_data["price"] - prev_price
            normalized_data["price_change_percentage"] = (normalized_data["price_change"] / prev_price) * 100
            
        # Add market cap if available
        if "market_cap" in data:
            normalized_data["market_cap"] = float(data["market_cap"])
            
        # Add exchange info if available
        if "exchange" in data:
            normalized_data["exchange"] = data["exchange"]
            
        # Add data source
        normalized_data["source"] = data.get("source", "unknown")
        normalized_data["processed"] = True
        
        logger.info(f"Processed market data for {symbol}")
        return normalized_data

class NewsProcessor:
    """Processor for news data inputs"""
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process news data"""
        # Extract key fields
        title = data.get("title", "")
        content = data.get("content", data.get("article", ""))
        source = data.get("source", "unknown")
        
        # Normalize data format
        normalized_data = {
            "title": title,
            "content": content,
            "source": source,
            "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "url": data.get("url", "")
        }
        
        # Extract mentioned symbols
        mentioned_symbols = self._extract_symbols(title + " " + content)
        normalized_data["mentioned_symbols"] = mentioned_symbols
        
        # Simple sentiment analysis
        sentiment = self._analyze_sentiment(title + " " + content)
        normalized_data["sentiment"] = sentiment
        
        # Add relevance score
        normalized_data["relevance_score"] = self._calculate_relevance(normalized_data)
        normalized_data["processed"] = True
        
        logger.info(f"Processed news: {title[:30]}... (sentiment: {sentiment['label']})")
        return normalized_data
        
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract trading symbols from text"""
        # Simple regex for common crypto symbols
        symbol_pattern = r'\b(BTC|ETH|SOL|USDC|USDT|WIF|BONK|JUP|RAY|ORCA|JTO)\b'
        matches = re.findall(symbol_pattern, text.upper())
        return list(set(matches))  # Remove duplicates
        
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple rule-based sentiment analysis"""
        # Positive and negative word lists
        positive_words = ["bullish", "surge", "gain", "rally", "soar", "jump", "positive", 
                         "growth", "profit", "success", "breakthrough", "partnership"]
        negative_words = ["bearish", "crash", "drop", "fall", "decline", "plunge", "negative",
                         "loss", "fail", "risk", "concern", "warning", "investigation"]
        
        # Count occurrences
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Determine sentiment
        if positive_count > negative_count:
            label = "positive"
            score = min(1.0, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            label = "negative"
            score = max(0.0, 0.5 - (negative_count - positive_count) * 0.1)
        else:
            label = "neutral"
            score = 0.5
            
        return {
            "label": label,
            "score": score,
            "positive_count": positive_count,
            "negative_count": negative_count
        }
        
    def _calculate_relevance(self, news_data: Dict[str, Any]) -> float:
        """Calculate relevance score for news"""
        score = 0.0
        
        # More symbols mentioned = more relevant
        score += len(news_data["mentioned_symbols"]) * 0.2
        
        # Title mentions are more important
        title_mentions = sum(1 for symbol in news_data["mentioned_symbols"] 
                           if symbol in news_data["title"].upper())
        score += title_mentions * 0.3
        
        # Recent news is more relevant
        try:
            news_time = datetime.fromisoformat(news_data["timestamp"])
            now = datetime.now(timezone.utc)
            hours_old = (now - news_time).total_seconds() / 3600
            recency_score = max(0, 1 - (hours_old / 24))  # 0 after 24 hours
            score += recency_score * 0.5
        except (ValueError, TypeError):
            # If timestamp parsing fails
            pass
            
        # Cap at 1.0
        return min(1.0, score)

class SocialMediaProcessor:
    """Processor for social media data inputs"""
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process social media data"""
        # Extract key fields
        content = data.get("content", data.get("text", data.get("tweet", "")))
        platform = data.get("platform", "unknown")
        author = data.get("author", data.get("username", "unknown"))
        
        # Normalize data format
        normalized_data = {
            "content": content,
            "platform": platform,
            "author": author,
            "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "likes": data.get("likes", 0),
            "reposts": data.get("reposts", data.get("retweets", 0)),
            "comments": data.get("comments", data.get("replies", 0))
        }
        
        # Extract mentioned symbols
        mentioned_symbols = self._extract_symbols(content)
        normalized_data["mentioned_symbols"] = mentioned_symbols
        
        # Simple sentiment analysis (reusing from NewsProcessor)
        news_processor = NewsProcessor()
        sentiment = news_processor._analyze_sentiment(content)
        normalized_data["sentiment"] = sentiment
        
        # Calculate influence score
        normalized_data["influence_score"] = self._calculate_influence(normalized_data)
        normalized_data["processed"] = True
        
        logger.info(f"Processed social media from {author} on {platform}")
        return normalized_data
        
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract trading symbols from text"""
        # Simple regex for common crypto symbols and cashtags
        symbol_pattern = r'\b(BTC|ETH|SOL|USDC|USDT|WIF|BONK|JUP|RAY|ORCA|JTO)\b|\$([A-Z]{2,5})'
        matches = re.findall(symbol_pattern, text.upper())
        
        # Process matches (handle both regex groups)
        symbols = []
        for match in matches:
            if isinstance(match, tuple):
                # Add non-empty group
                symbols.extend([g for g in match if g])
            else:
                symbols.append(match)
                
        return list(set(symbols))  # Remove duplicates
        
    def _calculate_influence(self, social_data: Dict[str, Any]) -> float:
        """Calculate influence score for social media post"""
        score = 0.0
        
        # Engagement metrics
        likes = social_data.get("likes", 0)
        reposts = social_data.get("reposts", 0)
        comments = social_data.get("comments", 0)
        
        # Calculate engagement score
        engagement = likes + (reposts * 2) + (comments * 3)  # Comments weighted highest
        
        # Log scale for engagement (to handle viral posts reasonably)
        if engagement > 0:
            log_engagement = min(1.0, (1 + engagement.bit_length()) / 10)
            score += log_engagement * 0.7
            
        # Platform weighting
        platform = social_data.get("platform", "").lower()
        if platform == "twitter":
            score += 0.2
        elif platform == "reddit":
            score += 0.15
        elif platform == "telegram":
            score += 0.1
            
        # Author influence (simplified)
        # In a real system, this would check against a database of known influencers
        author = social_data.get("author", "").lower()
        if author in ["elonmusk", "vitalikbuterin", "cz_binance", "solomonmg"]:
            score += 0.3
            
        # Cap at 1.0
        return min(1.0, score)

class OnChainDataProcessor:
    """Processor for on-chain data inputs"""
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process on-chain data"""
        # Extract key fields
        tx_type = data.get("type", "unknown")
        signature = data.get("signature", data.get("txid", ""))
        
        # Normalize data format
        normalized_data = {
            "signature": signature,
            "type": tx_type,
            "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "blockchain": data.get("blockchain", "solana")
        }
        
        # Process based on transaction type
        if tx_type == "swap":
            normalized_data.update(self._process_swap(data))
        elif tx_type == "transfer":
            normalized_data.update(self._process_transfer(data))
        elif tx_type == "liquidity":
            normalized_data.update(self._process_liquidity(data))
        else:
            # Generic processing
            normalized_data["addresses"] = data.get("addresses", [])
            normalized_data["amount"] = data.get("amount")
            normalized_data["token"] = data.get("token")
            
        # Calculate significance score
        normalized_data["significance_score"] = self._calculate_significance(normalized_data)
        normalized_data["processed"] = True

        return normalized_data

    def _process_swap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process swap transaction data"""
        return {
            "addresses": data.get("addresses", []),
            "token_in": data.get("token_in"),
            "token_out": data.get("token_out"),
            "amount_in": data.get("amount_in"),
            "amount_out": data.get("amount_out"),
            "dex": data.get("dex", "unknown"),
            "slippage": data.get("slippage")
        }

    def _process_transfer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process transfer transaction data"""
        return {
            "addresses": data.get("addresses", []),
            "from_address": data.get("from_address"),
            "to_address": data.get("to_address"),
            "amount": data.get("amount"),
            "token": data.get("token"),
            "token_address": data.get("token_address")
        }

    def _process_liquidity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process liquidity transaction data"""
        return {
            "addresses": data.get("addresses", []),
            "pool_address": data.get("pool_address"),
            "action": data.get("action", "unknown"),  # add/remove
            "token_a": data.get("token_a"),
            "token_b": data.get("token_b"),
            "amount_a": data.get("amount_a"),
            "amount_b": data.get("amount_b"),
            "liquidity_amount": data.get("liquidity_amount")
        }

    def _calculate_significance(self, tx_data: Dict[str, Any]) -> float:
        """Calculate significance score for on-chain transaction"""
        score = 0.0

        # Transaction type weighting
        tx_type = tx_data.get("type", "unknown")
        if tx_type == "swap":
            score += 0.4  # Swaps are highly significant for trading
        elif tx_type == "liquidity":
            score += 0.3  # Liquidity changes affect market
        elif tx_type == "transfer":
            score += 0.2  # Transfers less significant but still relevant
        else:
            score += 0.1  # Unknown transactions get minimal score

        # Amount significance (if available)
        amount = tx_data.get("amount") or tx_data.get("amount_in") or tx_data.get("liquidity_amount")
        if amount:
            try:
                amount_float = float(amount)
                # Log scale for amount significance
                if amount_float > 0:
                    log_amount = min(0.3, (1 + int(amount_float).bit_length()) / 50)
                    score += log_amount
            except (ValueError, TypeError):
                pass

        # DEX/Platform weighting
        dex = tx_data.get("dex", "").lower()
        if dex in ["raydium", "jupiter", "orca"]:
            score += 0.2  # Major DEXes are more significant
        elif dex:
            score += 0.1  # Other known DEXes

        # Recent transactions are more significant
        timestamp = tx_data.get("timestamp")
        if timestamp:
            try:
                from datetime import datetime, timezone
                tx_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_hours = (now - tx_time).total_seconds() / 3600

                # More recent = more significant (decay over 24 hours)
                if age_hours < 24:
                    recency_score = max(0, (24 - age_hours) / 24 * 0.2)
                    score += recency_score
            except (ValueError, TypeError):
                pass

        # Cap at 1.0
        return min(1.0, score)

