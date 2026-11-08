"""
Vulture Mode Storage - In-Memory Performance Storage

This module handles data storage for Vulture Mode with focus on performance.
Designed for in-memory operations during gameplay with optional persistence.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from collections import defaultdict, deque
import time

logger = logging.getLogger(__name__)

class VultureStorage:
    """
    High-performance storage system for Vulture Mode.
    
    Features:
    - In-memory first for performance
    - Ring buffers for automatic memory management
    - Optional background persistence
    - Fast data retrieval for bidding decisions
    """
    
    def __init__(self, config: Optional[Dict] = None, memory_limit: int = 5000):
        # Default configuration
        default_config = {
            'max_memory_rounds': 5000,
            'auto_save_interval': 10,
            'enable_persistence': True,
            'backup_logs': True,
            'compression_enabled': False
        }
        
        # Merge provided config with defaults
        self.config = default_config.copy()
        if config:
            self.config.update(config)
            memory_limit = config.get('max_memory_rounds', memory_limit)
            logger.info(f"🗄️ AgentStorage initialized with custom config: {list(config.keys())}")
        
        # In-memory storage configuration
        self.memory_limit = memory_limit
        
        # Ring buffers for different data types
        self.round_data = deque(maxlen=memory_limit)
        self.bid_results = deque(maxlen=memory_limit)
        self.performance_metrics = deque(maxlen=memory_limit)
        
        # Current state cache
        self.current_state = {}
        self.vulture_insights = {}
        
        # Statistics
        self.operations_count = 0
        self.storage_stats = defaultdict(int)
        
        # Optional persistence
        self.storage_dir = Path("data")
        self.storage_dir.mkdir(exist_ok=True)
        
        logger.info("🔥 Agent storage initialized")
    
    def store_round_data(self, round_num: int, data: Dict) -> None:
        """Store round data in memory for fast access."""
        round_entry = {
            'round': round_num,
            'timestamp': time.time(),
            'data': data
        }
        
        self.round_data.append(round_entry)
        self.operations_count += 1
        self.storage_stats['rounds_stored'] += 1
        
        # Update current state
        self.current_state.update({
            'last_round': round_num,
            'last_update': time.time()
        })
    
    def store_bid_results(self, round_num: int, bids: Dict[str, int], 
                         results: Dict) -> None:
        """Store bidding results for analysis."""
        bid_entry = {
            'round': round_num,
            'timestamp': time.time(),
            'bids': bids,
            'results': results
        }
        
        self.bid_results.append(bid_entry)
        self.storage_stats['bid_results_stored'] += 1
    
    def store_performance_data(self, round_num: int, metrics: Dict) -> None:
        """Store performance metrics."""
        perf_entry = {
            'round': round_num,
            'timestamp': time.time(),
            'metrics': metrics
        }
        
        self.performance_metrics.append(perf_entry)
        self.storage_stats['performance_entries'] += 1
    
    def get_recent_rounds(self, count: int = 10) -> List[Dict]:
        """Get recent round data for analysis."""
        recent_data = list(self.round_data)[-count:]
        return [entry['data'] for entry in recent_data]
    
    def get_recent_bids(self, count: int = 20) -> List[Dict]:
        """Get recent bid results for pattern analysis."""
        recent_bids = list(self.bid_results)[-count:]
        return recent_bids
    
    def get_performance_history(self, count: int = 50) -> List[Dict]:
        """Get performance history for trend analysis."""
        recent_perf = list(self.performance_metrics)[-count:]
        return [entry['metrics'] for entry in recent_perf]
    
    def store_vulture_insight(self, insight_key: str, insight_data: Dict) -> None:
        """Store vulture-specific insights and patterns."""
        self.vulture_insights[insight_key] = {
            'timestamp': time.time(),
            'data': insight_data
        }
        
        # Limit insights storage
        if len(self.vulture_insights) > 1000:
            # Remove oldest insights
            oldest_key = min(self.vulture_insights.keys(), 
                           key=lambda k: self.vulture_insights[k]['timestamp'])
            del self.vulture_insights[oldest_key]
    
    def get_vulture_insights(self, pattern: Optional[str] = None) -> Dict:
        """Retrieve vulture insights, optionally filtered by pattern."""
        if pattern:
            return {k: v for k, v in self.vulture_insights.items() if pattern in k}
        return self.vulture_insights.copy()
    
    def get_memory_usage(self) -> Dict:
        """Get current memory usage statistics."""
        return {
            'round_data_count': len(self.round_data),
            'bid_results_count': len(self.bid_results),
            'performance_data_count': len(self.performance_metrics),
            'vulture_insights_count': len(self.vulture_insights),
            'total_operations': self.operations_count,
            'memory_limit': self.memory_limit,
            'stats': dict(self.storage_stats)
        }
    
    def clear_old_data(self, keep_recent: int = 100) -> None:
        """Clear old data while keeping recent entries for performance."""
        # Ring buffers automatically manage size, but we can force cleanup
        if len(self.round_data) > keep_recent:
            recent_rounds = list(self.round_data)[-keep_recent:]
            self.round_data.clear()
            self.round_data.extend(recent_rounds)
        
        # Clear old insights
        current_time = time.time()
        old_insights = [
            key for key, value in self.vulture_insights.items()
            if current_time - value['timestamp'] > 3600  # 1 hour old
        ]
        
        for key in old_insights:
            del self.vulture_insights[key]
        
        logger.info(f"🧹 Vulture storage cleaned, keeping {keep_recent} recent entries")
    
    def export_session_data(self) -> Dict:
        """Export current session data for analysis."""
        return {
            'round_data': [entry for entry in self.round_data],
            'bid_results': [entry for entry in self.bid_results], 
            'performance_metrics': [entry for entry in self.performance_metrics],
            'vulture_insights': self.vulture_insights.copy(),
            'session_stats': self.get_memory_usage(),
            'export_timestamp': time.time()
        }
    
    def save_session_summary(self, filename: Optional[str] = None) -> bool:
        """Save session summary to disk (optional background operation)."""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"vulture_session_{timestamp}.json"
            
            filepath = self.storage_dir / filename
            session_data = self.export_session_data()
            
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"💾 Vulture session saved: {filename}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
            return False