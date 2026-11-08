"""
DoomGuy666 Agent - Controller

The infamous DoomGuy666 agent using advanced strategies.
Minimal main controller that orchestrates the doom guy auction agent.
All core logic is delegated to specialized modules for clean separation of concerns.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional

from websockets import ConnectionClosedError, ConnectionClosedOK
from dnd_auction_game import AuctionGameClient

# Import doom controller and components
from doom_controller import DoomController
from data_handler import VultureDataHandler
from storage import VultureStorage
from economy import EconomyAnalyzer
from settings_manager import get_settings_manager, get_setting

# Initialize settings-based logging
settings_manager = get_settings_manager()
log_level = get_setting('logging', 'level', 'INFO')
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

class DoomAgent:
    """Generic DoomGuy agent with configurable strategies and bid modes."""
    
    def __init__(self):
        # Load settings and initialize components with configuration
        self.settings = get_settings_manager()

        # Initialize supporting components
        self.data_handler = VultureDataHandler(self.settings.get('data_analysis', default={}))
        self.storage = VultureStorage(self.settings.get('storage', default={}))
        self.economy = EconomyAnalyzer(self.settings.get_economy_config())
        
        # Initialize DoomController for strategy/bid mode management
        self.doom_controller = DoomController(self.settings, data_handler=self.data_handler)
        self.doom_controller.initialize_from_settings()
        
        agent_info = self.settings.get_agent_info()
        controller_info = self.doom_controller.get_current_info()
        
        logger.info(f"🎮 {agent_info.get('name', 'DoomGuy666')} v{agent_info.get('version', '2.0')} INITIALIZED")
        logger.info(f"🎯 Strategy: {controller_info['strategy']['name']}")
        logger.info(f"🎛️ Bid Mode: {controller_info['bid_mode']['name']}")
        logger.info(f"🛠️ Settings loaded: {self.settings.settings_file}")
    
    def update_configurations(self):
        """Update all component configurations from current settings."""
        try:
            # Check for settings file updates
            if self.settings.check_for_updates():
                logger.info("🔄 Updating component configurations...")
                
                # Update doom controller (strategy and bid mode)
                self.doom_controller.update_from_settings()
                
                # Update supporting components
                self.economy.update_config(self.settings.get_economy_config())
                
                logger.info("✅ All configurations updated")
        except Exception as e:
            logger.error(f"❌ Error updating configurations: {e}")
    
    def switch_strategy(self, strategy_type: str, config: Optional[Dict] = None):
        """Dynamically switch to a different strategy."""
        try:
            new_strategy = self.doom_controller.load_strategy(strategy_type, config)
            self.doom_controller.current_strategy = new_strategy
            logger.info(f"🔄 Switched to strategy: {strategy_type}")
        except Exception as e:
            logger.error(f"❌ Failed to switch strategy: {e}")
    
    def switch_bid_mode(self, mode_type: str, config: Optional[Dict] = None):
        """Dynamically switch to a different bid mode."""
        try:
            new_mode = self.doom_controller.load_bid_mode(mode_type, config)
            self.doom_controller.current_bid_mode = new_mode
            logger.info(f"🔄 Switched to bid mode: {mode_type}")
        except Exception as e:
            logger.error(f"❌ Failed to switch bid mode: {e}")
    
    def get_system_info(self) -> Dict:
        """Get comprehensive system information."""
        return {
            'agent_info': self.settings.get_agent_info(),
            'doom_controller': self.doom_controller.get_current_info(),
            'available_strategies': self.doom_controller.get_available_strategies(),
            'available_bid_modes': self.doom_controller.get_available_bid_modes()
        }
    
    def get_max_bet_limit(self, current_round: int, bank_state: Dict) -> Optional[float]:
        """
        Retrieve the maximum bet limit percentage for the current round if enabled.

        Args:
            current_round: The current round number.
            bank_state: The current bank state.

        Returns:
            The maximum bet limit percentage as a float, or None if the feature is disabled.
        """
        if not self.settings.get('economy', 'use_max_bet_limit', default=True):
            logger.info("🔕 Max bet limit feature is disabled.")
            return None

        return self.economy.calculate_max_bet_limit(bank_state, current_round)

def connection_manager(game_client, bid_callback):
    """Manage connection with automatic reconnection."""
    while True:
        try:
            game_client.run(bid_callback)
            logger.info("🎮 Game completed successfully")
            break
        except (ConnectionClosedError, ConnectionClosedOK) as e:
            logger.warning(f"🎮 Connection lost: {e}. Retrying...")
            time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("🎮 Game interrupted by user")
            break
        except Exception as e:
            logger.error(f"🎮 Unexpected error: {e}")
            time.sleep(0.5)

if __name__ == "__main__":
    # Load configuration from settings
    settings = get_settings_manager()
    
    # Get connection configuration
    connection_config = settings.get_connection_config()
    agent_info = settings.get_agent_info()
    
    host = connection_config.get('host', 'localhost')
    port = connection_config.get('port', 8000)
    agent_name = agent_info.get('name', 'DoomGuy666')
    player_id = agent_info.get('player_id', 'doom_agent_666')
    
    # Log startup info
    logger.info(f"🚀 Starting {agent_name} v{agent_info.get('version', '2.0')}...")
    logger.info(f"🌐 Connecting to {host}:{port}")
    
    # Create game client
    game = AuctionGameClient(host=host, agent_name=agent_name, 
                           player_id=player_id, port=port)

    # Start agent with settings-based configuration
    logger.info("🎮 Starting DOOM AGENT with configurable strategies...")
    
    # Ensure doom_agent_instance is defined globally and initialized
    global doom_agent_instance
    doom_agent_instance = globals().get('doom_agent_instance', DoomAgent())

    # Expose `doom_bid_controller` as a module-level symbol for tests and
    # external callers that import it from `main.py` (backwards compatible
    # behavior: returns just bids dict for direct callers).
    doom_controller = doom_agent_instance.doom_controller
    globals()['doom_bid_controller'] = doom_controller.doom_bid_controller

    # Create a wrapper to adapt the controller's return value to the server
    # expected format: { "bids": {...}, "pool": n }
    def doom_bid_callback(a_id, current_round, states, auctions, prev_auctions, pool, prev_pool_buys, bank_state):
        bids = doom_controller.doom_bid_controller(a_id, current_round, states, auctions, prev_auctions, pool, prev_pool_buys, bank_state)
        pool_contribution = getattr(doom_controller, '_last_pool_contribution', 0)
        # Respect settings: whether pool buys are enabled for agent
        pool_buy_enabled = doom_controller.settings.get('economy', 'pool_buy_enabled', True)
        if not pool_buy_enabled:
            pool_contribution = 0
        # Ensure pool contribution uses points and can't exceed available points
        available_points = states.get(a_id, {}).get('points', 0)
        min_points_reserve = doom_controller.settings.get('economy', 'min_points_reserve', 1)
        total_bid = sum(bids.values()) if bids else 0
        # If not enough points left after pool buy (pool buy is paid in points), adjust pool contribution down
        if available_points - pool_contribution < min_points_reserve:
            pool_contribution = max(0, available_points - min_points_reserve)

        return {"bids": bids, "pool": pool_contribution}

    connection_manager(game, doom_bid_callback)