"""
DoomController - Generic Strategy and Bid Mode System

This module provides base classes and factory patterns for dynamically loading
different strategies and bid modes based on configuration. The DoomController
pattern allows for pluggable strategy selection and runtime configuration.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type, TYPE_CHECKING
from enum import Enum
from economy import EconomyAnalyzer
from settings_manager import get_settings_manager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from data_handler import VultureDataHandler  # type: ignore

# ================================
# BASE STRATEGY INTERFACE
# ================================

class DoomStrategy(ABC):
    """Base class for all auction strategies."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        
    @abstractmethod
    def calculate_bids(self, agent_id: str, auctions: Dict, 
                      prev_auctions: Dict, budget: int, data_handler: Optional['VultureDataHandler'] = None, pool: Optional[int] = None) -> Dict[str, int]:
        """Calculate bids for given auctions and budget."""
        pass
    
    @abstractmethod
    def update_config(self, new_config: Dict) -> None:
        """Update strategy configuration."""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get strategy information and current config."""
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'config': self.config.copy()
        }

# ================================
# BASE BID MODE INTERFACE  
# ================================

class DoomBidMode(ABC):
    """Base class for all bid distribution modes."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        
    @abstractmethod
    def apply_mode(self, strategy_bids: Dict[str, int], 
                  available_gold: int, auctions: Dict) -> Dict[str, int]:
        """Apply bid mode to strategy recommendations."""
        pass
    
    @abstractmethod
    def update_config(self, new_config: Dict) -> None:
        """Update bid mode configuration.""" 
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get bid mode information and current config."""
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'config': self.config.copy()
        }

# ================================
# STRATEGY TYPES
# ================================

class StrategyType(Enum):
    """Available strategy types."""
    VULTURE_MODE = "vulture_mode"
    AGGRESSIVE = "aggressive" 
    CONSERVATIVE = "conservative"
    RANDOM = "random"
    ADAPTIVE = "adaptive"

class BidModeType(Enum):
    """Available bid mode types."""
    ALL_OR_NOTHING = "all_or_nothing"
    EVEN_STEVEN = "even_steven"
    MEAN_GREEN = "mean_green"
    HIGHER_LOWER = "higher_lower"
    AGGRESSIVE_SPREAD = "aggressive_spread"

# ================================
# DOOM CONTROLLER FACTORY
# ================================

class DoomController:
    """
    Main controller for managing strategies and bid modes.
    
    Features:
    - Dynamic strategy/bid mode loading based on configuration
    - Runtime switching of strategies and modes
    - Centralized configuration management
    - Plugin architecture for new strategies/modes
    """
    
    def __init__(self, settings_manager=None, data_handler=None):
        if settings_manager is None:
            settings_manager = get_settings_manager()
        self.settings = settings_manager
        self.data_handler = data_handler
        self.strategy_registry = {}
        self.bid_mode_registry = {}
        
        # Register built-in strategies and bid modes
        self._register_builtin_components()
        
        # Current active components
        self.current_strategy = None
        self.current_bid_mode = None
        
        # Initialize economy analyzer
        self.economy = EconomyAnalyzer(settings_manager.get_economy_config())
        
        logger.info("🎮 DoomController initialized")
    
    def register_strategy(self, strategy_type: str, strategy_class: Type[DoomStrategy]):
        """Register a new strategy class."""
        self.strategy_registry[strategy_type] = strategy_class
        logger.info(f"🎯 Registered strategy: {strategy_type}")
    
    def register_bid_mode(self, mode_type: str, mode_class: Type[DoomBidMode]):
        """Register a new bid mode class.""" 
        self.bid_mode_registry[mode_type] = mode_class
        logger.info(f"🎛️ Registered bid mode: {mode_type}")
    
    def load_strategy(self, strategy_type: str, config: Optional[Dict] = None) -> DoomStrategy:
        """Load and configure a strategy."""
        if strategy_type not in self.strategy_registry:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        strategy_class = self.strategy_registry[strategy_type]
        strategy = strategy_class(config)
        
        logger.info(f"🎯 Loaded strategy: {strategy_type}")
        return strategy
    
    def load_bid_mode(self, mode_type: str, config: Optional[Dict] = None) -> DoomBidMode:
        """Load and configure a bid mode."""
        if mode_type not in self.bid_mode_registry:
            raise ValueError(f"Unknown bid mode type: {mode_type}")
        
        mode_class = self.bid_mode_registry[mode_type]
        bid_mode = mode_class(config)
        
        logger.info(f"🎛️ Loaded bid mode: {mode_type}")
        return bid_mode
    
    def initialize_from_settings(self):
        """Initialize strategy and bid mode from settings."""
        if not self.settings:
            raise ValueError("Settings manager not available")
        
        # Load strategy - merge strategy and data_analysis configs
        strategy_config = self.settings.get_strategy_config()
        data_analysis_config = self.settings.get('data_analysis', default={})
        merged_config = {**strategy_config, **data_analysis_config}
        strategy_type = strategy_config.get('type', 'vulture_mode')
        self.current_strategy = self.load_strategy(strategy_type, merged_config)
        
        # Load bid mode 
        bid_mode_config = self.settings.get_bid_mode_config()
        mode_type = bid_mode_config.get('current_mode', 'aggressive_spread')
        
        # Handle different mode type formats
        if hasattr(mode_type, 'value'):  # Enum object
            mode_type = mode_type.value
        elif isinstance(mode_type, str):
            # Handle string mode names
            mode_type = mode_type.lower()
        
        self.current_bid_mode = self.load_bid_mode(mode_type, bid_mode_config)
        
        logger.info(f"🎮 Initialized from settings: {strategy_type} + {mode_type}")
    
    def update_from_settings(self):
        """Update current components from settings changes."""
        if not self.settings or not self.current_strategy or not self.current_bid_mode:
            return
        
        # Check if settings file has changed
        if not self.settings.check_for_updates():
            return  # No changes, skip update
        
        # Update strategy config - merge strategy and data_analysis sections
        strategy_config = self.settings.get_strategy_config()
        data_analysis_config = self.settings.get('data_analysis', default={})
        merged_config = {**strategy_config, **data_analysis_config}
        self.current_strategy.update_config(merged_config)
        
        # Update data handler if available
        if self.data_handler and hasattr(self.data_handler, 'update_config'):
            self.data_handler.update_config(data_analysis_config)
        
        # Update bid mode config
        bid_mode_config = self.settings.get_bid_mode_config()
        self.current_bid_mode.update_config(bid_mode_config)
        
        logger.info("🔄 Updated components from settings")
    
    def calculate_bids(self, agent_id: str, auctions: Dict, prev_auctions: Dict, 
                  budget: int, available_gold: int, pool: Optional[int] = None) -> Dict[str, int]:
        """Main bidding calculation using current strategy and bid mode."""
        if not self.current_strategy or not self.current_bid_mode:
            raise ValueError("Strategy and bid mode must be initialized")

        # Get strategy recommendations (pass handler if available)
        try:
            # Pass `pool` through to the strategy if it accepts the parameter.
            try:
                strategy_bids = self.current_strategy.calculate_bids(
                    agent_id, auctions, prev_auctions, budget, data_handler=self.data_handler, pool=pool
                )
            except TypeError:
                # Some legacy strategies may not accept `pool` parameter
                strategy_bids = self.current_strategy.calculate_bids(
                    agent_id, auctions, prev_auctions, budget, data_handler=self.data_handler
                )
        except TypeError:
            # Backward compatibility: some strategies might not expect data_handler
            strategy_bids = self.current_strategy.calculate_bids(
                agent_id, auctions, prev_auctions, budget
            )

        # Guard against strategies returning None or unexpected types
        if not strategy_bids or not isinstance(strategy_bids, dict):
            strategy_bids = {}

        # Apply bid mode adjustments using the SPENDING BUDGET, not total gold
        # This respects the phase-based budget allocation from economy module
        final_bids = self.current_bid_mode.apply_mode(
            strategy_bids, budget, auctions
        )

        if not final_bids or not isinstance(final_bids, dict):
            final_bids = {}

        return final_bids
    
    def doom_bid_controller(self, agent_id: str, current_round: int, states: dict,
                           auctions: dict, prev_auctions: dict, *args, **kwargs) -> dict:
        """
        Generic bidding controller using configurable strategies and bid modes.
        
        Key features:
        - Configurable strategy selection (vulture_mode, aggressive, etc.)
        - Configurable bid mode selection (aggressive_spread, even_steven, etc.)
        - Real-time configuration updates
        - Aggressive gold spending to prevent accumulation
        """
        # Support both old and new server callback signatures. Older servers
        # passed `bank_state` as the 6th positional argument. Newer servers
        # include `pool` and `prev_pool_buys` between `prev_auctions` and
        # `bank_state`, i.e. (agent_id, round, states, auctions,
        # prev_auctions, pool, prev_pool_buys, bank_state). Accept both.
        # Positional parsing rules:
        # - len(args) == 1 -> (bank_state)
        # - len(args) == 3 -> (pool, prev_pool_buys, bank_state)
        # `bank_state` can also be provided via kwargs.
        bank_state = None
        pool = None
        prev_pool_buys = None
        if 'bank_state' in kwargs:
            bank_state = kwargs.get('bank_state')
        elif len(args) == 1:
            bank_state = args[0]
        elif len(args) == 3:
            pool, prev_pool_buys, bank_state = args
        # Normalize fallback values
        bank_state = bank_state or {}
        pool = pool or {}
        prev_pool_buys = prev_pool_buys or {}

        # Debug info for pool content if present
        if pool:
            logger.debug(f"🎲 Current pool info provided: {pool}")

        agent_state = states.get(agent_id, {})
        available_gold = agent_state.get("gold", 0)
        
        logger.info(f"🎮 Doom Round {current_round} | Gold: {available_gold}")
        
        # Handle no resources
        if available_gold <= 0 or not auctions:
            return {}
        
        try:
            # Check for settings updates and refresh configurations
            self.update_from_settings()
            
            # Compute pool contribution as configurable fraction of points won in previous round
            pool_contribution = 0
            try:
                contribution_rate = float(self.settings.get('economy', 'pool_contribution_rate', 0.05))
            except Exception:
                contribution_rate = 0.05

            # Sum points won in previous round(s) from prev_auctions data
            points_won_last_round = 0
            try:
                use_highest = bool(self.settings.get('economy', 'pool_contribution_use_highest', False))
                won_rewards = []
                for aid, pa in (prev_auctions or {}).items():
                    bids_list = pa.get('bids', [])
                    if bids_list and isinstance(bids_list, list):
                        # Winner is first element (server ensures ordering)
                        winner = bids_list[0].get('a_id') if isinstance(bids_list[0], dict) else None
                        if winner == agent_id:
                            won_rewards.append(int(pa.get('reward', 0) or pa.get('points', 0)))
                if use_highest and won_rewards:
                    points_won_last_round = max(won_rewards)
                else:
                    points_won_last_round = sum(won_rewards)
            except Exception:
                points_won_last_round = 0

            # Compute default contribution based on previous wins (points currency).
            # IMPORTANT: Only contribute if we have previous points won in last round —
            # do not fall back to any minimal contribution when there are no wins.
            pool_contribution = 0
            if points_won_last_round > 0:
                try:
                    pool_contribution = max(1, int(round(points_won_last_round * contribution_rate)))
                except Exception:
                    pool_contribution = 0

            # Ensure we don't try to contribute more points than agent has
            available_points = agent_state.get("points", 0)
            pool_contribution = max(0, min(pool_contribution, available_points))

            # Respect min_points_reserve and pool_buy_enabled from settings
            min_points_reserve = int(self.settings.get('economy', 'min_points_reserve', 1))
            pool_buy_enabled = bool(self.settings.get('economy', 'pool_buy_enabled', True))
            if not pool_buy_enabled:
                pool_contribution = 0
            elif available_points - pool_contribution < min_points_reserve:
                # Reduce or disable pool buy to maintain reserve
                pool_contribution = max(0, available_points - min_points_reserve)

            # Economic analysis for budget allocation uses gold only; pool is paid with points
            budget_info = self.economy.calculate_round_budget(
                available_gold, current_round, bank_state
            )
            
            # Get strategy recommendations and apply bid mode
            final_bids = self.calculate_bids(
                agent_id, auctions, prev_auctions,
                budget_info['spending_budget'], available_gold, pool=pool
            )
            # Ensure final_bids is a dict for later aggregation
            if not final_bids or not isinstance(final_bids, dict):
                final_bids = {}
            
            total_bid = sum(final_bids.values())
            logger.info(f"🎯 Doom bids: {len(final_bids)} auctions, {total_bid}/{available_gold} gold")
            
            # Attach pool contribution to return value for clients expecting `{ "bids": {...}, "pool": n }`.
            # Keep backwards compatibility: return just the bids dict for callers that expect only that.
            # The caller (eg main) will wrap this into the `bids`/`pool` structure sent to the server.
            # For now we simply return the bids dict but expose the pool contribution as an attribute
            # on the controller for wrappers to use if needed.
            self._last_pool_contribution = pool_contribution
            return final_bids
            
        except Exception as e:
            logger.error(f"🎮 Doom bidding error: {e}")
            # Emergency aggressive fallback to prevent gold accumulation
            return self.emergency_spend_gold(auctions, available_gold)

    def emergency_spend_gold(self, auctions: Dict, available_gold: int) -> Dict[str, int]:
        """Emergency gold spending to prevent accumulation."""
        if not auctions:
            return {}
        
        bids = {}
        remaining_gold = available_gold
        auction_list = list(auctions.keys())
        
        # Spend 80% of available gold aggressively
        target_spend = int(available_gold * 0.8)
        bid_per_auction = max(1, target_spend // len(auction_list))
        
        for auction_id in auction_list:
            if remaining_gold <= 0:
                break
            bid_amount = min(bid_per_auction, remaining_gold)
            if bid_amount > 0:
                bids[auction_id] = bid_amount
                remaining_gold -= bid_amount
        
        return bids
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategy types."""
        return list(self.strategy_registry.keys())
    
    def get_available_bid_modes(self) -> List[str]:
        """Get list of available bid mode types."""
        return list(self.bid_mode_registry.keys())
    
    def get_current_info(self) -> Dict[str, Any]:
        """Get information about current strategy and bid mode."""
        return {
            'strategy': self.current_strategy.get_info() if self.current_strategy else None,
            'bid_mode': self.current_bid_mode.get_info() if self.current_bid_mode else None,
            'available_strategies': self.get_available_strategies(),
            'available_bid_modes': self.get_available_bid_modes()
        }
    
    def _register_builtin_components(self):
        """Register built-in strategies and bid modes."""
        # Import here to avoid circular imports
        try:
            from strategies import VultureMode
            from bid_modes import BidModeSelector
            
            # Register strategies
            self.register_strategy('vulture_mode', VultureModeAdapter)
            
            # Register bid modes (using the correct enum values)
            self.register_bid_mode('aggressive_spend', AggressiveSpreadAdapter)
            self.register_bid_mode('aggressive_spread', AggressiveSpreadAdapter)  # Alias
            self.register_bid_mode('even_steven', EvenStevenAdapter)
            self.register_bid_mode('all_or_nothing', AllOrNothingAdapter)
            self.register_bid_mode('mean_green', MeanGreenAdapter)
            self.register_bid_mode('higher_lower', HigherLowerAdapter)
            
        except ImportError as e:
            logger.warning(f"Could not import built-in components: {e}")

