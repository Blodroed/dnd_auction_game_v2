"""
Settings Manager for DoomGuy666 Agent

Centralized settings management system that loads configuration from settings.json
and provides it to all bot components. Supports real-time updates and validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SettingsManager:
    """
    Centralized settings manager for the DoomGuy666 agent.
    
    Handles loading, validation, and distribution of configuration settings
    to all bot components. Supports hot-reloading and validation.
    """
    
    def __init__(self, settings_file: str = "data/settings.json"):
        self.settings_file = Path(settings_file)
        self.settings = {}
        self.default_settings = self._get_default_settings()
        self.last_modified = None
        
        # Load initial settings
        self.load_settings()
        
        logger.info("🛠️ Settings Manager initialized")
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file with fallback to defaults."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                self.last_modified = self.settings_file.stat().st_mtime
                logger.info(f"✅ Settings loaded from {self.settings_file}")
            else:
                logger.warning(f"⚠️ Settings file not found, using defaults")
                self.settings = self.default_settings.copy()
                self.save_settings()
            
            # Validate and merge with defaults
            self.settings = self._merge_with_defaults(self.settings)
            return self.settings
            
        except Exception as e:
            logger.error(f"❌ Error loading settings: {e}")
            logger.info("🔄 Using default settings")
            self.settings = self.default_settings.copy()
            return self.settings
    
    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            # Update metadata
            self.settings.setdefault('meta', {})
            self.settings['meta']['last_updated'] = datetime.now().isoformat()
            
            # Ensure directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            
            logger.info(f"✅ Settings saved to {self.settings_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving settings: {e}")
            return False
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get setting value by section and optional key.
        
        Args:
            section: Settings section (e.g., 'strategy', 'economy')
            key: Optional specific key within section
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        section_data = self.settings.get(section, {})
        
        if key is None:
            return section_data if section_data else default
        
        return section_data.get(key, default)
    
    def update(self, section: str, key: str, value: Any) -> bool:
        """
        Update a specific setting value.
        
        Args:
            section: Settings section
            key: Setting key
            value: New value
            
        Returns:
            True if updated successfully
        """
        try:
            if section not in self.settings:
                self.settings[section] = {}
            
            old_value = self.settings[section].get(key)
            self.settings[section][key] = value
            
            logger.info(f"🔧 Updated {section}.{key}: {old_value} → {value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating setting {section}.{key}: {e}")
            return False
    
    def update_section(self, section: str, new_values: Dict[str, Any]) -> bool:
        """
        Update entire section with new values.
        
        Args:
            section: Settings section to update
            new_values: Dictionary of new values
            
        Returns:
            True if updated successfully
        """
        try:
            if section not in self.settings:
                self.settings[section] = {}
            
            self.settings[section].update(new_values)
            logger.info(f"🔧 Updated section '{section}' with {len(new_values)} values")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating section {section}: {e}")
            return False
    
    def check_for_updates(self) -> bool:
        """Check if settings file has been modified and reload if needed."""
        try:
            if not self.settings_file.exists():
                return False
                
            current_modified = self.settings_file.stat().st_mtime
            if current_modified != self.last_modified:
                logger.info("🔄 Settings file changed, reloading...")
                self.load_settings()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking for updates: {e}")
            return False
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """Get complete strategy configuration."""
        return self.get('strategy', default={})
    
    def get_bid_mode_config(self) -> Dict[str, Any]:
        """Get complete bid mode configuration."""
        return self.get('bid_modes', default={})
    
    def get_economy_config(self) -> Dict[str, Any]:
        """Get complete economy configuration."""
        return self.get('economy', default={})
    
    def get_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration."""
        return self.get('connection', default={})
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return self.get('agent_info', default={})
    
    def _merge_with_defaults(self, loaded_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded settings with defaults to ensure all keys exist."""
        merged = self.default_settings.copy()
        
        for section, values in loaded_settings.items():
            if section in merged and isinstance(merged[section], dict) and isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values
        
        return merged
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings structure."""
        return {
            "agent_info": {
                "name": "DoomGuy666",
                "player_id": "doom_agent_666",
                "version": "2.0.0"
            },
            "connection": {
                "host": "localhost",
                "port": 8000,
                "reconnect_attempts": 5,
                "reconnect_delay": 0.5
            },
            "strategy": {
                "type": "vulture_mode",
                "aggression_multiplier": 1.5,
                "max_bid_ratio": 0.8,
                "min_auctions_target": 3,
                "deadspace_threshold": 2.0,
                "high_value_threshold": 15.0
            },
            "bid_modes": {
                "current_mode": "AGGRESSIVE_SPREAD",
                "focus_ratio": 0.7,
                "min_bid_amount": 1,
                "max_single_bid_ratio": 0.4,
                "spread_factor": 0.8
            },
            "economy": {
                "spending_ratio": 0.8,
                "accumulation_penalty": 1.2,
                "interest_threshold": 1.05,
                "pool_contribution_rate": 0.05,
                "min_points_reserve": 1,
                "pool_buy_enabled": True,
                "pool_contribution_use_highest": False
            },
            "logging": {
                "level": "INFO",
                "enable_performance_logs": True,
                "enable_debug_mode": False
            }
        }
    
        # Add pool contribution config defaults to economy
        merged = merged
    def validate_settings(self) -> bool:
        """Validate current settings for correctness."""
        try:
            # Validate ranges
            strategy = self.get('strategy', default={})
            if strategy.get('aggression_multiplier', 1.5) < 0.1:
                logger.warning("⚠️ Aggression multiplier too low, using minimum 0.1")
                self.update('strategy', 'aggression_multiplier', 0.1)
            
            economy = self.get('economy', default={})
            spending_ratio = economy.get('spending_ratio', 0.8)
            if not 0.1 <= spending_ratio <= 1.0:
                logger.warning(f"⚠️ Invalid spending ratio {spending_ratio}, using 0.8")
                self.update('economy', 'spending_ratio', 0.8)
            
            logger.info("✅ Settings validation completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Settings validation failed: {e}")
            return False

# Global settings manager instance
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

def get_setting(section: str, key: Optional[str] = None, default: Any = None) -> Any:
    """Convenience function to get a setting value."""
    return get_settings_manager().get(section, key, default)

def update_setting(section: str, key: str, value: Any) -> bool:
    """Convenience function to update a setting value."""
    return get_settings_manager().update(section, key, value)