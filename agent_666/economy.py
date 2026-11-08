"""
Vulture Mode Economy Analyzer - Economic analysis and budget optimization

This module handles economic analysis, budget allocation, and spending optimization
to prevent excessive gold accumulation while maximizing auction success.
"""

import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class EconomyAnalyzer:
    """
    Economic analysis engine for Vulture Mode.
    
    Key Functions:
    - Prevent gold accumulation by encouraging spending
    - Analyze bank interest and income patterns
    - Optimize budget allocation across rounds
    - Calculate optimal spending ratios
    
    Configurable parameters (dashboard controllable):
    - spending_ratio: Target percentage of gold to spend each round
    - reserve_ratio: Minimum gold to keep in reserve
    - interest_threshold: Interest rate that triggers different strategies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        # Default configurable parameters
        default_config = {
            'spending_ratio': 0.35,  # Base spending: 35% (balanced approach)
            'reserve_ratio': 0.5,   # Keep 50% in reserve (balanced)
            'interest_threshold': 1.025,  # Above 2.5% interest rate, be more conservative
            'max_single_round_spend_ratio': 0.6,  # Allow up to 60% in early game
            'accumulation_penalty': 0.9,  # Slight reduction when accumulating
            
            # Interest-based timeline analysis settings
            'max_bet_limit': 0.8,  # Base maximum bet limit percentage
            'use_dynamic_max_bet_limit': True,  # Enable dynamic adjustment
            'timeline_look_ahead': 10,  # Rounds to look ahead for analysis
            'aggressive_spending_threshold': 0.5,  # Trigger aggressive spending
            'conservative_spending_threshold': 0.8,  # Trigger conservative spending
            'max_adjustment_factor': 1.2,  # Maximum adjustment to base limit
        }
        
        # Merge provided config with defaults
        self.config = default_config.copy()
        if config:
            self.config.update(config)
            logger.info(f"💰 EconomyAnalyzer initialized with custom config: {list(config.keys())}")
        
        # Phase configuration (configurable via settings.json)
        self.phase_config = {
            'capital_build_end': self.config.get('phase_capital_build_end', 150),
            'compound_end': self.config.get('phase_compound_end', 500),
            'optimization_end': self.config.get('phase_optimization_end', 850),
            'capital_spending': self.config.get('phase_capital_spending', 0.6),
            'compound_high_interest': self.config.get('phase_compound_high_interest', 0.2),
            'compound_medium_high_interest': self.config.get('phase_compound_medium_high_interest', 0.27),
            'compound_medium_interest': self.config.get('phase_compound_medium_interest', 0.35),
            'compound_low_interest': self.config.get('phase_compound_low_interest', 0.45),
            'optimization_spending': self.config.get('phase_optimization_spending', 0.2),
            'endgame_spending': self.config.get('phase_endgame_spending', 0.8),
            'interest_high_threshold': self.config.get('interest_high_threshold', 7.0),
            'interest_medium_high_threshold': self.config.get('interest_medium_high_threshold', 4.0),
            'interest_medium_threshold': self.config.get('interest_medium_threshold', 2.0),
        }
        
        self.economic_history = []
        self.spending_history = []
    
    def calculate_round_budget(self, available_gold: int, current_round: int, 
                              bank_state: Dict) -> Dict:
        """
        Calculate optimal spending budget for current round.
        
        Key principle: Adapt spending based on interest rate patterns.
        
        Interest Rate Pattern (from auction_house.py):
        - Random walk between 1.0 (0%) and 1.1 (10%)
        - Step size: ±0.02 per round
        - Resets to ~1.00 every 250 rounds
        - Average rate over time: ~1.05 (5% per round)
        
        Args:
            available_gold: Current gold amount
            current_round: Current round number
            bank_state: Economic parameters (interest, income, etc.)
            
        Returns:
            Dict with spending recommendations
        """
        # Extract economic parameters
        interest_rate = self._get_current_interest(bank_state, current_round)
        gold_income = self._get_current_income(bank_state, current_round)
        bank_limit = self._get_current_bank_limit(bank_state, current_round)
        
        # Analyze future interest rates to predict compound potential
        future_rates = self._analyze_future_interest(bank_state, current_round)
        avg_future_rate = future_rates['avg_rate']
        interest_trend = future_rates['trend']  # 'rising', 'falling', or 'stable'
        
        # Detect gold accumulation problem
        accumulation_factor = self._detect_gold_accumulation(available_gold, gold_income)
        
        # Calculate base spending ratio
        base_spending = self.config['spending_ratio']
        
        # Phase-based strategy: Build capital early, compound mid-game, spend late-game
        # Use configurable phase boundaries and spending ratios
        pc = self.phase_config
        
        # Determine game phase with interest rate awareness
        if current_round < pc['capital_build_end']:  # CAPITAL BUILD PHASE
            # Aggressive bidding to build initial capital base
            spending_ratio = pc['capital_spending']
            logger.info(f"🚀 CAPITAL BUILD: Round {current_round} - aggressive growth ({spending_ratio:.0%})")
            
        elif current_round < pc['compound_end']:  # COMPOUND PHASE
            # Adjust spending based on interest rate forecast
            # Interest rate is (rate - 1.0) e.g., 1.05 = 5% interest
            effective_interest = (avg_future_rate - 1.0) * 100  # Convert to percentage
            
            if effective_interest >= pc['interest_high_threshold']:  # High interest
                # Very conservative - let compound interest work
                spending_ratio = pc['compound_high_interest']
                logger.info(f"💰 COMPOUND: Round {current_round} - HIGH interest ({effective_interest:.1f}%), conservative ({spending_ratio:.0%})")
            elif effective_interest >= pc['interest_medium_high_threshold']:  # Medium-high interest
                # Balanced - some spending, some compounding
                spending_ratio = pc['compound_medium_high_interest']
                logger.info(f"💰 COMPOUND: Round {current_round} - MEDIUM-HIGH interest ({effective_interest:.1f}%), balanced ({spending_ratio:.0%})")
            elif effective_interest >= pc['interest_medium_threshold']:  # Medium interest
                # Moderate spending
                spending_ratio = pc['compound_medium_interest']
                logger.info(f"💰 COMPOUND: Round {current_round} - MEDIUM interest ({effective_interest:.1f}%), moderate ({spending_ratio:.0%})")
            else:  # Low interest
                # More aggressive - interest not worth hoarding
                spending_ratio = pc['compound_low_interest']
                logger.info(f"💰 COMPOUND: Round {current_round} - LOW interest ({effective_interest:.1f}%), aggressive ({spending_ratio:.0%})")
                
        elif current_round < pc['optimization_end']:  # OPTIMIZATION PHASE
            # Strategic spending with large capital base
            spending_ratio = pc['optimization_spending']
            logger.info(f"📈 OPTIMIZATION: Round {current_round} - strategic bidding ({spending_ratio:.0%})")
            
        else:  # ENDGAME PHASE
            # Spend accumulated wealth for final point push (no point hoarding)
            spending_ratio = pc['endgame_spending']
            logger.info(f"🎯 ENDGAME: Round {current_round} - final push ({spending_ratio:.0%})")
        
        # Apply accumulation penalty
        spending_ratio *= accumulation_factor
        spending_ratio = min(spending_ratio, self.config['max_single_round_spend_ratio'])
        
        # Calculate final budget
        reserve_amount = max(
            int(available_gold * self.config['reserve_ratio']),
            gold_income // 4  # Keep at least 1/4 of income as reserve
        )
        
        spending_budget = min(
            int(available_gold * spending_ratio),
            available_gold - reserve_amount
        )
        
        # Apply max_budget_per_round if configured
        max_budget = self.config.get('max_budget_per_round', 0.85)
        if isinstance(max_budget, float) and 0 < max_budget <= 1.0:
            # Percentage-based max budget
            spending_budget = min(spending_budget, int(available_gold * max_budget))
        elif isinstance(max_budget, int) and max_budget > 0:
            # Fixed max budget
            spending_budget = min(spending_budget, max_budget)
        
        spending_budget = max(1, spending_budget)  # Always spend at least 1 gold
        
        # Store economic analysis
        economic_data = {
            'round': current_round,
            'available_gold': available_gold,
            'spending_budget': spending_budget,
            'reserve_amount': reserve_amount,
            'spending_ratio': spending_ratio,
            'interest_rate': interest_rate,
            'gold_income': gold_income,
            'accumulation_factor': accumulation_factor
        }
        
        self.economic_history.append(economic_data)
        
        # Keep only recent history
        if len(self.economic_history) > 100:
            self.economic_history.pop(0)
        
        logger.info(f"💰 Economy: Spend {spending_budget}/{available_gold} gold "
                   f"({spending_ratio:.1%}) | Interest: {interest_rate:.3f}")
        
        return economic_data
    
    def _analyze_future_interest(self, bank_state: Dict, current_round: int, 
                                 look_ahead: int = 50) -> Dict:
        """
        Analyze future interest rates to predict compound potential.
        
        Interest rate pattern (from auction_house.py):
        - Random walk: min=1.0 (0%), max=1.1 (10%), step=±0.02
        - Resets to ~1.0 every 250 rounds
        
        Args:
            bank_state: Economic state with remainder_bank_interest
            current_round: Current round number
            look_ahead: How many rounds ahead to analyze
            
        Returns:
            Dict with avg_rate, trend, and forecast analysis
        """
        interest_rates = bank_state.get('remainder_bank_interest', [1.05])
        
        # Get current and future rates
        current_rate = self._get_current_interest(bank_state, current_round)
        
        # Get next N rates for forecasting
        future_rates = []
        for i in range(look_ahead):
            idx = current_round + i
            if idx < len(interest_rates):
                future_rates.append(interest_rates[idx])
            else:
                # Assume average rate if we run out of data
                future_rates.append(1.05)
        
        # Calculate statistics
        avg_rate = sum(future_rates) / len(future_rates) if future_rates else 1.05
        
        # Detect trend by comparing first half vs second half
        if len(future_rates) >= 10:
            first_half = sum(future_rates[:len(future_rates)//2]) / (len(future_rates)//2)
            second_half = sum(future_rates[len(future_rates)//2:]) / (len(future_rates) - len(future_rates)//2)
            
            if second_half > first_half + 0.01:
                trend = 'rising'
            elif second_half < first_half - 0.01:
                trend = 'falling'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'current_rate': current_rate,
            'avg_rate': avg_rate,
            'trend': trend,
            'future_rates': future_rates[:10]  # First 10 for logging
        }
    
    def _get_current_interest(self, bank_state: Dict, current_round: int) -> float:
        """Get current interest rate."""
        interest_rates = bank_state.get('remainder_bank_interest', [1.03])
        if current_round < len(interest_rates):
            return interest_rates[current_round]
        return interest_rates[-1] if interest_rates else 1.03
    
    def _get_current_income(self, bank_state: Dict, current_round: int) -> int:
        """Get current gold income."""
        income_rates = bank_state.get('remainder_gold_income', [1000])
        if current_round < len(income_rates):
            return income_rates[current_round]
        return income_rates[-1] if income_rates else 1000
    
    def _get_current_bank_limit(self, bank_state: Dict, current_round: int) -> int:
        """Get current bank limit."""
        bank_limits = bank_state.get('remainder_bank_limit', [2000])
        if current_round < len(bank_limits):
            return bank_limits[current_round]
        return bank_limits[-1] if bank_limits else 2000
    
    def _detect_gold_accumulation(self, current_gold: int, income: int) -> float:
        """
        Detect gold accumulation status.
        
        Returns multiplier for spending ratio.
        HYBRID STRATEGY: Balance growth with spending
        """
        # Allow accumulation but not extreme hoarding
        if current_gold > income * 50:
            return 1.2  # Massive reserves - can afford to spend more
        elif current_gold > income * 20:
            return 1.0  # Large reserves - normal spending
        elif current_gold > income * 5:
            return 0.9  # Good reserves - slightly conservative
        elif current_gold > income * 2:
            return 1.0  # Building up - normal spending
        else:
            return 1.1  # Low reserves - slightly more aggressive
    
    def analyze_spending_effectiveness(self, round_results: Dict) -> Dict:
        """Analyze how effective our spending was in the last round."""
        bids_made = round_results.get('bids', {})
        auctions_won = round_results.get('wins', [])
        total_spent = sum(bids_made.values())
        
        # Calculate effectiveness metrics
        win_rate = len(auctions_won) / len(bids_made) if bids_made else 0
        gold_efficiency = len(auctions_won) / max(total_spent, 1)
        
        effectiveness = {
            'total_spent': total_spent,
            'auctions_bid': len(bids_made),
            'auctions_won': len(auctions_won),
            'win_rate': win_rate,
            'gold_efficiency': gold_efficiency
        }
        
        self.spending_history.append(effectiveness)
        
        # Keep only recent history
        if len(self.spending_history) > 50:
            self.spending_history.pop(0)
        
        return effectiveness
    
    def get_economic_outlook(self, bank_state: Dict, current_round: int, 
                           look_ahead: Optional[int] = None) -> Dict:
        """Get economic outlook for next N rounds."""
        # Use configured look-ahead if not specified
        if look_ahead is None:
            look_ahead = int(self.config.get('timeline_look_ahead', 10))
            
        outlook = {
            'future_interest': [],
            'future_income': [],
            'future_bank_limits': [],
            'recommended_strategy': 'aggressive_spend',
            'look_ahead_rounds': look_ahead
        }
        
        for i in range(look_ahead):
            future_round = current_round + i
            
            interest = self._get_current_interest(bank_state, future_round)
            income = self._get_current_income(bank_state, future_round)
            bank_limit = self._get_current_bank_limit(bank_state, future_round)
            
            outlook['future_interest'].append(interest)
            outlook['future_income'].append(income)
            outlook['future_bank_limits'].append(bank_limit)
        
        # Determine recommended strategy based on future trends
        avg_future_interest = sum(outlook['future_interest']) / len(outlook['future_interest'])
        
        # Use configurable thresholds for decision making
        good_interest_threshold = self.config.get('interest_threshold', 1.05)  # Default 1.05
        poor_interest_threshold = 0.95  # Hardcoded for now, could be configurable too
        
        if avg_future_interest > good_interest_threshold:
            outlook['recommended_strategy'] = 'moderate_spend'
        elif avg_future_interest < poor_interest_threshold:
            outlook['recommended_strategy'] = 'very_aggressive_spend'
        else:
            outlook['recommended_strategy'] = 'aggressive_spend'
            
        outlook['avg_future_interest'] = avg_future_interest
        
        return outlook
    
    def update_config(self, new_config: Dict):
        """Update economic configuration (for dashboard integration)."""
        self.config.update(new_config)
        logger.info(f"💰 Economy config updated: {new_config}")
    
    def get_performance_summary(self) -> Dict:
        """Get summary of economic performance."""
        if not self.spending_history:
            return {'status': 'no_data'}
        
        recent_history = self.spending_history[-10:]  # Last 10 rounds
        
        avg_win_rate = sum(h['win_rate'] for h in recent_history) / len(recent_history)
        avg_efficiency = sum(h['gold_efficiency'] for h in recent_history) / len(recent_history)
        total_spent = sum(h['total_spent'] for h in recent_history)
        
        return {
            'avg_win_rate': avg_win_rate,
            'avg_gold_efficiency': avg_efficiency,
            'total_recent_spending': total_spent,
            'rounds_analyzed': len(recent_history),
            'current_config': self.config.copy()
        }
    
    def calculate_max_bet_limit(self, bank_state: Dict, current_round: int, look_ahead: int = 10) -> float:
        """
        Calculate the maximum bet limit percentage based on future economic outlook.

        Args:
            bank_state: Economic parameters (interest, income, etc.).
            current_round: Current round number.
            look_ahead: Number of rounds to look ahead for analysis.

        Returns:
            A float representing the maximum bet limit percentage (e.g., 0.8 for 80%).
        """
        # Get economic outlook for the next `look_ahead` rounds
        outlook = self.get_economic_outlook(bank_state, current_round, look_ahead)

        # Analyze future income and bank limits
        future_income = outlook['future_income']
        future_bank_limits = outlook['future_bank_limits']

        # Calculate the average income-to-bank-limit ratio
        avg_income_to_limit_ratio = sum(
            income / limit if limit > 0 else 0
            for income, limit in zip(future_income, future_bank_limits)
        ) / len(future_income)

        # Get base max bet limit from configuration
        base_max_bet_limit = self.config.get('max_bet_limit', 0.8)
        use_dynamic_limit = self.config.get('use_dynamic_max_bet_limit', True)
        
        if not use_dynamic_limit:
            # Use static configured limit
            logger.info(f"📊 Using static max bet limit: {base_max_bet_limit:.1%}")
            return base_max_bet_limit
        
        # Get configurable thresholds
        aggressive_threshold = self.config.get('aggressive_spending_threshold', 0.5)
        conservative_threshold = self.config.get('conservative_spending_threshold', 0.8)
        max_adjustment = self.config.get('max_adjustment_factor', 1.2)
        
        # Determine dynamic adjustment based on economic outlook
        if avg_income_to_limit_ratio < aggressive_threshold:
            # Very poor future outlook - spend aggressively (up to max_adjustment of base limit)
            adjustment_factor = max_adjustment
            max_bet_limit = min(base_max_bet_limit * adjustment_factor, 0.95)  # Cap at 95%
        elif avg_income_to_limit_ratio < conservative_threshold:
            # Moderate future outlook - normal spending (100% of base limit)
            adjustment_factor = 1.0
            max_bet_limit = base_max_bet_limit * adjustment_factor
        else:
            # Good future outlook - conservative spending (80% of base limit)
            adjustment_factor = 0.8
            max_bet_limit = base_max_bet_limit * adjustment_factor
        
        logger.info(f"📊 Dynamic max bet limit: {max_bet_limit:.1%} (base: {base_max_bet_limit:.1%}, factor: {adjustment_factor:.1f}) based on future outlook")
        return max_bet_limit
    
    def get_max_bet_limit_for_round(self, bank_state: Dict, current_round: int) -> float:
        """
        Get the maximum bet limit for the current round based on interest-based timeline analysis.
        
        This is the main method agents should use to get their betting limit.
        """
        if self.config.get('use_max_bet_limit', True):
            return self.calculate_max_bet_limit(bank_state, current_round)
        else:
            return 1.0  # No limit if disabled