# ================================
# ADAPTER CLASSES FOR EXISTING COMPONENTS
# ================================

class VultureModeAdapter(DoomStrategy):
    """Adapter for existing VultureMode strategy."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        from strategies import VultureMode
        self.vulture_mode = VultureMode(config)
    
    def calculate_bids(self, agent_id: str, auctions: Dict, 
                  prev_auctions: Dict, budget: int, data_handler: Optional['VultureDataHandler'] = None, pool: Optional[int] = None) -> Dict[str, int]:
        # Forward data_handler to underlying VultureMode strategy if present
        try:
            return self.vulture_mode.calculate_vulture_bids(agent_id, auctions, prev_auctions, budget, data_handler=data_handler, pool=pool)
        except TypeError:
            return self.vulture_mode.calculate_vulture_bids(agent_id, auctions, prev_auctions, budget)
    
    def update_config(self, new_config: Dict) -> None:
        self.config.update(new_config)
        self.vulture_mode.update_config(new_config)

class AggressiveSpreadAdapter(DoomBidMode):
    """Adapter for aggressive spread bid mode."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        from bid_modes import BidModeSelector, BidModeType
        self.bid_selector = BidModeSelector(config)
    
    def apply_mode(self, strategy_bids: Dict[str, int], 
                  available_gold: int, auctions: Dict) -> Dict[str, int]:
        return self.bid_selector.apply_bid_mode(strategy_bids, available_gold, auctions)
    
    def update_config(self, new_config: Dict) -> None:
        self.config.update(new_config)
        self.bid_selector.update_config(new_config)

