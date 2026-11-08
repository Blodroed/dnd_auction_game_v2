"""
VULTURE MODE Data Handler - Exploiting Deadspace in Auction Bidding Patterns

This module implements a comprehensive data analysis system to identify and exploit
low-competition dice auctions. It tracks bidding patterns, calculates expected values,
and identifies "green zones" where competition is minimal.

Author: Agent 666
Strategy: VULTURE MODE - Exploiting deadspace for maximum dice acquisition
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import logging
from datetime import datetime

from dice import average_roll, dice_score, fast_dice_stats

logger = logging.getLogger(__name__)

class VultureDataHandler:
    """
    Analyzes auction data to identify deadspace opportunities where few agents bid.
    
    Key Features:
    - Tracks bidding patterns across all dice combinations
    - Calculates expected values vs actual bid competition
    - Identifies green zones (low competition areas)
    - Provides vulture opportunities scoring
    """
    
    def __init__(self, config: Optional[Dict] = None, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Default configuration
        default_config = {
            'min_vulture_score': 2.0,
            'max_bid_per_auction': 20,
            'competition_analysis_rounds': 5,
            'pattern_detection_enabled': True,
            'learning_rate': 0.1,
            'historical_weight': 0.8
        }
        
        # Merge provided config with defaults
        self.config = default_config.copy()
        if config:
            self.config.update(config)
            logger.info(f"🦅 VultureDataHandler initialized with custom config: {list(config.keys())}")
        
        # Core data structures for tracking patterns
        self.bidding_matrix = defaultdict(list)  # (die, num) -> list of bid amounts
        self.auction_outcomes = defaultdict(list)  # (die, num, bonus) -> list of rewards
        self.competition_levels = defaultdict(list)  # (die, num) -> list of bid counts
        self.expected_values = {}  # (die, num) -> calculated EV
    
    def update_config(self, new_config: Dict) -> None:
        """Update data handler configuration (for real-time settings updates)."""
        self.config.update(new_config)
        logger.info(f"🦅 VultureDataHandler config updated: {list(new_config.keys())}")
        self.vulture_scores = {}  # (die, num) -> opportunity score
        
        # Dice generation probabilities from source
        self.die_sizes = [2, 3, 4, 6, 8, 10, 12, 20, 20]
        self.die_prob = [8, 8, 9, 8, 6, 6, 5, 2, 1]
        self.max_n_die = [5, 7, 10, 2, 3, 3, 6, 2, 4]
        
        # Load existing data
        self.load_historical_data()
        
    def process_game_state(self, game_state: Dict) -> None:
        """
        Process current game state and update bidding patterns.
        
        Args:
            game_state: Current game state including auctions and previous auctions
        """
        # Process previous auctions to learn from completed bidding
        if 'prev_auctions' in game_state:
            self._process_previous_auctions(game_state['prev_auctions'])
            
        # Analyze current auctions for immediate opportunities
        if 'auctions' in game_state:
            self._analyze_current_auctions(game_state['auctions'])
            
        # Update vulture opportunity scores
        self._calculate_vulture_scores()
        
        # Save updated data
        self.save_data()
        
    def _process_previous_auctions(self, prev_auctions: Dict) -> None:
        """Process completed auctions to update bidding pattern data."""
        for auction_id, auction_data in prev_auctions.items():
            die = auction_data['die']
            num = auction_data['num']
            bonus = auction_data['bonus']
            reward = auction_data['reward']
            bids = auction_data.get('bids', [])
            
            # Track auction outcome
            key = (die, num, bonus)
            self.auction_outcomes[key].append(reward)
            
            # Track bidding competition
            dice_key = (die, num)
            bid_amounts = [bid['gold'] for bid in bids]
            self.bidding_matrix[dice_key].extend(bid_amounts)
            self.competition_levels[dice_key].append(len(bids))
            
            # Log interesting patterns
            expected_reward = average_roll(num, die, bonus)
            if len(bids) == 0 and reward >= expected_reward * 0.8:
                logger.info(f"VULTURE OPPORTUNITY MISSED: {dice_key} had {reward} reward with 0 bids!")
                
    def _analyze_current_auctions(self, auctions: Dict) -> None:
        """Analyze current auctions for immediate vulture opportunities."""
        opportunities = []
        
        for auction_id, auction_data in auctions.items():
            die = auction_data['die']
            num = auction_data['num']
            bonus = auction_data['bonus']
            
            dice_key = (die, num)
            expected_reward = average_roll(num, die, bonus)
            vulture_score = self.get_vulture_score(dice_key)
            
            opportunities.append({
                'auction_id': auction_id,
                'dice_key': dice_key,
                'expected_reward': expected_reward,
                'vulture_score': vulture_score,
                'bonus': bonus,
                'dice_format': f"{num}d{die}{bonus:+d}"
            })
            
        # Sort by vulture opportunity score
        opportunities.sort(key=lambda x: x['vulture_score'], reverse=True)
        
        # Log top opportunities
        for i, opp in enumerate(opportunities[:5]):
            logger.info(f"Vulture Rank {i+1}: {opp['dice_format']} "
                       f"(Score: {opp['vulture_score']:.3f}, "
                       f"Expected: {opp['expected_reward']:.1f})")
                       
    def _calculate_vulture_scores(self) -> None:
        """
        Calculate vulture opportunity scores for all dice combinations.
        
        Score factors:
        - Low average competition (fewer bidders)
        - Low average bid amounts
        - High expected value
        - Consistency of low competition
        """
        for dice_key in self.competition_levels.keys():
            die, num = dice_key
            
            # Get statistics
            competitions = self.competition_levels[dice_key]
            bid_amounts = self.bidding_matrix[dice_key]
            
            if not competitions:
                continue
                
            # Calculate base expected value
            expected_reward = average_roll(num, die, 0)  # Use 0 bonus for base calculation
            
            # Competition metrics
            avg_competition = np.mean(competitions)
            competition_consistency = 1 / (1 + np.std(competitions))  # Higher is better
            no_bid_percentage = sum(1 for c in competitions if c == 0) / len(competitions)
            
            # Bidding metrics
            if bid_amounts:
                avg_bid = np.mean(bid_amounts)
                bid_consistency = 1 / (1 + np.std(bid_amounts))
            else:
                avg_bid = 0
                bid_consistency = 1.0
                
            # Calculate composite vulture score
            # Higher score = better vulture opportunity
            competition_factor = 1 / (1 + avg_competition)  # Lower competition is better
            bid_factor = 1 / (1 + avg_bid / max(expected_reward, 1))  # Lower bids relative to value
            consistency_factor = (competition_consistency + bid_consistency) / 2
            no_bid_bonus = no_bid_percentage * 2  # Boost for frequent no-bid auctions
            
            vulture_score = (
                expected_reward * 0.3 +  # Base value
                competition_factor * 0.3 +  # Low competition
                bid_factor * 0.2 +  # Low bid amounts
                consistency_factor * 0.1 +  # Consistency
                no_bid_bonus * 0.1  # No bid bonus
            )
            
            self.vulture_scores[dice_key] = vulture_score
            
    def get_vulture_score(self, dice_key: Tuple[int, int]) -> float:
        """Get vulture opportunity score for a dice combination."""
        # Return a moderate default score when no historical data exists
        # This encourages bidding when the agent is just starting
        return self.vulture_scores.get(dice_key, 0.5)
        
    def get_green_zones(self, min_score: float = 0.5) -> List[Tuple[int, int]]:
        """
        Get dice combinations that are in the 'green zone' (good vulture opportunities).
        
        Args:
            min_score: Minimum vulture score to be considered a green zone
            
        Returns:
            List of (die, num) tuples sorted by vulture score
        """
        green_zones = [
            (dice_key, score) for dice_key, score in self.vulture_scores.items()
            if score >= min_score
        ]
        green_zones.sort(key=lambda x: x[1], reverse=True)
        return [dice_key for dice_key, _ in green_zones]
        
    def get_bidding_recommendation(self, dice_key: Tuple[int, int], 
                                 bonus: int, available_gold: int) -> Dict:
        """
        Get bidding recommendation for a specific auction.
        
        Args:
            dice_key: (die, num) tuple
            bonus: Bonus for this specific auction
            available_gold: Gold available for bidding
            
        Returns:
            Dictionary with recommendation details
        """
        die, num = dice_key
        expected_reward = average_roll(num, die, bonus)
        vulture_score = self.get_vulture_score(dice_key)
        
        # Get historical bidding data
        competitions = self.competition_levels.get(dice_key, [])
        bid_amounts = self.bidding_matrix.get(dice_key, [])
        
        # Track if we have historical data to adjust recommendations
        has_history = len(competitions) > 0 and len(bid_amounts) > 0
        
        if competitions:
            avg_competition = np.mean(competitions)
            no_bid_prob = sum(1 for c in competitions if c == 0) / len(competitions)
        else:
            # Assume moderate competition when no data
            avg_competition = 3.0
            no_bid_prob = 0.0
            
        if bid_amounts:
            avg_bid = np.mean(bid_amounts)
            min_bid = min(bid_amounts)
        else:
            # More generous when no data
            avg_bid = expected_reward * 0.3
            min_bid = 1
            
        # Calculate recommended bid - scale with available budget for aggressive spending
        max_single_bid = self.config.get('max_bid_per_auction', 1000)
        
        # Boost vulture score when we have no historical data to ensure we bid
        if not has_history:
            vulture_score = max(vulture_score, 0.6)  # Treat unknown as medium-high opportunity
        
        if vulture_score > 0.7:  # High opportunity
            # Bid very aggressively - use significant portion of available gold
            base_bid = max(
                int(expected_reward * 1.2),  # 120% of expected value
                int(avg_bid * 1.5) if avg_bid > 0 else min_bid,
                int(available_gold * 0.15)  # At least 15% of available budget
            )
            recommended_bid = min(base_bid, available_gold, max_single_bid)
            confidence = "HIGH"
        elif vulture_score > 0.4:  # Medium opportunity  
            # Moderate bidding
            base_bid = max(
                int(expected_reward * 0.8),
                int(avg_bid * 1.2) if avg_bid > 0 else min_bid,
                int(available_gold * 0.10)  # At least 10% of available budget
            )
            recommended_bid = min(base_bid, available_gold, max_single_bid)
            confidence = "MEDIUM"
        else:  # Low opportunity
            # Conservative bid but still reasonable
            base_bid = max(
                int(expected_reward * 0.5),
                int(avg_bid * 0.8) if avg_bid > 0 else 1,
                int(available_gold * 0.05)  # At least 5% of available budget
            )
            recommended_bid = min(base_bid, available_gold // 2, max_single_bid)
            confidence = "LOW"
            
        # Ensure recommended_bid is sensible given available_gold - at least 1 if we have gold
        if available_gold and available_gold > 0:
            try:
                recommended_bid = int(min(max(1, int(recommended_bid)), available_gold))
            except Exception:
                recommended_bid = min(int(recommended_bid or 1), available_gold)

        return {
            'recommended_bid': recommended_bid,
            'expected_reward': expected_reward,
            'vulture_score': vulture_score,
            'confidence': confidence,
            'avg_competition': avg_competition,
            'no_bid_probability': no_bid_prob,
            'historical_avg_bid': avg_bid,
            'dice_format': f"{num}d{die}{bonus:+d}"
        }
        
    def create_opportunity_matrix(self) -> pd.DataFrame:
        """
        Create a DataFrame showing vulture opportunities in table format.
        
        Returns:
            DataFrame with die types as columns, num dice as rows, and vulture scores as values
        """
        # Get all unique die sizes and numbers from our data
        die_sizes = sorted(set(dice_key[0] for dice_key in self.vulture_scores.keys()))
        num_dice = sorted(set(dice_key[1] for dice_key in self.vulture_scores.keys()))
        
        # Create matrix
        matrix_data = []
        for num in num_dice:
            row = []
            for die in die_sizes:
                score = self.vulture_scores.get((die, num), 0.0)
                row.append(score)
            matrix_data.append(row)
            
        # Create DataFrame
        df = pd.DataFrame(
            matrix_data,
            index=[f"{n} dice" for n in num_dice],
            columns=[f"d{d}" for d in die_sizes]
        )
        
        return df
        
    def save_data(self) -> None:
        """Save current data to JSON files."""
        timestamp = datetime.now().isoformat()
        
        # Prepare data for JSON serialization
        data = {
            'timestamp': timestamp,
            'bidding_matrix': {str(k): v for k, v in self.bidding_matrix.items()},
            'competition_levels': {str(k): v for k, v in self.competition_levels.items()},
            'vulture_scores': {str(k): v for k, v in self.vulture_scores.items()},
            'auction_outcomes': {str(k): v for k, v in self.auction_outcomes.items()}
        }
        
        # Save to file
        data_file = self.data_dir / 'vulture_data.json'
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Vulture data saved to {data_file}")
        
    def load_historical_data(self) -> None:
        """Load historical data from JSON files."""
        data_file = self.data_dir / 'vulture_data.json'
        
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert string keys back to tuples
                for key_str, values in data.get('bidding_matrix', {}).items():
                    key = eval(key_str)  # Convert "(2, 3)" back to (2, 3)
                    self.bidding_matrix[key] = values
                    
                for key_str, values in data.get('competition_levels', {}).items():
                    key = eval(key_str)
                    self.competition_levels[key] = values
                    
                for key_str, value in data.get('vulture_scores', {}).items():
                    key = eval(key_str)
                    self.vulture_scores[key] = value
                    
                for key_str, values in data.get('auction_outcomes', {}).items():
                    key = eval(key_str)
                    self.auction_outcomes[key] = values
                    
                logger.info(f"Loaded historical vulture data from {data_file}")
                
            except Exception as e:
                logger.warning(f"Failed to load historical data: {e}")
                
    def load_game_logs(self, log_directory: str = "agent_666/logs") -> None:
        """
        Load and process multiple game log files to build comprehensive data.
        
        Args:
            log_directory: Directory containing JSONL log files
        """
        log_dir = Path(log_directory)
        if not log_dir.exists():
            logger.warning(f"Log directory {log_dir} does not exist")
            return
            
        processed_count = 0
        for log_file in log_dir.glob("*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            game_state = json.loads(line)
                            if 'prev_auctions' in game_state and game_state['prev_auctions']:
                                self._process_previous_auctions(game_state['prev_auctions'])
                                processed_count += 1
                                
            except Exception as e:
                logger.warning(f"Error processing {log_file}: {e}")
                
        logger.info(f"Processed {processed_count} game states from log files")
        
        # Recalculate scores with new data
        self._calculate_vulture_scores()
        self.save_data()
        
    def get_statistics_summary(self) -> Dict:
        """Get summary statistics about the vulture analysis."""
        total_auctions = sum(len(outcomes) for outcomes in self.auction_outcomes.values())
        total_dice_types = len(self.vulture_scores)
        
        if self.vulture_scores:
            avg_vulture_score = np.mean(list(self.vulture_scores.values()))
            best_opportunities = sorted(
                [(k, v) for k, v in self.vulture_scores.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        else:
            avg_vulture_score = 0.0
            best_opportunities = []
            
        return {
            'total_auctions_analyzed': total_auctions,
            'total_dice_combinations': total_dice_types,
            'average_vulture_score': avg_vulture_score,
            'best_opportunities': [
                {
                    'dice_combination': f"{num}d{die}",
                    'vulture_score': score
                }
                for (die, num), score in best_opportunities
            ]
        }

def create_vulture_strategy_bids(handler: VultureDataHandler, auctions: Dict,
                               available_gold: int, agent_id: str) -> Dict:
    """
    Create vulture strategy bids using the data handler analysis.
    
    Args:
        handler: VultureDataHandler instance with analyzed data
        auctions: Current auctions dictionary
        available_gold: Available gold for bidding
        agent_id: Agent identifier
        
    Returns:
        Dictionary of auction_id -> bid_amount
    """
    bids = {}
    remaining_gold = available_gold
    
    # Get all auction opportunities and sort by vulture score
    opportunities = []
    for auction_id, auction_data in auctions.items():
        die = auction_data['die']
        num = auction_data['num']
        bonus = auction_data['bonus']
        
        dice_key = (die, num)
        recommendation = handler.get_bidding_recommendation(dice_key, bonus, remaining_gold)
        recommendation['auction_id'] = auction_id
        opportunities.append(recommendation)
        
    # Sort by vulture score (best opportunities first)
    opportunities.sort(key=lambda x: x['vulture_score'], reverse=True)
    
    # Allocate bids starting with best opportunities
    for opp in opportunities:
        auction_id = opp['auction_id']
        recommended_bid = opp['recommended_bid']
        
        # Only bid if we have enough gold and it's a decent opportunity
        # Enforce a minimum bid of 1 if we have any remaining budget
        if remaining_gold > 0 and recommended_bid <= 0:
            recommended_bid = 1
        # Clamp recommended bid to remaining gold
        recommended_bid = min(recommended_bid, remaining_gold)
        if remaining_gold >= recommended_bid and opp['vulture_score'] > 0.2 and recommended_bid > 0:
            bids[auction_id] = recommended_bid
            remaining_gold -= recommended_bid
            
            logger.info(f"VULTURE BID: {opp['dice_format']} -> {recommended_bid} gold "
                       f"(Score: {opp['vulture_score']:.3f}, "
                       f"Expected: {opp['expected_reward']:.1f})")
                       
        # Stop if we're running low on gold
        if remaining_gold < available_gold * 0.1:
            break
            
    return bids
