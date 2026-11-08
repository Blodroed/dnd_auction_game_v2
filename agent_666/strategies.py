"""
Vulture Mode Strategies - Core bidding strategies for exploiting auction deadspace

This module implements the main Vulture Mode strategy and related strategic approaches
for auction bidding optimization.
"""

import statistics
import logging
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
from dice import average_roll

if TYPE_CHECKING:
    from data_handler import VultureDataHandler

logger = logging.getLogger(__name__)

class VultureMode:
    """
    Main Vulture Mode strategy implementation.
    
    Core Strategy: Bid Mean + Standard Deviation of other players' bids
    - Excludes agent's own bids from calculations to avoid bias
    - Focuses on exploiting deadspace in auction competition
    - Aggressive gold spending to prevent accumulation
    
    Parameters configurable from dashboard:
    - aggression_multiplier: How aggressive to bid (default 1.5)
    - max_bid_ratio: Maximum bid as ratio of available gold (default 0.8)
    - min_auctions_target: Minimum number of auctions to bid on (default 3)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        # Default configurable parameters
        default_config = {
            'aggression_multiplier': 1.2,  # Moderately aggressive for low-competition wins
            'max_bid_ratio': 0.4,  # Maximum total spending as ratio of gold (40%)
            'min_auctions_target': 8,  # Target ~8 auctions (low-competition ones)
            'deadspace_threshold': 1.5,  # Low competition threshold
            'high_value_threshold': 12.0,  # Decent value threshold (not too high)
            'min_vulture_score': 0.01,  # Very permissive (almost all auctions)
            'min_ev_threshold': 0.0,  # No EV filtering (0 = disabled)
            'max_auction_share': 0.35,  # Bid on up to 35% of auctions (~12 out of 35)
            'min_roi_vs_interest': 1.2,  # ROI only needs to beat interest by 20%
            'prefer_low_competition': True,  # Focus on auctions with fewer bidders
        }
        
        # Merge provided config with defaults
        self.config = default_config.copy()
        if config:
            self.config.update(config)
            logger.info(f"🦅 VultureMode initialized with custom config: {list(config.keys())}")
        
        self.bid_history = []
        self.performance_stats = {'wins': 0, 'total_bids': 0}

    def calculate_vulture_bids(self, agent_id: str, auctions: Dict, 
                              prev_auctions: Dict, budget: int, data_handler: Optional['VultureDataHandler'] = None, pool: Optional[int] = 0) -> Dict[str, int]:
        """
        Calculate vulture mode bids based on mean + std deviation strategy.
        
        Args:
            agent_id: Agent identifier 
            auctions: Current auctions available
            prev_auctions: Previous round auction results
            budget: Available budget for bidding
            
        Returns:
            Dictionary of auction_id -> bid_amount
        """
        if not auctions or budget <= 0:
            return {}
        
        # Ensure bids is always defined to avoid UnboundLocalError in some code paths
        bids = {}
        # Debugging: log data handler presence at debug-level
        logger.debug(f"Entering calculate_vulture_bids; data_handler is {'present' if data_handler is not None else 'None'}")
        # Calculate bidding statistics from previous auctions
        mean_bid, std_bid = self._calculate_bid_statistics(prev_auctions, agent_id)
        base_bid_amount = (mean_bid + std_bid) * self.config['aggression_multiplier']
        
        logger.info(f"🦅 Vulture Analysis: Mean={mean_bid:.2f}, Std={std_bid:.2f}, Base={base_bid_amount:.2f}")
        
        # If a data handler is supplied, use it to score and sort all auctions by vulture score
        if data_handler is not None:
            opportunities = []
            for auction_id, auction_data in auctions.items():
                die = auction_data.get('die', 6)
                num = auction_data.get('num', 1)
                bonus = auction_data.get('bonus', 0)
                try:
                    rec = data_handler.get_bidding_recommendation((die, num), bonus, budget)
                except Exception:
                    rec = None
                if not rec:
                    continue
                
                # NO FILTERING - include all auctions
                rec['auction_id'] = auction_id
                opportunities.append(rec)
            
            if not opportunities:
                logger.warning(f"🦅 No recommendations available, falling back to legacy")
                # Fall through to legacy mode
            else:
                # Sort by vulture score only (descending = best opportunities first)
                opportunities.sort(key=lambda x: -x.get('vulture_score', 0.0))
                
                logger.info(f"🦅 Sorted {len(opportunities)} auctions by vulture score")
                logger.info(f"🦅 Top 5 scores: {[f'{opp.get('vulture_score', 0):.2f}' for opp in opportunities[:5]]}")
                
                # Return simple bids with equal amounts - bid mode will handle allocation
                # This creates a dictionary in sorted order (Python 3.7+ preserves dict order)
                bids = {}
                base_bid = max(1, budget // max(len(opportunities), 1))  # Equal split as baseline
                
                for opp in opportunities:
                    bids[opp['auction_id']] = base_bid
                
                logger.info(f"🦅 Created {len(bids)} equal baseline bids of {base_bid} each")
                logger.info(f"🦅 Passing sorted bids to bid mode for allocation")
                
                if bids:
                    return bids
                
                # If something went wrong, fall through to legacy
                logger.debug("🦅 Vulture sorting failed, falling back to legacy")

        # Legacy path: use internal scoring if handler wasn't available or didn't return bids
        scored_auctions = self._score_auctions(auctions, base_bid_amount)
        # Use 90% of budget to ensure aggressive spending
        effective_budget = int(budget * self.config['max_bid_ratio'])
        bids = self._allocate_budget(scored_auctions, effective_budget, auctions)
        # If no bids were generated but there are positive-EV auctions, place a minimum bid
        if not bids and scored_auctions and budget > 0:
            top_auction_id, _, _ = scored_auctions[0]
            min_bid = max(1, min(int(budget * 0.1), budget))  # bid 10% of budget, at least 1
            bids = {top_auction_id: min_bid}
            logger.info(f"🦅 Vulture fallback minimal bid: {top_auction_id} -> {min_bid}")
        return bids
    
    def _calculate_bid_statistics(self, prev_auctions: Dict, agent_id: str) -> Tuple[float, float]:
        """Calculate mean and std deviation of OTHER players' bids (excluding our own)."""
        all_other_bids = []
        
        for auction_id, auction_data in prev_auctions.items():
            bids = auction_data.get('bids', [])
            for bid in bids:
                # Exclude our own bids to avoid bias
                if bid.get('agent', bid.get('agent_id', '')) != agent_id:
                    all_other_bids.append(bid['gold'])
        
        if len(all_other_bids) < 2:
            return 5.0, 2.0  # Default values for early game
        
        mean_bid = statistics.mean(all_other_bids)
        std_bid = statistics.stdev(all_other_bids) if len(all_other_bids) > 1 else 1.0
        
        return mean_bid, std_bid
    
    def _score_auctions(self, auctions: Dict, base_bid: float) -> List[Tuple[str, float, Dict]]:
        """Score auctions based on expected value and vulture opportunity."""
        scored_auctions = []
        
        for auction_id, auction_data in auctions.items():
            die = auction_data.get('die', 6)
            num = auction_data.get('num', 1)
            bonus = auction_data.get('bonus', 0)
            
            # Calculate expected value
            try:
                expected_value = average_roll(num, die, bonus)
            except:
                expected_value = num * ((die + 1) / 2) + bonus
            # Skip auctions with low expected value (configurable)
            if expected_value <= self.config.get('min_ev_threshold', 0.0):
                logger.debug(f"🦅 Skipping auction {auction_id} due to EV {expected_value} <= threshold {self.config.get('min_ev_threshold', 0.0)}")
                continue
            
            # Vulture scoring: higher EV vs lower expected competition
            competition_factor = 1.0  # Will be enhanced with historical data
            value_per_gold = expected_value / max(base_bid, 1)
            
            # Bonus for high-value auctions
            if expected_value > self.config['high_value_threshold']:
                value_per_gold *= 1.5
            
            vulture_score = value_per_gold * competition_factor
            scored_auctions.append((auction_id, vulture_score, auction_data))
        
        # Sort by vulture score (highest first)
        scored_auctions.sort(key=lambda x: x[1], reverse=True)
        return scored_auctions
    
    def _allocate_budget(self, scored_auctions: List, budget: int, auctions: Dict) -> Dict[str, int]:
        """Allocate budget across auctions with aggressive spending to prevent accumulation."""
        bids = {}
        
        # Use most of available budget (prevent gold accumulation)
        spending_budget = int(budget * self.config['max_bid_ratio'])
        remaining_budget = spending_budget
        
        # Ensure we bid on at least minimum number of auctions
        target_auctions = min(len(scored_auctions), 
                            max(self.config['min_auctions_target'], len(auctions) // 2))
        
        if target_auctions == 0:
            return {}
        
        # Distribute budget with preference for high-scoring auctions
        for i, (auction_id, score, auction_data) in enumerate(scored_auctions[:target_auctions]):
            if remaining_budget <= 0:
                break
            
            # Progressive bidding: more on better opportunities
            if i == 0:  # Best opportunity
                bid_amount = min(remaining_budget // 2, remaining_budget)
            elif i < target_auctions // 2:  # Good opportunities
                bid_amount = min(remaining_budget // 3, remaining_budget)
            else:  # Remaining opportunities
                avg_remaining = remaining_budget // (target_auctions - i)
                bid_amount = min(avg_remaining, remaining_budget)
            
            bid_amount = max(1, bid_amount)  # Minimum bid of 1
            
            if bid_amount <= remaining_budget:
                bids[auction_id] = bid_amount
                remaining_budget -= bid_amount
                
                logger.debug(f"🎯 Vulture bid: {auction_id} -> {bid_amount} gold (score: {score:.2f})")
        
        return bids
    
    def update_performance(self, won_auctions: List[str], bid_results: Dict):
        """Update strategy performance metrics."""
        self.performance_stats['total_bids'] += len(bid_results)
        self.performance_stats['wins'] += len(won_auctions)
        
        # Store for analysis
        self.bid_history.append({
            'bids': bid_results,
            'wins': won_auctions,
            'win_rate': len(won_auctions) / max(len(bid_results), 1)
        })
        
        # Keep only recent history
        if len(self.bid_history) > 50:
            self.bid_history.pop(0)
    
    def get_performance_stats(self) -> Dict:
        """Get current performance statistics."""
        total_bids = self.performance_stats['total_bids']
        wins = self.performance_stats['wins']
        win_rate = wins / max(total_bids, 1)
        
        return {
            'total_bids': total_bids,
            'wins': wins,
            'win_rate': win_rate,
            'recent_performance': self.bid_history[-10:] if self.bid_history else [],
            'config': self.config.copy()
        }
    
    def update_config(self, new_config: Dict):
        """Update strategy configuration (for dashboard integration)."""
        self.config.update(new_config)
        logger.info(f"🦅 Vulture config updated: {new_config}")

# Legacy compatibility classes
class StartMethod:
    """Base class for start methods (legacy compatibility)."""
    def __init__(self, **kwargs):
        self.params = kwargs

    def apply(self, agent_state, bank_state, current_round, total_rounds):
        return 1.0  # Default multiplier

class BiddingStrategy:
    """Base class for bidding strategies (legacy compatibility)."""
    def __init__(self, **kwargs):
        self.params = kwargs

    def filter(self, auctions, agent_state, bank_state, **kwargs):
        return list(auctions.keys())  # Return all auction IDs by default