class EvenStevenAdapter(DoomBidMode):
    """Adapter for even steven bid mode."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        from bid_modes import BidModeSelector, BidModeType
        config = config or {}
        config['current_mode'] = BidModeType.EVEN_STEVEN
        self.bid_selector = BidModeSelector(config)
    
    def apply_mode(self, strategy_bids: Dict[str, int], 
                  available_gold: int, auctions: Dict) -> Dict[str, int]:
        return self.bid_selector.apply_bid_mode(strategy_bids, available_gold, auctions)
    
    def update_config(self, new_config: Dict) -> None:
        self.config.update(new_config)
        self.bid_selector.update_config(new_config)

class AllOrNothingAdapter(DoomBidMode):
    """Adapter for all-or-nothing bid mode."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        from bid_modes import BidModeSelector, BidModeType
        config = config or {}
        config['current_mode'] = BidModeType.ALL_OR_NOTHING
        self.bid_selector = BidModeSelector(config)
    
    def apply_mode(self, strategy_bids: Dict[str, int], 
                  available_gold: int, auctions: Dict) -> Dict[str, int]:
        return self.bid_selector.apply_bid_mode(strategy_bids, available_gold, auctions)
    
    def update_config(self, new_config: Dict) -> None:
        self.config.update(new_config)
        self.bid_selector.update_config(new_config)

