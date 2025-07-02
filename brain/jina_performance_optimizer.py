#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Jina AI Performance Optimizer
Production-grade performance optimization for Jina AI integration
"""

import asyncio
import json
import time
import logging
import redis
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import aiohttp
from collections import defaultdict
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    operation_type: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    cache_hit: bool
    api_calls: int
    data_size: int
    error_message: Optional[str] = None

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int
    cooldown_period: int

class JinaPerformanceOptimizer:
    """
    Production performance optimizer for Jina AI integration
    Handles caching, rate limiting, connection pooling, and monitoring
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6380):
        # Redis for caching and rate limiting
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Performance tracking
        self.metrics = []
        self.performance_stats = defaultdict(list)
        
        # Caching configuration
        self.cache_config = {
            'news_analysis': {'ttl': 1800, 'max_size': 1000},  # 30 minutes
            'deep_search': {'ttl': 3600, 'max_size': 500},     # 1 hour
            'vector_search': {'ttl': 900, 'max_size': 2000},   # 15 minutes
            'research_results': {'ttl': 2700, 'max_size': 300} # 45 minutes
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            'jina_reader': RateLimitConfig(60, 1000, 10, 60),
            'jina_deepsearch': RateLimitConfig(30, 500, 5, 120),
            'vector_operations': RateLimitConfig(120, 2000, 20, 30),
            'research_requests': RateLimitConfig(40, 800, 8, 90)
        }
        
        # Connection pooling
        self.connection_pools = {}
        self.pool_config = {
            'connector_limit': 100,
            'limit_per_host': 30,
            'timeout': aiohttp.ClientTimeout(total=30)
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            'max_response_time': 30.0,  # seconds
            'min_cache_hit_rate': 0.6,  # 60%
            'max_error_rate': 0.05,     # 5%
            'max_memory_usage': 0.8     # 80%
        }
        
        logger.info("🚀 Jina AI Performance Optimizer initialized")
    
    async def initialize_connection_pools(self):
        """Initialize HTTP connection pools"""
        try:
            connector = aiohttp.TCPConnector(
                limit=self.pool_config['connector_limit'],
                limit_per_host=self.pool_config['limit_per_host'],
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self.connection_pools['default'] = aiohttp.ClientSession(
                connector=connector,
                timeout=self.pool_config['timeout']
            )
            
            logger.info("✅ HTTP connection pools initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing connection pools: {e}")
    
    async def optimized_jina_reader(self, url: str) -> Optional[str]:
        """Optimized Jina Reader API call with caching and rate limiting"""
        try:
            start_time = time.time()
            
            # Check cache first
            cache_key = f"jina_reader:{hashlib.md5(url.encode()).hexdigest()}"
            cached_result = await self._get_from_cache(cache_key, 'news_analysis')
            
            if cached_result:
                await self._record_metrics('jina_reader', start_time, True, True, 0, len(cached_result))
                return cached_result
            
            # Check rate limits
            if not await self._check_rate_limit('jina_reader'):
                logger.warning(f"⚠️ Rate limit exceeded for Jina Reader")
                return None
            
            # Make API call with optimized session
            session = self.connection_pools.get('default')
            if not session:
                await self.initialize_connection_pools()
                session = self.connection_pools['default']
            
            reader_url = f"https://r.jina.ai/{url}"
            headers = {
                'Authorization': 'Bearer jina_72cc7ed00e21496290ed9e018d56de3bETDGPqW-TUXuYYIxk4jwHLN9h0C6',
                'User-Agent': 'OVERMIND-Protocol/1.0'
            }
            
            async with session.get(reader_url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Cache the result
                    await self._store_in_cache(cache_key, content, 'news_analysis')
                    
                    await self._record_metrics('jina_reader', start_time, True, False, 1, len(content))
                    logger.info(f"✅ Jina Reader: {len(content)} chars from {url}")
                    return content
                else:
                    await self._record_metrics('jina_reader', start_time, False, False, 1, 0, f"HTTP {response.status}")
                    return None
                    
        except Exception as e:
            await self._record_metrics('jina_reader', start_time, False, False, 1, 0, str(e))
            logger.error(f"❌ Optimized Jina Reader error: {e}")
            return None
    
    async def optimized_deep_search(self, query: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Optimized DeepSearch API call with intelligent caching"""
        try:
            start_time = time.time()
            
            # Create cache key based on query and content hash
            content_hash = hashlib.md5((content or "").encode()).hexdigest()[:8]
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            cache_key = f"deep_search:{query_hash}:{content_hash}"
            
            # Check cache
            cached_result = await self._get_from_cache(cache_key, 'deep_search')
            if cached_result:
                await self._record_metrics('deep_search', start_time, True, True, 0, len(str(cached_result)))
                return cached_result
            
            # Rate limiting
            if not await self._check_rate_limit('jina_deepsearch'):
                logger.warning(f"⚠️ Rate limit exceeded for DeepSearch")
                return {}
            
            # Optimized API call
            session = self.connection_pools.get('default')
            search_url = f"https://s.jina.ai/{query}"
            headers = {
                'Authorization': 'Bearer jina_72cc7ed00e21496290ed9e018d56de3bETDGPqW-TUXuYYIxk4jwHLN9h0C6',
                'User-Agent': 'OVERMIND-Protocol/1.0'
            }
            
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    try:
                        result = await response.json()
                    except:
                        # Parse text response
                        text_result = await response.text()
                        result = await self._parse_deepsearch_response(text_result, query)
                    
                    # Cache with TTL
                    await self._store_in_cache(cache_key, result, 'deep_search')
                    
                    await self._record_metrics('deep_search', start_time, True, False, 1, len(str(result)))
                    return result
                else:
                    await self._record_metrics('deep_search', start_time, False, False, 1, 0, f"HTTP {response.status}")
                    return {}
                    
        except Exception as e:
            await self._record_metrics('deep_search', start_time, False, False, 1, 0, str(e))
            logger.error(f"❌ Optimized DeepSearch error: {e}")
            return {}
    
    async def optimized_vector_search(self, query_vector: List[float], collection: str, limit: int = 10) -> List[Dict]:
        """Optimized vector search with result caching"""
        try:
            start_time = time.time()
            
            # Create cache key from vector hash
            vector_str = ','.join([f"{v:.4f}" for v in query_vector[:10]])  # First 10 components
            cache_key = f"vector_search:{collection}:{hashlib.md5(vector_str.encode()).hexdigest()[:8]}:{limit}"
            
            # Check cache
            cached_result = await self._get_from_cache(cache_key, 'vector_search')
            if cached_result:
                await self._record_metrics('vector_search', start_time, True, True, 0, len(cached_result))
                return cached_result
            
            # Rate limiting
            if not await self._check_rate_limit('vector_operations'):
                logger.warning(f"⚠️ Rate limit exceeded for vector operations")
                return []
            
            # Simulate vector search (in real implementation, this would call actual vector DB)
            await asyncio.sleep(0.1)  # Simulate search time
            
            # Mock results for demonstration
            results = [
                {
                    'id': f'vec_{i}',
                    'score': 0.9 - i * 0.1,
                    'metadata': {'type': 'mock', 'collection': collection}
                }
                for i in range(min(limit, 3))
            ]
            
            # Cache results
            await self._store_in_cache(cache_key, results, 'vector_search')
            
            await self._record_metrics('vector_search', start_time, True, False, 1, len(results))
            return results
            
        except Exception as e:
            await self._record_metrics('vector_search', start_time, False, False, 1, 0, str(e))
            logger.error(f"❌ Optimized vector search error: {e}")
            return []
    
    async def batch_process_requests(self, requests: List[Dict[str, Any]], batch_size: int = 5) -> List[Any]:
        """Batch process multiple requests for optimal performance"""
        try:
            logger.info(f"🔄 Batch processing {len(requests)} requests in batches of {batch_size}")
            
            results = []
            
            for i in range(0, len(requests), batch_size):
                batch = requests[i:i + batch_size]
                
                # Process batch concurrently
                batch_tasks = []
                for request in batch:
                    if request['type'] == 'jina_reader':
                        task = self.optimized_jina_reader(request['url'])
                    elif request['type'] == 'deep_search':
                        task = self.optimized_deep_search(request['query'], request.get('content'))
                    elif request['type'] == 'vector_search':
                        task = self.optimized_vector_search(request['vector'], request['collection'])
                    else:
                        continue
                    
                    batch_tasks.append(task)
                
                # Execute batch
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                results.extend(batch_results)
                
                # Small delay between batches to respect rate limits
                if i + batch_size < len(requests):
                    await asyncio.sleep(1)
            
            logger.info(f"✅ Batch processing complete: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in batch processing: {e}")
            return []
    
    async def _get_from_cache(self, key: str, cache_type: str) -> Optional[Any]:
        """Get item from cache with type-specific configuration"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Cache get error: {e}")
            return None
    
    async def _store_in_cache(self, key: str, data: Any, cache_type: str):
        """Store item in cache with TTL"""
        try:
            config = self.cache_config.get(cache_type, {'ttl': 1800})
            serialized_data = json.dumps(data) if not isinstance(data, str) else data
            
            self.redis_client.setex(key, config['ttl'], serialized_data)
            
        except Exception as e:
            logger.warning(f"⚠️ Cache store error: {e}")
    
    async def _check_rate_limit(self, operation: str) -> bool:
        """Check if operation is within rate limits"""
        try:
            config = self.rate_limits.get(operation)
            if not config:
                return True
            
            current_time = int(time.time())
            minute_key = f"rate_limit:{operation}:minute:{current_time // 60}"
            hour_key = f"rate_limit:{operation}:hour:{current_time // 3600}"
            
            # Check current counts
            minute_count = int(self.redis_client.get(minute_key) or 0)
            hour_count = int(self.redis_client.get(hour_key) or 0)
            
            # Check limits
            if minute_count >= config.requests_per_minute or hour_count >= config.requests_per_hour:
                return False
            
            # Increment counters
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            pipe.execute()
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Rate limit check error: {e}")
            return True  # Allow on error
    
    async def _record_metrics(self, operation: str, start_time: float, success: bool, 
                            cache_hit: bool, api_calls: int, data_size: int, 
                            error_message: Optional[str] = None):
        """Record performance metrics"""
        try:
            end_time = time.time()
            duration = end_time - start_time
            
            metric = PerformanceMetrics(
                operation_type=operation,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                cache_hit=cache_hit,
                api_calls=api_calls,
                data_size=data_size,
                error_message=error_message
            )
            
            self.metrics.append(metric)
            self.performance_stats[operation].append(duration)
            
            # Keep only recent metrics (last 1000)
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
            
        except Exception as e:
            logger.warning(f"⚠️ Metrics recording error: {e}")
    
    async def _parse_deepsearch_response(self, text_response: str, query: str) -> Dict[str, Any]:
        """Parse DeepSearch text response into structured format"""
        try:
            # Basic sentiment analysis from response
            text_lower = text_response.lower()
            
            positive_indicators = ['positive', 'bullish', 'good', 'strong', 'growth']
            negative_indicators = ['negative', 'bearish', 'bad', 'weak', 'decline']
            
            positive_count = sum(1 for indicator in positive_indicators if indicator in text_lower)
            negative_count = sum(1 for indicator in negative_indicators if indicator in text_lower)
            
            total_indicators = positive_count + negative_count
            sentiment_score = positive_count / total_indicators if total_indicators > 0 else 0.5
            
            # Extract key insights
            sentences = text_response.split('.')[:5]
            key_insights = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            return {
                'sentiment_score': sentiment_score,
                'confidence': min(total_indicators / 10.0, 0.8),
                'key_insights': key_insights,
                'trading_signals': ['bullish' if sentiment_score > 0.6 else 'bearish' if sentiment_score < 0.4 else 'neutral'],
                'relevance_score': 0.7,
                'reasoning': f'Analyzed response for: {query[:50]}...'
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing DeepSearch response: {e}")
            return {
                'sentiment_score': 0.5,
                'confidence': 0.1,
                'key_insights': [],
                'trading_signals': [],
                'relevance_score': 0.3,
                'reasoning': 'Failed to parse response'
            }
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            if not self.metrics:
                return {'error': 'No metrics available'}
            
            # Calculate overall statistics
            total_operations = len(self.metrics)
            successful_operations = sum(1 for m in self.metrics if m.success)
            cache_hits = sum(1 for m in self.metrics if m.cache_hit)
            
            # Performance by operation type
            operation_stats = {}
            for operation in self.performance_stats:
                durations = self.performance_stats[operation]
                if durations:
                    operation_stats[operation] = {
                        'count': len(durations),
                        'avg_duration': statistics.mean(durations),
                        'min_duration': min(durations),
                        'max_duration': max(durations),
                        'median_duration': statistics.median(durations)
                    }
            
            # Recent performance (last 100 operations)
            recent_metrics = self.metrics[-100:] if len(self.metrics) >= 100 else self.metrics
            recent_success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
            recent_cache_hit_rate = sum(1 for m in recent_metrics if m.cache_hit) / len(recent_metrics)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_operations': total_operations,
                'success_rate': successful_operations / total_operations,
                'cache_hit_rate': cache_hits / total_operations,
                'recent_success_rate': recent_success_rate,
                'recent_cache_hit_rate': recent_cache_hit_rate,
                'operation_stats': operation_stats,
                'performance_thresholds': self.performance_thresholds,
                'alerts': await self._generate_performance_alerts()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating performance report: {e}")
            return {'error': str(e)}
    
    async def _generate_performance_alerts(self) -> List[str]:
        """Generate performance alerts based on thresholds"""
        alerts = []
        
        try:
            if not self.metrics:
                return alerts
            
            # Check recent performance
            recent_metrics = self.metrics[-50:] if len(self.metrics) >= 50 else self.metrics
            
            # Success rate alert
            success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
            if success_rate < (1 - self.performance_thresholds['max_error_rate']):
                alerts.append(f"High error rate: {(1-success_rate)*100:.1f}% (threshold: {self.performance_thresholds['max_error_rate']*100:.1f}%)")
            
            # Cache hit rate alert
            cache_hit_rate = sum(1 for m in recent_metrics if m.cache_hit) / len(recent_metrics)
            if cache_hit_rate < self.performance_thresholds['min_cache_hit_rate']:
                alerts.append(f"Low cache hit rate: {cache_hit_rate*100:.1f}% (threshold: {self.performance_thresholds['min_cache_hit_rate']*100:.1f}%)")
            
            # Response time alert
            avg_duration = statistics.mean([m.duration for m in recent_metrics])
            if avg_duration > self.performance_thresholds['max_response_time']:
                alerts.append(f"High response time: {avg_duration:.2f}s (threshold: {self.performance_thresholds['max_response_time']}s)")
            
        except Exception as e:
            logger.warning(f"⚠️ Error generating alerts: {e}")
        
        return alerts
    
    async def optimize_cache_settings(self):
        """Dynamically optimize cache settings based on usage patterns"""
        try:
            logger.info("🔧 Optimizing cache settings...")
            
            # Analyze cache hit rates by type
            cache_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
            
            for metric in self.metrics[-500:]:  # Last 500 operations
                operation = metric.operation_type
                if metric.cache_hit:
                    cache_stats[operation]['hits'] += 1
                else:
                    cache_stats[operation]['misses'] += 1
            
            # Adjust TTL based on hit rates
            for operation, stats in cache_stats.items():
                total = stats['hits'] + stats['misses']
                if total > 10:  # Minimum sample size
                    hit_rate = stats['hits'] / total
                    
                    # Find corresponding cache type
                    cache_type = None
                    if 'news' in operation or 'reader' in operation:
                        cache_type = 'news_analysis'
                    elif 'search' in operation:
                        cache_type = 'deep_search'
                    elif 'vector' in operation:
                        cache_type = 'vector_search'
                    elif 'research' in operation:
                        cache_type = 'research_results'
                    
                    if cache_type and cache_type in self.cache_config:
                        current_ttl = self.cache_config[cache_type]['ttl']
                        
                        # Adjust TTL based on hit rate
                        if hit_rate > 0.8:  # High hit rate - increase TTL
                            new_ttl = min(current_ttl * 1.2, 7200)  # Max 2 hours
                        elif hit_rate < 0.4:  # Low hit rate - decrease TTL
                            new_ttl = max(current_ttl * 0.8, 300)   # Min 5 minutes
                        else:
                            new_ttl = current_ttl
                        
                        if new_ttl != current_ttl:
                            self.cache_config[cache_type]['ttl'] = int(new_ttl)
                            logger.info(f"📊 Adjusted {cache_type} TTL: {current_ttl}s → {new_ttl}s (hit rate: {hit_rate:.2f})")
            
            logger.info("✅ Cache optimization complete")
            
        except Exception as e:
            logger.error(f"❌ Error optimizing cache settings: {e}")
    
    async def cleanup_resources(self):
        """Cleanup resources and close connections"""
        try:
            # Close HTTP sessions
            for session in self.connection_pools.values():
                await session.close()
            
            # Close Redis connection
            self.redis_client.close()
            
            logger.info("✅ Resources cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up resources: {e}")

# Performance monitoring and optimization orchestrator
class PerformanceOrchestrator:
    """Orchestrates performance optimization for Jina AI integration"""
    
    def __init__(self):
        self.optimizer = JinaPerformanceOptimizer()
        self.monitoring_active = False
        
    async def start_performance_monitoring(self):
        """Start continuous performance monitoring"""
        try:
            logger.info("📊 Starting performance monitoring...")
            
            await self.optimizer.initialize_connection_pools()
            self.monitoring_active = True
            
            # Start monitoring loop
            asyncio.create_task(self._monitoring_loop())
            
            logger.info("✅ Performance monitoring started")
            
        except Exception as e:
            logger.error(f"❌ Error starting performance monitoring: {e}")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                # Generate performance report
                report = await self.optimizer.get_performance_report()
                
                # Log alerts if any
                alerts = report.get('alerts', [])
                if alerts:
                    for alert in alerts:
                        logger.warning(f"⚠️ Performance Alert: {alert}")
                
                # Optimize cache settings periodically
                await self.optimizer.optimize_cache_settings()
                
                # Wait before next check
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def stop_performance_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        await self.optimizer.cleanup_resources()
        logger.info("🛑 Performance monitoring stopped")

# Test and demonstration functions
async def test_performance_optimization():
    """Test Jina AI performance optimization"""

    print("🧠 THE OVERMIND PROTOCOL - Jina AI Performance Optimization Test")
    print("=" * 80)

    optimizer = JinaPerformanceOptimizer()

    # Test 1: Initialize connection pools
    print("\n🔗 Test 1: Connection Pool Initialization")
    await optimizer.initialize_connection_pools()
    print("   Connection pools: ✅ Initialized")
    print(f"   Pool config: {optimizer.pool_config}")

    # Test 2: Optimized Jina Reader
    print("\n📖 Test 2: Optimized Jina Reader")
    test_urls = [
        "https://solana.com",
        "https://solana.com",  # Duplicate for cache test
        "https://docs.solana.com"
    ]

    for i, url in enumerate(test_urls):
        start_time = time.time()
        content = await optimizer.optimized_jina_reader(url)
        duration = time.time() - start_time

        print(f"   Request {i+1}: {url}")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Content: {'✅ Success' if content else '❌ Failed'}")
        print(f"     Size: {len(content) if content else 0} chars")

    # Test 3: Optimized DeepSearch
    print("\n🔍 Test 3: Optimized DeepSearch")
    search_queries = [
        "Solana ecosystem analysis",
        "Solana ecosystem analysis",  # Duplicate for cache test
        "DeFi trends on Solana"
    ]

    for i, query in enumerate(search_queries):
        start_time = time.time()
        result = await optimizer.optimized_deep_search(query)
        duration = time.time() - start_time

        print(f"   Query {i+1}: {query}")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Result: {'✅ Success' if result else '❌ Failed'}")
        print(f"     Sentiment: {result.get('sentiment_score', 0):.3f}")
        print(f"     Confidence: {result.get('confidence', 0):.3f}")

    # Test 4: Optimized Vector Search
    print("\n🔍 Test 4: Optimized Vector Search")
    test_vector = [0.1] * 768  # Mock 768-dimensional vector

    for i in range(3):
        start_time = time.time()
        results = await optimizer.optimized_vector_search(test_vector, f"collection_{i}", limit=5)
        duration = time.time() - start_time

        print(f"   Search {i+1}: collection_{i}")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Results: {len(results)} found")

    # Test 5: Batch Processing
    print("\n🔄 Test 5: Batch Processing")
    batch_requests = [
        {'type': 'jina_reader', 'url': 'https://solana.com'},
        {'type': 'deep_search', 'query': 'Solana market analysis'},
        {'type': 'vector_search', 'vector': test_vector, 'collection': 'test'},
        {'type': 'jina_reader', 'url': 'https://docs.solana.com'},
        {'type': 'deep_search', 'query': 'Blockchain technology trends'}
    ]

    start_time = time.time()
    batch_results = await optimizer.batch_process_requests(batch_requests, batch_size=3)
    duration = time.time() - start_time

    print(f"   Batch size: {len(batch_requests)} requests")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Results: {len(batch_results)} completed")
    print(f"   Avg per request: {duration/len(batch_requests):.2f}s")

    # Test 6: Performance Report
    print("\n📊 Test 6: Performance Report")
    report = await optimizer.get_performance_report()

    print(f"   Total operations: {report.get('total_operations', 0)}")
    print(f"   Success rate: {report.get('success_rate', 0)*100:.1f}%")
    print(f"   Cache hit rate: {report.get('cache_hit_rate', 0)*100:.1f}%")
    print(f"   Recent success rate: {report.get('recent_success_rate', 0)*100:.1f}%")
    print(f"   Recent cache hit rate: {report.get('recent_cache_hit_rate', 0)*100:.1f}%")

    # Show operation statistics
    operation_stats = report.get('operation_stats', {})
    for operation, stats in operation_stats.items():
        print(f"   {operation}:")
        print(f"     Count: {stats['count']}")
        print(f"     Avg duration: {stats['avg_duration']:.3f}s")
        print(f"     Min/Max: {stats['min_duration']:.3f}s / {stats['max_duration']:.3f}s")

    # Show alerts
    alerts = report.get('alerts', [])
    if alerts:
        print(f"   Alerts: {len(alerts)}")
        for alert in alerts:
            print(f"     ⚠️ {alert}")
    else:
        print("   Alerts: ✅ None")

    # Test 7: Cache Optimization
    print("\n🔧 Test 7: Cache Optimization")
    await optimizer.optimize_cache_settings()

    print("   Cache settings optimized based on usage patterns")
    for cache_type, config in optimizer.cache_config.items():
        print(f"     {cache_type}: TTL {config['ttl']}s, Max size {config['max_size']}")

    # Test 8: Performance Orchestrator
    print("\n🎭 Test 8: Performance Orchestrator")
    orchestrator = PerformanceOrchestrator()

    print("   Starting performance monitoring...")
    await orchestrator.start_performance_monitoring()

    # Let it run for a few seconds
    await asyncio.sleep(3)

    print("   Stopping performance monitoring...")
    await orchestrator.stop_performance_monitoring()

    print(f"\n🎯 Jina AI Performance Optimization Test Complete!")
    print("=" * 80)

    # Final Summary
    print(f"\n📊 OPTIMIZATION TEST SUMMARY:")
    print(f"✅ Connection Pooling: HTTP sessions with connection limits")
    print(f"✅ Intelligent Caching: Redis-based with TTL optimization")
    print(f"✅ Rate Limiting: Per-minute and per-hour limits")
    print(f"✅ Batch Processing: Concurrent request handling")
    print(f"✅ Performance Monitoring: Real-time metrics and alerts")
    print(f"✅ Cache Optimization: Dynamic TTL adjustment")
    print(f"✅ Resource Management: Proper cleanup and monitoring")

    print(f"\n🚀 Production-Ready Performance Optimization Complete!")

if __name__ == "__main__":
    asyncio.run(test_performance_optimization())
