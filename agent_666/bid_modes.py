"""
Vulture Mode Bid Modes - Different bidding distribution strategies

This module handles how bids are distributed across selected auctions.
All parameters are designed to be configurable from the dashboard.
"""

import logging
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class BidModeType(Enum):
    """Available bid distribution modes."""
    ALL_OR_NOTHING = "all_or_nothing"  # Focus on few high-value auctions
    EVEN_STEVEN = "even_steven"  # Equal distribution across auctions
    MEAN_GREEN = "mean_green"  # Mean + std deviation based bidding
    HIGHER_LOWER = "higher_lower"  # Weighted by auction value
    AGGRESSIVE_SPREAD = "aggressive_spend"  # Spend aggressively to prevent accumulation

class BidModeSelector:
    """
    Manages different bid distribution modes for Vulture strategy.
    
    Configurable parameters (dashboard controllable):
    - current_mode: Active bid mode
    - focus_ratio: Concentration of bids (0.1-1.0)  
    - min_bid_amount: Minimum bid per auction
    - max_single_bid_ratio: Maximum single bid as % of budget
    """
    
    def __init__(self, config: Optional[Dict] = None):
        # Default configurable parameters
        default_config = {
            'current_mode': BidModeType.MEAN_GREEN,
            'focus_ratio': 0.7,  # How much to focus on top auctions
            'min_bid_amount': 1,
            'max_single_bid_ratio': 0.4,  # Max 40% of budget on single auction
            'spread_factor': 0.8,  # How much of budget to spend (prevent accumulation)
        }
        
        # Merge provided config with defaults
        self.config = default_config.copy()
        if config:
            self.config.update(config)
            logger.info(f"🎯 BidModeSelector initialized with custom config: {list(config.keys())}")
            
            # Handle string mode conversion
            if isinstance(config.get('current_mode'), str):
                mode_name = config['current_mode']
                try:
                    self.config['current_mode'] = BidModeType[mode_name]
                except KeyError:
                    logger.warning(f"⚠️ Invalid bid mode '{mode_name}', using AGGRESSIVE_SPREAD")
                    self.config['current_mode'] = BidModeType.AGGRESSIVE_SPREAD
    
    def apply_bid_mode(self, strategy_bids: Dict[str, int], 
                      available_gold: int, auctions: Dict) -> Dict[str, int]:
        """
        Apply selected bid mode to strategy recommendations.
        
        Args:
            strategy_bids: Raw bids from strategy
            available_gold: Total available gold
            auctions: Current auction details
            
        Returns:
            Adjusted bids based on selected mode
        """
        if not strategy_bids:
            return {}
        
        mode = self.config['current_mode']
        
        if mode == BidModeType.ALL_OR_NOTHING:
            return self._all_or_nothing_mode(strategy_bids, available_gold)
        elif mode == BidModeType.EVEN_STEVEN:
            return self._even_steven_mode(strategy_bids, available_gold)
        elif mode == BidModeType.MEAN_GREEN:
            return self._mean_green_mode(strategy_bids, available_gold)
        elif mode == BidModeType.HIGHER_LOWER:
            return self._higher_lower_mode(strategy_bids, available_gold, auctions)
        elif mode == BidModeType.AGGRESSIVE_SPREAD:
            return self._aggressive_spread_mode(strategy_bids, available_gold)
        else:
            return strategy_bids
    
    def _all_or_nothing_mode(self, bids: Dict[str, int], budget: int) -> Dict[str, int]:
        """Focus on 1-3 highest value auctions with concentrated bidding."""
        if not bids:
            return {}
        
        # Sort by bid amount (proxy for value)
        sorted_bids = sorted(bids.items(), key=lambda x: x[1], reverse=True)
        
        # Focus on top auctions based on focus_ratio
        focus_count = max(1, int(len(sorted_bids) * (1 - self.config['focus_ratio']) + 1))
        selected_auctions = sorted_bids[:focus_count]
        
        # Distribute budget across selected auctions
        total_budget = budget  # Budget is already the phase-adjusted spending amount
        adjusted_bids = {}
        
        for i, (auction_id, original_bid) in enumerate(selected_auctions):
            if i == 0:  # Best auction gets most
                bid_amount = min(total_budget // 2, 
                               int(budget * self.config['max_single_bid_ratio']))
            else:  # Remaining auctions share the rest
                remaining_budget = total_budget - sum(adjusted_bids.values())
                remaining_auctions = len(selected_auctions) - i
                bid_amount = remaining_budget // remaining_auctions
            
            adjusted_bids[auction_id] = max(self.config['min_bid_amount'], bid_amount)
        
        logger.info(f"🎯 All-or-Nothing: {len(adjusted_bids)} focused bids")
        return adjusted_bids
    
    def _even_steven_mode(self, bids: Dict[str, int], budget: int) -> Dict[str, int]:
        """Distribute budget evenly across all selected auctions."""
        if not bids:
            return {}
        
        total_budget = budget  # Budget is already the phase-adjusted spending amount
        bid_per_auction = max(self.config['min_bid_amount'], 
                             total_budget // len(bids))
        
        adjusted_bids = {}
        for auction_id in bids.keys():
            adjusted_bids[auction_id] = bid_per_auction
        
        logger.info(f"📊 Even Steven: {len(adjusted_bids)} equal bids of {bid_per_auction}")
        return adjusted_bids
    
    def _mean_green_mode(self, bids: Dict[str, int], budget: int) -> Dict[str, int]:
        """
        Bid based on mean + standard deviation principle (core Vulture Mode).
        
        Assumes bids dictionary is sorted by priority (vulture score).
        Allocates budget using mean+std calculation across all auctions.
        """
        if not bids:
            return {}
        
        # Calculate mean and std of proposed bids (baseline bids from strategy)
        bid_values = list(bids.values())
        mean_bid = sum(bid_values) / len(bid_values)
        
        if len(bid_values) > 1:
            variance = sum((x - mean_bid) ** 2 for x in bid_values) / len(bid_values)
            std_bid = variance ** 0.5
        else:
            std_bid = mean_bid * 0.5
        
        # Use mean + std as target, with configurable aggression multiplier
        mean_green_aggression = self.config.get('mean_green_aggression', 1.0)
        target_bid = (mean_bid + std_bid) * mean_green_aggression
        total_budget = budget  # Budget is already the phase-adjusted spending amount
        
        # Calculate what we'd spend at target level
        total_target = target_bid * len(bids)
        
        # Scale UP if target is too low (we want to spend the budget!)
        if total_target < total_budget * 0.7:  # If target spends less than 70% of budget
            scale_factor = (total_budget * 0.8) / total_target if total_target > 0 else 2.0
        else:
            scale_factor = min(1.0, total_budget / total_target) if total_target > 0 else 1.0
        
        # Allocate budget in sorted order (dict preserves insertion order in Python 3.7+)
        # Distribute equally at target level, but respect ordering
        adjusted_bids = {}
        remaining_budget = total_budget
        auction_ids = list(bids.keys())
        
        for i, auction_id in enumerate(auction_ids):
            if remaining_budget <= 0:
                break
            
            # Calculate bid: use target scaled amount
            scaled_bid = int(target_bid * scale_factor)
            
            # Ensure we don't exceed remaining budget
            final_bid = max(self.config['min_bid_amount'], min(scaled_bid, remaining_budget))
            adjusted_bids[auction_id] = final_bid
            remaining_budget -= final_bid
        
        logger.info(f"🎯 Mean Green: target {target_bid:.1f}, aggr {mean_green_aggression:.2f}, "
                   f"scale {scale_factor:.2f}, allocated {len(adjusted_bids)}/{len(bids)} auctions")
        return adjusted_bids
    
    def _higher_lower_mode(self, bids: Dict[str, int], budget: int, auctions: Dict) -> Dict[str, int]:
        """Weight bids by auction expected value (50% best, distribute rest)."""
        if not bids:
            return {}
        
        # Weight by original bid amounts (proxy for value)
        total_original = sum(bids.values())
        total_budget = budget  # Budget is already the phase-adjusted spending amount
        
        adjusted_bids = {}
        
        # Best auction gets 50% of budget
        best_auction = max(bids.items(), key=lambda x: x[1])
        best_bid = min(int(total_budget * 0.5), 
                      int(budget * self.config['max_single_bid_ratio']))
        adjusted_bids[best_auction[0]] = best_bid
        
        # Distribute remaining budget proportionally
        remaining_budget = total_budget - best_bid
        remaining_auctions = {k: v for k, v in bids.items() if k != best_auction[0]}
        
        if remaining_auctions:
            remaining_total = sum(remaining_auctions.values())
            for auction_id, original_bid in remaining_auctions.items():
                if remaining_total > 0:
                    proportion = original_bid / remaining_total
                    bid_amount = int(remaining_budget * proportion)
                else:
                    bid_amount = remaining_budget // len(remaining_auctions)
                
                adjusted_bids[auction_id] = max(self.config['min_bid_amount'], bid_amount)
        
        logger.info(f"📈 Higher-Lower: best {best_bid}, {len(remaining_auctions)} others")
        return adjusted_bids
    
    def _aggressive_spread_mode(self, bids: Dict[str, int], budget: int) -> Dict[str, int]:
        """Aggressively spend most of available gold to prevent accumulation."""
        if not bids:
            return {}
        
        # Spend 85% of available gold aggressively
        total_budget = int(budget * 0.85)
        
        # Sort auctions by original bid amount
        sorted_bids = sorted(bids.items(), key=lambda x: x[1], reverse=True)
        
        adjusted_bids = {}
        remaining_budget = total_budget
        
        for i, (auction_id, original_bid) in enumerate(sorted_bids):
            if remaining_budget <= 0:
                break
            
            # Front-load spending on better auctions
            if i == 0:  # Best auction
                bid_amount = min(remaining_budget // 2, 
                               int(budget * self.config['max_single_bid_ratio']))
            elif i < len(sorted_bids) // 2:  # Good auctions
                bid_amount = min(remaining_budget // 3, remaining_budget)
            else:  # Remaining auctions
                remaining_auctions = len(sorted_bids) - i
                bid_amount = remaining_budget // remaining_auctions
            
            bid_amount = max(self.config['min_bid_amount'], bid_amount)
            bid_amount = min(bid_amount, remaining_budget)
            
            adjusted_bids[auction_id] = bid_amount
            remaining_budget -= bid_amount
        
        total_spent = sum(adjusted_bids.values())
        spend_ratio = total_spent / budget if budget > 0 else 0
        
        logger.info(f"💥 Aggressive: {total_spent}/{budget} gold ({spend_ratio:.1%}) across {len(adjusted_bids)} auctions")
        return adjusted_bids
    
    def update_config(self, new_config: Dict):
        """Update bid mode configuration (for dashboard integration)."""
        # Validate mode change
        if 'current_mode' in new_config:
            mode_value = new_config['current_mode']
            if isinstance(mode_value, str):
                # Handle different string formats
                mode_mapping = {
                    'aggressive_spread': BidModeType.AGGRESSIVE_SPREAD,
                    'aggressive_spend': BidModeType.AGGRESSIVE_SPREAD,
                    'even_steven': BidModeType.EVEN_STEVEN,
                    'all_or_nothing': BidModeType.ALL_OR_NOTHING,
                    'mean_green': BidModeType.MEAN_GREEN,
                    'higher_lower': BidModeType.HIGHER_LOWER
                }
                new_config['current_mode'] = mode_mapping.get(mode_value.lower(), BidModeType.AGGRESSIVE_SPREAD)
        
        self.config.update(new_config)
        logger.info(f"🎯 Bid mode config updated: {new_config}")
    
    def get_current_config(self) -> Dict:
        """Get current configuration for dashboard display."""
        config_copy = self.config.copy()
        config_copy['current_mode'] = self.config['current_mode'].value
        return config_copy