class MeanGreenAdapter(DoomBidMode):
    """Adapter for mean green bid mode."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        from bid_modes import BidModeSelector, BidModeType
        config = config or {}
        config['current_mode'] = BidModeType.MEAN_GREEN
        self.bid_selector = BidModeSelector(config)
    
    def apply_mode(self, strategy_bids: Dict[str, int], 
                  available_gold: int, auctions: Dict) -> Dict[str, int]:
        return self.bid_selector.apply_bid_mode(strategy_bids, available_gold, auctions)
    
    def update_config(self, new_config: Dict) -> None:
        self.config.update(new_config)
        self.bid_selector.update_config(new_config)

class HigherLowerAdapter(DoomBidMode):
    """Adapter for higher/lower bid mode."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        from bid_modes import BidModeSelector, BidModeType
        config = config or {}
        config['current_mode'] = BidModeType.HIGHER_LOWER
        self.bid_selector = BidModeSelector(config)
    
    def apply_mode(self, strategy_bids: Dict[str, int], 
                  available_gold: int, auctions: Dict) -> Dict[str, int]:
        return self.bid_selector.apply_bid_mode(strategy_bids, available_gold, auctions)
    
    def update_config(self, new_config: Dict) -> None:
        self.config.update(new_config)
        self.bid_selector.update_config(new_config)