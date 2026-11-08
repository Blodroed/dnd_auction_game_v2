"""
DoomGuy666 Start Mode Manager - Lightning Fast Game Initialization

This module handles different starting strategies and initialization modes
for optimal game phase adaptation and high-performance startup.

Author: DoomGuy666
Strategy: ADAPTIVE INITIALIZATION - Start strong, adapt fast, dominate early
"""

import time
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StartMode(Enum):
    """DoomGuy666 start modes for different game contexts."""
    AGGRESSIVE_OPENER = "aggressive_opener"    # High risk opening for early dominance
    CALCULATED_START = "calculated_start"      # Balanced opening with analysis
    DEFENSIVE_SETUP = "defensive_setup"        # Conservative start for long games
    ADAPTIVE_LAUNCH = "adaptive_launch"        # Dynamic start based on opponents

class StartModeManager:
    """
    Ultra-fast start mode management for DoomGuy666.
    
    Features:
    - Instant game phase detection
    - Opponent pattern analysis
    - Resource optimization for early rounds
    - Performance-focused initialization
    """
    
    def __init__(self):
        self.current_start_mode = StartMode.AGGRESSIVE_OPENER  # Default DoomGuy666 style
        self.initialization_time = 0
        self.early_game_performance = {}
        
        # Start mode configuration parameters
        self.start_configs = {
            StartMode.AGGRESSIVE_OPENER: {
                'initial_aggression': 2.0,
                'risk_tolerance': 0.8,
                'gold_allocation_ratio': 0.7,  # Use 70% of starting gold early
                'bid_frequency': 0.9,  # Bid on 90% of auctions
                'competition_threshold': 5  # Ignore competition up to 5 players
            },
            StartMode.CALCULATED_START: {
                'initial_aggression': 1.2,
                'risk_tolerance': 0.5,
                'gold_allocation_ratio': 0.4,  # Use 40% of starting gold
                'bid_frequency': 0.6,  # Bid on 60% of auctions
                'competition_threshold': 3  # Avoid high competition
            },
            StartMode.DEFENSIVE_SETUP: {
                'initial_aggression': 0.8,
                'risk_tolerance': 0.3,
                'gold_allocation_ratio': 0.25,  # Use 25% of starting gold
                'bid_frequency': 0.4,  # Bid on 40% of auctions
                'competition_threshold': 2  # Very selective bidding
            },
            StartMode.ADAPTIVE_LAUNCH: {
                'initial_aggression': 1.5,
                'risk_tolerance': 0.6,
                'gold_allocation_ratio': 0.5,  # Use 50% of starting gold
                'bid_frequency': 0.7,  # Bid on 70% of auctions
                'competition_threshold': 4  # Moderate competition tolerance
            }
        }
    
    def fast_analyze_game_start(self, agent_state: Dict, bank_state: Dict, 
                               opponents_data: Dict, total_rounds: int) -> StartMode:
        """Ultra-fast analysis of optimal start mode."""
        start_time = time.time()
        
        # Quick analysis factors
        starting_gold = agent_state.get('gold', 50)
        num_opponents = len(opponents_data) if opponents_data else 4
        expected_game_length = total_rounds
        
        # Fast decision logic
        if starting_gold > 60 and num_opponents <= 4:
            # Rich start with few opponents - GO AGGRESSIVE
            optimal_mode = StartMode.AGGRESSIVE_OPENER
        elif starting_gold < 30 or num_opponents > 6:
            # Poor start or many opponents - BE CAREFUL
            optimal_mode = StartMode.DEFENSIVE_SETUP
        elif expected_game_length > 80:
            # Long game - CALCULATED APPROACH
            optimal_mode = StartMode.CALCULATED_START
        else:
            # Standard conditions - ADAPT
            optimal_mode = StartMode.ADAPTIVE_LAUNCH
        
        self.initialization_time = time.time() - start_time
        self.current_start_mode = optimal_mode
        
        logger.info(f"⚡ DoomGuy666: Start mode {optimal_mode.value} selected in {self.initialization_time:.3f}s")
        return optimal_mode
    
    def get_start_parameters(self, mode: Optional[StartMode] = None) -> Dict:
        """Get start parameters for specified mode or current mode."""
        target_mode = mode or self.current_start_mode
        return self.start_configs.get(target_mode, self.start_configs[StartMode.ADAPTIVE_LAUNCH])
    
    def calculate_early_bid_strategy(self, auctions: Dict, agent_gold: int, 
                                   mode: Optional[StartMode] = None) -> Dict[str, int]:
        """Calculate optimal early-game bidding strategy."""
        params = self.get_start_parameters(mode)
        
        if not auctions or agent_gold <= 0:
            return {}
        
        # Calculate available budget based on start mode
        available_budget = int(agent_gold * params['gold_allocation_ratio'])
        bid_frequency = params['bid_frequency']
        aggression = params['initial_aggression']
        
        # Score and filter auctions
        scored_auctions = []
        for auction_id, auction_data in auctions.items():
            die = auction_data.get('die', 6)
            num = auction_data.get('num', 1)
            
            # Simple but fast scoring
            expected_value = num * ((die + 1) / 2)  # Average roll
            score = expected_value * aggression
            
            scored_auctions.append((auction_id, score, expected_value))
        
        # Sort by score and select top auctions based on frequency
        scored_auctions.sort(key=lambda x: x[1], reverse=True)
        target_auction_count = max(1, int(len(auctions) * bid_frequency))
        
        # Distribute budget across selected auctions
        selected_auctions = scored_auctions[:target_auction_count]
        bids = {}
        
        if selected_auctions:
            base_bid = available_budget // len(selected_auctions)
            remaining_budget = available_budget
            
            for auction_id, score, expected_value in selected_auctions:
                if remaining_budget <= 0:
                    break
                
                # Adjust bid based on auction quality and aggression
                score_multiplier = min(score / 10, 2.0)  # Cap at 2x
                bid_amount = max(1, int(base_bid * score_multiplier))
                bid_amount = min(bid_amount, remaining_budget)
                
                bids[auction_id] = bid_amount
                remaining_budget -= bid_amount
        
        return bids
    
    def adapt_start_mode(self, round_results: List[Dict], current_round: int) -> bool:
        """Adapt start mode based on early round performance."""
        if current_round > 10:  # Only adapt in early game
            return False
        
        # Analyze recent performance
        recent_wins = sum(1 for result in round_results[-5:] if result.get('won', False))
        win_rate = recent_wins / min(5, len(round_results)) if round_results else 0
        
        # Adaptation logic
        if win_rate < 0.2 and self.current_start_mode == StartMode.AGGRESSIVE_OPENER:
            # Aggressive not working, tone it down
            self.current_start_mode = StartMode.CALCULATED_START
            logger.info("📉 DoomGuy666: Adapting to CALCULATED_START due to poor performance")
            return True
        elif win_rate > 0.7 and self.current_start_mode == StartMode.DEFENSIVE_SETUP:
            # Defensive too conservative, increase aggression
            self.current_start_mode = StartMode.ADAPTIVE_LAUNCH
            logger.info("📈 DoomGuy666: Adapting to ADAPTIVE_LAUNCH due to good performance")
            return True
        
        return False
    
    def get_aggression_multiplier(self, current_round: int, total_rounds: int) -> float:
        """Get aggression multiplier based on start mode and game progress."""
        params = self.get_start_parameters()
        base_aggression = params['initial_aggression']
        
        # Adjust aggression based on game phase
        game_progress = current_round / max(total_rounds, 1)
        
        if game_progress < 0.2:  # Very early game
            return base_aggression
        elif game_progress < 0.4:  # Early game
            return base_aggression * 0.9  # Slightly reduce aggression
        else:  # Transitioning out of early game
            return base_aggression * 0.8  # More conservative
    
    def get_start_mode_stats(self) -> Dict:
        """Get comprehensive start mode statistics."""
        return {
            'current_start_mode': self.current_start_mode.value,
            'initialization_time': self.initialization_time,
            'early_game_performance': self.early_game_performance,
            'start_configs': {
                mode.value: config for mode, config in self.start_configs.items()
            },
            'available_modes': [mode.value for mode in StartMode]
        }
    
    def quick_setup_doomguy(self, agent_state: Dict, bank_state: Dict) -> Dict:
        """Quick setup for DoomGuy666 with optimal configuration."""
        setup_start = time.time()
        
        # Fast setup based on game conditions
        starting_gold = agent_state.get('gold', 50)
        
        if starting_gold >= 60:
            # Rich start - be very aggressive
            mode = StartMode.AGGRESSIVE_OPENER
            logger.info("💰 DoomGuy666: Rich start detected - AGGRESSIVE MODE ACTIVATED")
        elif starting_gold >= 40:
            # Standard start - adaptive approach
            mode = StartMode.ADAPTIVE_LAUNCH
            logger.info("⚖️ DoomGuy666: Standard start - ADAPTIVE MODE ACTIVATED")
        else:
            # Poor start - calculated approach
            mode = StartMode.CALCULATED_START
            logger.info("🎯 DoomGuy666: Limited resources - CALCULATED MODE ACTIVATED")
        
        self.current_start_mode = mode
        setup_time = time.time() - setup_start
        
        return {
            'start_mode': mode.value,
            'setup_time': setup_time,
            'parameters': self.get_start_parameters(mode),
            'ready_for_combat': True
        }
